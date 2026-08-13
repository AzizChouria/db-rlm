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
| + `reasoning_effort=high` (old prompt, hints on) | 69.2–70.2% (band, ±~1.5 run variance) | reasoning depth: **+5–6** more |

Net: **+15 points from architecture and reasoning depth combined, zero
training, zero bigger model.**

### 1a. This week's updates (2026-08-12/13): dedup fix, hints removed, reasoning-effort re-ablation

Three changes landed this week, each independently validated before merging:

1. **Dedup-convention prompt fix** — the prompt was telling the model to add
   `DISTINCT`/dedupe joined rows, which fights how BIRD gold actually computes
   `COUNT`/`SUM`/`AVG` (raw join cardinality unless the hint says otherwise).
   Traced to 13/79 classified failures (§3). Validated on a 197-question
   failcore+canary set first (28/137 recovered, ~0 real regressions), then
   full 500: **net +7 attributable specifically to the fix**, mostly masked
   by ordinary run-to-run noise in the raw top-line number.
2. **Per-database hints (`ours/db_hints.py`) removed by default** — ablation
   on the 112 questions across the 3 hinted DBs showed an exact net-zero
   effect (58/112 both with and without). Helped 2 DBs, hurt the third,
   cancelled out. Also non-generalizing (tuned by looking at this exact
   benchmark's weakest DBs). Old dict/logic kept, opt-in via `ENABLE_DB_HINTS=1`.
3. **Per-call timeout raised 60s → 120s → 240s** — found the hard way: 12-13%
   of calls in early batches were hitting a 60s wall on `reasoning_effort=high`
   with a large accumulated conversation. At 120s, still 17/500 (3.4%) timed
   out on the full run. Raised to 240s and reran just those 17: 0 timeouts,
   6/17 flipped to correct (11 remained genuine reasoning failures — lower
   hit rate than the rest of the set, so timeouts weren't randomly-distributed
   easy questions). Merged into the main result.

**Full 500, current pipeline (dedup fix + hints off + 240s timeout), fair comparison — fully resolved, no infra noise on either side:**

| Configuration | Official EX | Timeouts | Avg reasoning tokens | Avg latency |
|---|---|---|---|---|
| `reasoning_effort=high` | **351/500 = 70.20%** | 0 | 3,847 | 67.1s |
| `reasoning_effort=low` | 340/500 = 68.00% | 0 | 322 (12x fewer) | 13.4s (5x faster) |

**Read carefully — small samples were misleading here.** On a 50-question and
a 79-question sample, low effort looked tied or even ahead of high effort.
At full 500 scale, fully resolved (no timeouts on either side now), high
effort is ahead by **~2.2 points** (70.20% vs 68.00%) — smaller than the
~3.4-point gap an earlier timeout-exclusion estimate suggested, since the
17 retested questions only recovered at a below-average 6/17 (35%) hit rate,
not the ~71% the rest of the set achieves. This is a real accuracy-vs-cost
tradeoff, not a free lunch: 12x the reasoning tokens and 5x the latency buys
~2.2 points. Frame this to Harshal as a tradeoff to decide on, matching the
project's own stated optimization target ("highest accuracy per cost"), not
a settled answer.

Trace-level mechanism (from manually reading ~20 traces, tagged by stage —
UNDERSTAND/EXPLORE/DRAFT/TEST/REFINE/FINALIZE): 312/500 questions are
correct under *both* configs — the "common path" is genuinely common.
Effort matters mainly on: (a) questions needing a non-obvious workaround
found only through sustained exploration (e.g. `bird_1501` — high found a
join through an unrelated table, low gave up), and (b) cases where *more*
reasoning reintroduces the dedup-convention bug the fix (#1 above) was
supposed to prevent (e.g. `bird_1525` — high reasons its way back into
adding `DISTINCT` against the explicit prompt rule; low follows the rule
literally and gets it right). Low effort also shows a distinct new failure
mode not seen at high effort: momentarily doubting it has database-query
tools at all and finalizing an unverified guess (~29% of correct low-effort
traces show this doubt-and-proceed-anyway pattern even when they still land
on the right answer — a fragile-correct process, not a clean one).

**New failure set, current pipeline**: **149 wrong out of 500, 0 timeouts**
(138 original non-timeout failures + 11 of the 17 timeout cases that turned
out to be genuine reasoning failures once actually run at 240s — the other
6 flipped correct). This supersedes the old 158-question (79+79) classified
set, which was traced under the *old* prompt (pre-dedup-fix, hints on). The
old classification sheet is still valid as a record of what those specific
failure mechanisms look like, but the current failure *population* has
shifted — worth flagging before re-running the full classification exercise
on the new set. Given 149 is close to double the original 79-per-person
scope and the 21 Aug deadline, consider classifying a representative sample
(~40-50) with the same live-SQL-verification rigor rather than all 149
exhaustively — disclosed honestly as a sample, not a scope-reduction hidden
in the numbers.

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
