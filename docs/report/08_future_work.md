# 8. Future Work

The items below are ordered by how concretely they are already scoped,
not by importance. Several are partial fixes already implemented and
merged during this project, with a specific residual gap identified and
left for the next iteration rather than treated as closed.

## 8.1 The Dedup-Convention Rule's Remaining Gap Is Compliance, Not Coverage

The dedup-convention prompt rule (§6.3) — do not deduplicate join results
for `COUNT`/`SUM`/`AVG` unless the hint says otherwise — was the single
largest fixable pattern identified in an earlier classification pass (13
of 79 failures at that time). An earlier draft of this section described
extending the rule's wording to name semi-join shapes (`EXISTS`,
correlated `IN`) explicitly, not only the literal `DISTINCT` keyword; this
has already been done — the rule as currently written covers both forms.
That correction is reflected here rather than left as a stale open item.

A live re-check of the 6 questions previously flagged as dedup-convention
failures found that only one, `bird_1254`, is still a genuine violation
under the current pipeline: the model writes `COUNT(DISTINCT P.ID)` where
gold has plain `COUNT(T1.ID)`, despite the rule explicitly prohibiting
this. Two of the six (`bird_1490`, `bird_1227`) now pass; the remaining
three (`bird_145`, `bird_169`, `bird_24`) fail for unrelated reasons —
wrong join or wrong column — and the dedup label on them was stale.

The remaining gap is therefore not a wording gap: the rule already says
the right thing and the model violates it anyway on at least one case.
Rewriting the rule again is unlikely to help, consistent with this
project's broader finding that additional prompt text does not reliably
improve compliance (§7.2). A more promising next step, not yet tried, is
a post-hoc check: after the model finalizes, run a cheap, deterministic
scan of the SQL for `DISTINCT` or an `EXISTS`/correlated-`IN` semi-join
shape, and if the hint does not justify one, force a single corrective
turn rather than relying on the model to remember its own instruction
under load.

## 8.2 Reconcile the Hint Symbol-Legend Fix's Residual Failures

A second prompt rule, addressing hint symbol-legend mistranslation
(§6.3, §6.4), was added and confirmed to correctly resolve the
symbol-translation step on direct re-test — but residual, unrelated gaps
remained on two of the three questions it targeted (`bird_1265`,
`bird_1267`, `bird_1275`). The specific remaining defect on those two
cases has not yet been classified; doing so is a small, bounded next step
that should happen before this pattern is reported as resolved rather than
partially resolved.

## 8.3 Recursion: Typed Sub-Call Contracts

This project's recursion ablation (§5.4, §7.2) found no measured benefit
from recursive delegation over a plain, non-recursive ReAct loop at equal
cost, converging with a teammate's independent test. The working, as-yet
untested explanation is that this project's recursive sub-calls pass
free-text context between parent and child agents, where systems reporting
a benefit from recursion in the broader literature — specifically
Trampoline AI's `predict-rlm` runtime, which uses typed DSPy signatures
(defined inputs, outputs, and tools) rather than free-text handoff for
sub-LM calls (Trampoline-AI/predict-rlm, GitHub, 2026,
https://github.com/Trampoline-AI/predict-rlm) — appear to rely on
typed, narrow sub-call contracts instead — a child agent is given a
specific, structured question to answer (e.g. "return the id for value X
in table Y") rather than an open-ended slice of the parent's own context.
Building a typed sub-call interface and re-running the same recursion
ablation against it is the direct next step to either confirm or rule out
this explanation. Additionally, §5.4's negative result was measured on an
earlier, pre-dedup-fix pipeline; the ablation should be re-run once under
the current best configuration before any claim about recursion is
finalized against it.

## 8.4 Offline Precompute

A specification for an offline precompute stage — mining per-database
metadata and recurring query patterns ahead of inference, rather than
relying entirely on live exploration during the ReAct loop — was drafted
earlier in this project but not built. This is a natural complement to
the KNOWLEDGE-class failures documented in §6.2 (10 of 64, 16%): cases
where the model lacked a fact about the database it could not have
inferred from the schema or the question's own evidence field, and where
a precomputed index of actual column values or common join paths could
supply that fact without per-question exploration cost.

## 8.5 Reconcile the Combined Failure Classification

Aziz's 64-question classification (§6) and a teammate's independent
163-question classification, using a distinct nine-category taxonomy,
were cross-validated (§6.6) and found to agree on several specific
defects by question id. One real methodological difference remains open:
the teammate's convention records a case where gold answers correctly
despite a defective hint as a model error with a defective-hint flag,
rather than as a gold defect outright — stricter than this document's
convention (§6.1), and one that would shift some fraction of the
GOLD_NOISE share reported in §6.2 toward REASONING once harmonized. This
should be resolved by direct discussion before the two classification
sets are merged into one combined table, rather than by either side
silently adopting the other's convention.

## 8.6 Investigate the Reasoning-Effort Curve Discrepancy on Corrected Gold

This project's own reasoning-effort ablation (§5.2) found a comparatively
small, noisy high-vs-low gap (2.2 points) on the original gold set. A
teammate's independent analysis on the Arcwise-corrected gold set reports
a substantially larger and cleaner reasoning-effort curve. Since §5.3
shows that gold-set correctness alone accounts for a 15.3-point swing
under this project's own harness, it is not yet established whether the
teammate's steeper curve is a property of the corrected gold set
specifically, of a different harness configuration, or both. Running this
project's own high-vs-low comparison against the corrected gold set
(building on the same-harness run already completed in §5.3) would
isolate this directly and is a small, well-defined next step.

## 8.7 Thought-Anchors-Style Formal Step Scoring

The manual stage-tagging methodology used in §6.5 (UNDERSTAND / EXPLORE /
DRAFT / TEST / REFINE / FINALIZE, applied by hand to a 50-question sample,
of which 47 were tagged)
approximates, informally, the kind of step-importance scoring the Thought
Anchors line of work (Bogdan, Macar, Nanda, and Conmy, "Thought Anchors:
Which LLM Reasoning Steps Matter?," arXiv:2506.19143) formalizes mechanistically. Replacing the manual
tagging with a formal step-importance measure would let the DRAFT-stage
clustering finding in §6.5 (5 of 7 genuine model mistakes occur at DRAFT,
not UNDERSTAND — corrected from an earlier draft's stale "8 of 10," which
predated this document's numerical audit) be verified at a scale beyond
what manual tagging can
practically cover, and would generalize beyond the specific 47-trace
sample it is currently based on.

## 8.8 Scale and Scope Extensions

- **Full BIRD dev set.** All results in this document are reported on the
  500-question mini-dev subset (498 unique, §4.1). Running the
  best-validated configuration against the full BIRD dev set (1,534
  questions) would test whether the ablation results in §5 generalize
  beyond the smaller subset, and is the natural scale-up once the mini-dev
  configuration is considered final.
- **A larger generator model — done as a single-run side comparison
  (§5.5).** `gpt-5.4` (normal) was run against the same harness and
  configuration used throughout this document, at both low and high
  reasoning effort, on the original gold set. The gain over
  `gpt-5.4-mini` was real but modest (+3.6 points at low effort, +0.8 at
  high), well below the harness- and gold-correction gains reported in
  §5.1 and §5.3 — consistent with this project's central claim rather
  than a threat to it. This was a single run per condition, not repeated,
  and not yet combined with the corrected-gold experiment; a repeated run
  and a `gpt-5.4` × corrected-gold comparison remain open follow-ups if
  time allows.
- **Per-layer reasoning-step tabulation.** A mean/median count of
  reasoning steps taken, broken out by question-difficulty layer and by
  correct-vs-incorrect outcome, was requested as a specific deliverable
  in project review; the underlying data (`llm_calls`, transcript turn
  counts) already exists in every results file used in this document and
  has not yet been tabulated separately.
