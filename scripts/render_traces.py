"""Render ReAct transcripts into a readable HTML report for trace analysis.

Joins transcripts.jsonl with the result file, renders each question as a
collapsible story (question → hint → turns → final vs gold), failures first.

Usage:
  python scripts/render_traces.py \
    --transcripts transcripts/rhigh_500/transcripts.jsonl \
    --results results/bird_traced_rhigh_500.json \
    --out transcripts/rhigh_500/traces_report.html [--failures-only]
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def esc(s) -> str:
    return html.escape(str(s))


def render_question(rec: dict, res: dict) -> str:
    ok = res.get("correct")
    badge = ("<span style='color:#2e7d32'>✔ correct</span>" if ok
             else "<span style='color:#c62828'>✘ WRONG</span>")
    parts = [f"<details><summary><b>{esc(rec['id'])}</b> "
             f"[{esc(res.get('db_id','?'))} / {esc(res.get('difficulty','?'))}] {badge} "
             f"— {esc(res.get('question','')[:110])}</summary>"]
    parts.append("<div style='margin:0.5em 1em; padding:0.5em; border-left:3px solid #999'>")
    traces = rec.get("reasoning_traces", [])
    if traces:
        parts.append(f"<details open><summary><b>🧠 reasoning trace ({len(traces)} steps)</b></summary>")
        for t in traces:
            parts.append(f"<div style='margin:0.3em 0 0.8em 0.5em;padding:0.4em;background:#fffbe6;"
                         f"border-left:3px solid #e0c000'><i>iteration {t.get('iteration')}</i>"
                         f"<pre style='white-space:pre-wrap;font-family:inherit'>{esc(t.get('text',''))}</pre></div>")
        parts.append("</details>")
    msgs = rec.get("messages", [])
    for i, m in enumerate(msgs):
        role = m.get("role")
        content = str(m.get("content", ""))
        if role == "system":
            parts.append(f"<details><summary><i>system prompt ({len(content)} chars)</i></summary>"
                         f"<pre style='white-space:pre-wrap'>{esc(content[:4000])}</pre></details>")
        elif role == "user" and i <= 1:
            parts.append(f"<details open><summary><b>task prompt</b> ({len(content)} chars)</summary>"
                         f"<pre style='white-space:pre-wrap'>{esc(content[:6000])}</pre></details>")
        elif role == "assistant":
            parts.append(f"<p><b>🤖 model turn:</b></p>"
                         f"<pre style='background:#f0f4ff;white-space:pre-wrap'>{esc(content[:5000])}</pre>")
        else:
            parts.append(f"<p><b>⚙️ observation:</b></p>"
                         f"<pre style='background:#f7f7f7;white-space:pre-wrap'>{esc(content[:3000])}</pre>")
    parts.append(f"<p><b>FINAL SQL:</b> <code>{esc(res.get('predicted_sql',''))}</code></p>")
    parts.append(f"<p><b>PRED result:</b> {esc(str(res.get('predicted_answer'))[:300])}</p>")
    parts.append(f"<p><b>GOLD SQL:</b> <code>{esc(res.get('gold_sql',''))}</code></p>")
    parts.append(f"<p><b>GOLD result:</b> {esc(str(res.get('gold_answer'))[:300])}</p>")
    parts.append(f"<p><i>tokens: {res.get('prompt_tokens')}p / {res.get('completion_tokens')}c "
                 f"/ {res.get('reasoning_tokens')}r · {res.get('llm_calls')} calls</i></p>")
    parts.append("</div></details><hr>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--failures-only", action="store_true")
    args = ap.parse_args()

    results = {x["id"]: x for x in json.loads(Path(args.results).read_text())}
    recs = [json.loads(l) for l in open(args.transcripts)]
    # de-dup by id, keep last occurrence (reruns)
    by_id = {r["id"]: r for r in recs}
    recs = list(by_id.values())

    def key(r):
        res = results.get(r["id"], {})
        return (res.get("correct", True), r["id"])  # failures first
    recs.sort(key=key)

    n_fail = sum(1 for r in recs if not results.get(r["id"], {}).get("correct", True))
    body = [f"<h1>Trace report — {len(recs)} questions ({n_fail} failures, listed first)</h1>",
            "<p>For each failure: find the <b>wrong turn</b> and classify "
            "<b>KNOWLEDGE</b> (model lacked a fact) vs <b>REASONING</b> (had it, misused it).</p>"]
    for r in recs:
        res = results.get(r["id"])
        if not res:
            continue
        if args.failures_only and res.get("correct"):
            continue
        body.append(render_question(r, res))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("<meta charset='utf-8'><body style='font-family:sans-serif;max-width:1100px;margin:auto'>"
                   + "\n".join(body) + "</body>")
    print(f"wrote {out} ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
