# Aziz's Track — One-Page Status (for the 2026-08-25 meeting)

## What's done

Six report sections, written and verified against source data (not carried
forward from memory/notes):

- **Introduction** — motivation, research question (harness vs. model
  scale, model fixed at `gpt-5.4-mini` throughout), three contributions
- **Methodology** — dataset (BIRD mini-dev, 498 unique), official
  execution-accuracy protocol, DB-RLM architecture, ablation protocol,
  data-integrity fixes (leakage, timeout, evidence-field bug)
- **Results** — full harness ablation, reasoning-effort cost/accuracy
  tradeoff, the new corrected-gold comparison, recursion negative result
- **Failure Analysis** — 64 questions, live-SQL-verified, class breakdown,
  13 named recurring patterns, 4 worked examples with real SQL
- **Discussion** — what worked and why, two negative results explained,
  relation to external evidence (SQRL), the effective-ceiling argument
- **Future Work** — 8 concretely scoped next steps

## Headline numbers (this track only, all live-verified this week)

| Configuration | Official EX |
|---|---|
| Baseline 1 — direct schema→SQL | 55.20% |
| Baseline 2 — + keyword table filter | 51.60% (negative result) |
| DB-RLM harness (ReAct + live tools) | 64.20% |
| + `reasoning_effort=high` | 70.20% |
| Same pipeline, Arcwise-corrected gold | **85.54%** (+15.3pts, isolates gold-set correctness alone) |

## What's NOT yet resolved

- How this track combines with Hanyan's separate, larger experimental
  line (her five-layer chain, mechanism-attribution framing, 163-item
  ledger) — one merged document vs. two tracks under one cover is an open
  question, sent to her today
- §3 Related Work — not started, needs a shared reading-list split
- The classification-convention gap between my taxonomy and Hanyan's
  (defective-hint-but-answerable cases) — flagged, not reconciled
- gpt-5.4 (normal) comparison — explicitly out of scope without
  Harshal's sign-off; not attempted

## This week's audit note

Every section above was independently re-verified this week: several
numbers from earlier drafts were corrected against source data (a
pattern-count table, a trace-tagging sample size, a mischaracterized
worked example, an unsourced noise-floor statistic replaced by a fresh
20-question measurement). Flagging this proactively rather than letting
it surface as a discrepancy later.
