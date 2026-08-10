# Report Skeleton

Standard research format per Harshal (30+ pages target, deadline ~21 Aug).
Each section below has: purpose, what we already have to draw from, and
what's still missing. Fill in prose over the content already in
`docs/findings.md`, `docs/project_journal.md`, `docs/aziz_summary_for_report.md` —
don't re-derive results, write them up.

---

## 1. Abstract (~0.5 page)
One paragraph: problem (small models fail at Text-to-SQL without the right
harness) → approach (DB-RLM: ReAct loop + live DB tools, gpt-5.4-mini fixed) →
headline result (55.2% → 69-70% official EX on BIRD mini-dev, +15 pts,
zero training/bigger model) → failure analysis contribution (79+79 questions
root-caused, ~48% of failures are benchmark defects) → negative result
(recursion doesn't help on this benchmark, confirmed two ways).
**Status: write last, once everything else is drafted.**

## 2. Introduction (~2 pages)
- Motivation: Text-to-SQL with LLMs; why small models fail (context rot,
  hallucinated joins/columns/values — cite the SQRL/LinkedIn examples as
  a second, independent source naming the same failure modes)
- Research question (supervisor's framing): how far can a *harness* around
  a fixed small model go, without a bigger or domain-specific model?
- Contributions: (1) harness ablation on BIRD, (2) verified failure taxonomy
  with fix candidates, (3) recursion ablation (negative result)
**Status: not started. Draft from this doc + `aziz_summary_for_report.md` §1.**

## 3. Background / Related Work (~4-6 pages)
Papers to cover (2/week/person quota — track who's covered what):
- Original RLM paper (the base architecture we extend)
- CHESS (value retrieval / schema linking, cited for our failed value-lookup
  attempt and for context on what "good" retrieval looks like)
- DAIL-SQL (few-shot example selection)
- CHASE-SQL (multi-candidate + selection — relevant to why our own
  candidate-selection experiment failed: selection needs a stronger judge
  or diverse candidates, ours had neither)
- Self-Consistency (Wang et al.) — relevant to our SC experiments
- SQRL / "ask the database first" (Feyn blog + independent A100
  verification) — closest published parallel to our ReAct loop; note the
  overlap in named failure modes (wrong joins, misread columns, filtering
  for nonexistent values) as external validation
- Thought Anchors (mechanistic interpretability, step-importance scoring) —
  cite as the formal framework our manual "wrong-turn" classification
  approximates; note as future work, not implemented
- predict-rlm (Trampoline AI) — cite for the typed-sub-call insight
  (candidate explanation for why our recursion ablation is negative)
**Status: not started.**

## 4. Methodology (~4-5 pages)
- Dataset: BIRD mini-dev, 500 questions (498 unique — 2 exact duplicates,
  disclose this), 11 databases
- Scoring: official BIRD execution-accuracy protocol (set comparison);
  note the mid-project correction from a stricter homemade metric and why
  it matters for comparability with published numbers
- System architecture: DB-RLM — ReAct loop, sandboxed live SQLite
  connection, `db.execute`/`db.sample_values` tools, evidence/hint
  injection. Diagram needed (can adapt from the RLM-with-REPL diagram
  style Harshal referenced).
- Generator model fixed throughout: gpt-5.4-mini (state and justify —
  supervisor's "harness must be bitter-lesson compatible" constraint)
- Ablation protocol: incremental, one module per trial, labeled
  "Baseline", "Baseline + X" (Harshal's explicit format requirement)
- **Rigor/integrity subsection** (this is a genuine strength, include it):
  the data-leakage incident — found, disclosed, fixed, all affected runs
  re-verified. Shows the methodology survives scrutiny. Don't bury this;
  a paragraph describing detection + fix is a credibility asset.
**Status: mostly ready to write — it's already documented in the journal,
needs prose + a system diagram.**

## 5. Experiments & Results (~5-6 pages)
Table (already have all numbers, `aziz_summary_for_report.md` §1):

| Config | Official EX | Δ |
|---|---|---|
| B1 — direct schema→SQL | 55.2% | — |
| B2 — + keyword table filter | 51.6% | −3.6 (negative result) |
| DB-RLM (ReAct + tools) | 64.2% | +9.0 |
| + reasoning_effort=high | 69.2–70.2% | +5–6 |

- Per-difficulty breakdown (simple/moderate/challenging)
- Cost note: reasoning-high is ~3-4x tokens, ~22s vs ~7s/question latency
  (R-VES unaffected — measures SQL runtime not model latency)
- **Recursion ablation** (own subsection): Reactive+Recursive config vs
  non-recursive at equal cost — negative result, converges with Hanyan's
  independent 50-question test. State plainly, this is real content not
  a gap.
**Status: table ready, need per-difficulty numbers pulled + prose.**

## 6. Failure Analysis (~5-6 pages) — our strongest original section
- Methodology: 158 failures traced with full transcripts, split 79/79,
  each independently classified into KNOWLEDGE / REASONING / GOLD_NOISE
  (+ INFRA_ERROR), then cross-verified by live SQL re-execution against
  the real databases (not just reading) — describe the verification
  protocol itself, it's a real methodological contribution
- Results table (`aziz_summary_for_report.md` §3): class breakdown,
  subcategory clusters, counts
- Headline pattern: dedup-convention (~1 in 6 failures) — explain the
  mechanism with a worked example (e.g. bird_1505 or bird_152's AVG case)
- Gold-noise exhibit: 2-3 concrete, airtight examples (AND/OR precedence
  bug, join-fanout bug in toxicology, gold-answers-different-question) —
  quantifies the benchmark's own error floor
- Best single case study: the "early committal" example (model discovers
  correct values via exploration, then ignores its own discovery in the
  final answer) — ties directly into the Thought Anchors framing from §3
- Merge with Hanyan's 79 once available; combined tally becomes final table
**Status: content fully exists (`findings.md`, classification sheet),
needs writing + 2-3 illustrated examples pulled from the sheet.**

## 7. Discussion (~2-3 pages)
- What worked and why (harness > model size; reasoning depth > prompt
  engineering)
- What didn't and why (recursion; most scaffolding tricks net ≈0 —
  the systematic-error-ceiling finding from earlier ablation rounds)
- Relation to SQRL: independent convergent evidence that "inspect before
  answering" is the right mechanism; our contribution is doing this
  without any training, on a fixed general-purpose model
- Effective ceiling discussion: ~48% of remaining failures are benchmark
  defects, not model errors — puts our accuracy number in context against
  the literature's ceiling
**Status: not started, but every claim already exists elsewhere in docs —
this section is synthesis, not new research.**

## 8. Future Work (~1 page)
- Fix the dedup-convention scaffold rule at scale (in progress as of
  writing — cite the failcore validation result once available)
- Typed sub-call contracts for recursion (predict-rlm-inspired), re-test
- Offline precompute (metadata + query-pattern mining, per-DB insights) —
  spec already written (`spec.md`), not yet built
- Thought-Anchors-style formal step-importance scoring, replacing manual
  wrong-turn classification
- Full BIRD dev (1,534 q) run with the best validated config
- Possible workshop paper extension (per Harshal, contingent on team interest)
**Status: mostly ready, pull from `tasks.md`.**

## 9. Conclusion (~0.5 page)
Restate contributions + headline number. Write last.

---

## Cross-cutting TODOs
- [ ] System architecture diagram (§4)
- [ ] Per-difficulty results table (§5)
- [ ] 2-3 worked failure examples with SQL shown (§6)
- [ ] Merge Hanyan's 79 classifications into §6's combined tally
- [ ] Literature summaries — track who's read what to avoid duplicate work
- [ ] Dedup-fix validation result (test running now, plug into §5/§8 once done)
