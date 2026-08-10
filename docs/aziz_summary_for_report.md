# Aziz's Track — Summary for Report Outline

*Condensed for merging with Hanyan's offline-knowledge/retrieval findings.
Full detail lives in `docs/findings.md`, `docs/project_journal.md`, and
`transcripts/rhigh_500/classification_sheet.csv`.*

## 1. Pipeline & results (methodology + results sections)

System: DB-RLM — a ReAct loop where the model explores a live, sandboxed
SQLite connection (`db.execute`, `db.sample_values`) before committing SQL.
Generator fixed at `gpt-5.4-mini` throughout (supervisor's constraint).
Evaluated on BIRD mini-dev (500 questions), official execution-accuracy
protocol (set comparison).

| Configuration | Official EX | What it isolates |
|---|---|---|
| Baseline 1 — direct schema→SQL, no tools | 55.2% | no-harness floor |
| Baseline 2 — + keyword table filter | 51.6% | naive schema pruning *hurts* |
| DB-RLM harness (ReAct loop + live tools) | 64.2% | harness alone: **+9.0** |
| + `reasoning_effort=high` | 69.2–70.2% (band, ±~1.5 run variance) | reasoning depth: **+5–6** more |

Net: **+15 points from architecture and reasoning depth combined, zero
training, zero bigger model.**

## 2. Recursion ablation (converges with Hanyan's finding)

The RLM literature's headline claim is the *recursive/divide-and-conquer*
mechanism specifically (parent spawns child agents). We never found evidence
this component helps on BIRD:
- Reactive+Recursive config (investigator sub-agent) scored ~63.8%, at or
  below the same-cost non-recursive config (64.2%)
- **This matches Hanyan's own paired ablation independently** (recursion
  −4% vs baseline on her 50-question test)
- Working theory (from `predict-rlm` study, see `docs/predict_rlm_notes.md`):
  our recursive sub-calls pass free-text context; comparable systems that
  succeed with recursion use typed, narrow sub-call contracts. Untested
  fix, not yet built.
- **Conclusion so far: plain ReAct (ours) is doing the load-bearing work;
  recursion has not shown a measured benefit on this benchmark in any
  config tried.** Worth stating plainly in the report rather than assuming
  recursion helped — the data says otherwise.

## 3. Failure taxonomy — 79 questions classified, root-cause verified

Every classification cross-checked by live SQL re-execution against the
real databases (not just read) — 22 with deep mechanism analysis, 57 with
result cross-checks; 1 mislabeling caught and corrected during the process.

**By class:**

| Class | Count | Meaning |
|---|---|---|
| GOLD_NOISE | 38 (48%) | benchmark's own gold query is defective/inconsistent |
| REASONING | 24 (30%) | model had the information, misapplied it |
| KNOWLEDGE | 16 (20%) | model lacked a fact it couldn't have inferred |
| INFRA_ERROR | 1 (1%) | API failure, model never produced an answer |

**Recurring, fixable patterns (subcategory clusters):**

| Pattern | Count | Fix type |
|---|---|---|
| **Dedup-convention** (gold doesn't deduplicate join results; ~1 in 6 of all classified failures) | 13 | one scaffold rule |
| Column-count mismatch (gold adds/drops requested columns) | 4 | benchmark inconsistency — document, largely unfixable |
| Yes/no rule interactions (our own scaffold rule over/under-triggering) | 4 | scaffold rule refinement |
| Join-fanout bugs (unintended row multiplication in gold's SQL) | 4 | benchmark defect — document |
| AND/OR operator-precedence bugs in gold SQL | 3 | benchmark defect — document |
| Literal column-name matching (gold prefers a column whose name matches question wording, even when semantically odd) | 2 | candidate heuristic |

**Headline finding**: the single most valuable fix candidate is the
**dedup-convention rule** — "BIRD gold does not deduplicate join results
(COUNT/SUM/AVG all use raw join cardinality) unless the hint explicitly
says otherwise." This one rule is implicated in ~16% of all failures,
confirmed across multiple databases and multiple aggregate types (COUNT,
SUM, AVG) — not COUNT-specific.

**Best single supporting case for "early committal"** (supervisor's theory
that the model locks onto a wrong interpretation at the first reasoning
step and doesn't recover): one question where the model's own database
exploration *discovered* that the hint's literal values didn't exist,
found the correct values itself — then submitted the original wrong values
anyway in its final answer. Verified: using its own discovery would have
given the exact correct answer.

## 4. What this means for round 2 (next experiment)

Test the dedup-convention rule as a scaffold addition, validated on the
failure-core set before any full run (per team protocol). Highest
confidence, cheapest, most broadly applicable fix identified so far.

## 5. Merge points with Hanyan's track

- Her retrieval-schema (offline knowledge) results are the natural
  complement to my REASONING/scaffold findings — the KNOWLEDGE-class
  failures (16, 20%) are specifically the ones her offline mining should
  address (things the model couldn't have inferred without external info).
- Recursion result: converges with hers, cite jointly, one paragraph in
  the report rather than two separate half-findings.
- Report skeleton suggestion: Methodology (shared) → Results (accuracy
  table, shared) → Failure Analysis (my classification + her retrieval
  ablations) → Discussion (recursion doesn't help — joint finding;
  dedup-convention as the leading fix candidate) → Future Work
  (typed sub-calls for recursion, trace-folding, Thought-Anchors-style
  formal step scoring).
