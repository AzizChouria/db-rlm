# Project Journal — DB-RLM

Running log of decisions, experiments, bugs, and findings. One entry per
milestone/session. Source of truth for the final report and presentation.

Conventions: all accuracies are official BIRD execution accuracy (set
comparison) on mini-dev 500 (498 unique) unless stated; generator model is
`gpt-5.4-mini` unless stated.

---

## 2026-05-22 — Project kickoff (initial presentation)

**Objective:** Extend MIT's Recursive Language Model (RLM) paradigm from text to structured databases; validate on Text-to-SQL.
**Actions:** Reproduced original RLM framework locally (qwen2.5-coder:7b via ollama). Built 3 Spider baselines (direct, retrieval, non-recursive agent): 50/66/72% on a 50-question Spider sample (qwen2.5-coder:3b). Defined research questions: SQ1 RLMs on structured DBs, SQ2 recursive exploration, SQ3 scaling vs RAG.
**Takeaways:** Sandboxed code execution + DB tools is viable; move to BIRD for a harder, realistic benchmark.

## 2026-06-22 → 06-29 — DB-RLM v1-v4 iteration (BIRD mini-dev era begins)

**Objective:** Build and iterate the DB-RLM agent on BIRD mini-dev 500.
**Actions:** ReAct loop with live SQLite bridge (`db.execute`, `db.sample_values`), hint injection, prompt rules (ratio denominators, RANK(), date formats), static worked examples, per-DB hints. Versions v2→v4 plus "Reactive" variant (investigator child-agent spawned after 2 consecutive failures — the recursion mechanism).
**Results (strict scoring, later rescored):** B1 52.0, B2 52.0, v2 58.8, Reactive 60.8, v3 60.6, v4 61.2 (best).
**Errors/Roadblocks:** BLOCKED-on-empty-FINAL mechanic backfired (−4.2 on Reactive); table pre-selection −1.6.
**Takeaways:** Execution loop beats baselines by ~+9; hard blocking interventions hurt; 91% of failures are logic errors with plausible-looking rows; 68% of failures gave up within 2 LLM calls.

## 2026-07-02 → 07-03 — Scaling experiments; infrastructure hardening

**Objective:** Push accuracy with self-consistency, few-shot retrieval, schema enrichment; make runs reliable.
**Actions & code:** In-domain few-shot retriever; SC (5×temp 0.5 voting); schema sample-values in `format_schema()`; `asyncio.wait_for` 60s timeout on LLM calls (`src/rlm/core.py`); Azure baselines B1/B2 rerun.
**Errors/Roadblocks:** GPT-5 family rejects `temperature=0` in one-shot scripts (use 1); runs froze for hours — diagnosed later (see 07-04); ThreadPoolExecutor "timeout" didn't actually cancel (context manager blocks on shutdown) — replaced with asyncio-level timeout.
**Results (later found contaminated — retracted):** indomain 67.8 strict, SC 70.4 official.
**Takeaways:** Reliability engineering matters as much as modeling; several "gains" of this period were later invalidated.

## 2026-07-03 — Official scoring protocol adopted

**Objective:** Align our evaluation with the official BIRD protocol.
**Actions & code:** Discovered official `evaluation.py` uses `set(pred)==set(gold)` (order/duplicates ignored) while our evaluator compared sorted lists (stricter). Rewrote `shared/evaluator.py:is_correct` to official protocol (strict kept as `is_correct_strict`); built `scripts/rescore_official.py`; rescored all runs (+1.5-3 points each).
**Takeaways:** Protocol mismatch had us under-reporting and mis-prioritizing (chasing DISTINCT/duplicate "failures" the benchmark ignores).

## 2026-07-04 (a.m.) — Runaway-query root cause; large-model probe

**Objective:** Kill the mysterious multi-hour run stalls; probe model scaling.
**Actions & code:** Stall diagnosed: model-written cartesian JOINs pinned sqlite at 100% CPU — immune to asyncio timeouts. Fix: sqlite progress-handler abort after 30s in `ours/db_environment.py:_connect` (`QUERY_TIMEOUT_S`). Verified: runaway triple-join aborts at exactly 30s; normal queries unaffected. Endpoint probe found full `gpt-5.4` deployment; tested on the 117 never-solved questions: fixed 16/117, canary 59/60; full-500 run reached 74.4 (later retracted — leak).
**Takeaways:** CPU-bound work needs in-engine timeouts, not event-loop timeouts. Capability-bound errors exist that no scaffolding fixes.

## 2026-07-04 (p.m.) — ⚠️ DATA LEAKAGE DISCOVERED AND FIXED

**Objective:** (Supervisor directive: analyze the model's mistakes) — audit the few-shot machinery.
**Actions & code:** Self-retrieval audit: the in-domain retriever's pool = 306 dev questions with gold SQL; similarity retrieval returned the query question ITSELF for 73/100 sampled questions — the model saw its own gold answer. All runs using this retriever invalidated (incl. 70.4 SC and 74.4 gpt-5.4). Fix in `ours/bird_few_shot_retriever.py:retrieve`: exclude exact text matches and >0.98-similarity near-duplicates; re-audit 0/100. Clean rerun launched. Supervisor informed and numbers retracted.
**Errors/Roadblocks:** Emotional low point; user had already reported inflated numbers — handled with immediate correction message.
**Takeaways:** Retrieval pools must never overlap the eval set. Catching your own leakage pre-publication is the difference between a footnote and a disaster. Clean mini truth at this point: ~61.6 (heavy config).

## 2026-07-05 — Clean rebuild; ensemble mechanics mapped

**Objective:** Re-test all interventions against honest baselines.
**Actions:** v4 rescored officially = 64.2 (clean best). Distill pool from gpt-5.4's verified-correct traces: 62.4 (+0.8). Lean-prompt reconstruction: 61.8. Heterogeneous 4-run majority vote (execute → compare result sets): 65.6; 6 runs: 66.4; oracle 76-77.8.
**Errors/Roadblocks:** Dataset tail is hard: pace at 340/500 runs 3-5 points above final — early-pace extrapolation banned. Canary tests only valid for small deltas on a fixed config (cross-config churn ~13%).
**Takeaways:** Config tweaks live within ±1.5 noise; ensembles of diverse configs harvest real points; user deprioritized ensembles on cost grounds (correctly — accuracy-per-cost is the project metric).

## 2026-07-06 — Post-mortem; API-retry recovery; ⭐ reasoning-effort breakthrough

**Objective:** First-principles review; find silent failures; break the ~64 ceiling.
**Actions & code:** (1) Found 22 questions in the clean run auto-scored wrong due to unhandled `APIError`/`APIConnectionError` — added 3-attempt retry in `run_one`, re-ran the dead questions: 61.6 → **64.0** (+2.4). (2) Verified `reasoning_effort` is honored by mini (reasoning-token probe). Cleancore test: fixed 25/137 never-solved (best of any intervention incl. bigger model). Full 500: **70.2 official** — simple 78.4 / moderate 69.6 / challenging 59.8, 2.6 calls/q, ~22s vs 7s latency.
**Errors/Roadblocks:** Model-attribution confusion (old runs don't record model; briefly mis-concluded v4 was Llama-70B — user corrected: all mini). Lesson: result files must record model+config.
**Takeaways:** Reasoning depth (+5-6) beat every scaffolding intervention combined (~0). Infra errors silently eat points — retry everything. Trace of failures is systematic → judges/self-verify saturate.

## 2026-07-07 → 07-08 — Failure autopsy; variance measured; verified ensemble best

**Objective:** Autopsy the 149 rhigh failures; establish variance; finalize numbers.
**Actions:** Taxonomy: 49 recoverable coin-flips (gold's inconsistent output formats), ~96 never solved by ANY config incl. larger model (documented defective gold: AND/OR precedence bug, 'Min' answer to a who-question, inverted ratio gold, corrupted question text) → effective ceiling ≈ 80%. Train-set convention mining (9,428 gold): multi-part → 2+ cols 76%; yes/no → 1 col 80%; RANK() OVER ≈ 0 in train gold. Rules updated accordingly. rhigh-v2 run (rules + 12 iters): 67.2 → reasoning-high band 67-70 (±3 run variance; rules neutral). 5-voter ensemble (rh1+rh2+v4+noleak+lean_distill) = 72.4 verified by independent recount (found & fixed own arithmetic slip 72.0→72.4; found dataset's 2 exact duplicate entries bird_137/138 → 498 unique).
**Takeaways:** Voting law: equal-strength voters required; 2 strong + 3 weak works (72.4), 1 strong + N weak fails (67.8). Single-run deltas <2 points are noise. ~19% of mini-dev is benchmark noise.

## 2026-07-09 — Supervisor meeting; eval-set-free finals; clean repo

**Objective:** Implement meeting directives; remove all eval-set contact from the headline.
**Meeting directives (Harshal):** rollouts+result-vote approved; NEVER touch the eval set (mine patterns from train instead); 1-page spec before coding (→ `docs/spec.md`); NEW idea: reasoning-trace folding ("dynamic programming for reasoning" — mine rollout traces for repeated reasoning events, precompute them per-DB; goal: fewer reasoning tokens); start report now, 2 papers/person/week; split work with Hanyan explicitly.
**Actions:** Two ablation runs: train-set few-shot k=1 + rhigh = **69.2** (clean headline); no-fewshot + rhigh = **68.6**. → dev-pool retrieval was never load-bearing. Clean-only 3-voter ensemble (trainfs+nofs+v4) = **71.1**; best-5 = 72.3 (gray-zone runs disclosed). Created clean repository (`db-rlm`): validated pipeline only, README/findings/spec/tasks docs, 9 curated result files; pushed to GitHub; Hanyan added as collaborator; supervisor invited.
**Takeaways:** Final clean story: **55.2 → 64.2 (harness) → 69.2 (reasoning) → 71.1 (clean ensemble)**. Harnessed mini ≈ domain-specific 30B (ReViSQL) bare. Next phase = instrumentation (transcript+token logging) → offline ingestion → trace folding.

## 2026-07-10 — Direction debate resolved; instrumentation shipped; context-scaling built then deprioritized

**Objective:** Respond to Irene/Hanyan's finding that recursion shows no accuracy gain; align on research direction.
**Thread:** Hanyan's ablation (50q): recursion −4% vs baseline. Irene proposed pivoting to long-context/RLM-as-context-management (cited AutoLink, AAAI'26 — agentic schema linking, 97.4% SRR / 68.7% EX on BIRD-Dev via iterative explore/retrieve/verify/expand actions). Built `docs/spec_recursion_at_scale.md` + `scripts/build_megadb.py`: merged all 11 BIRD DBs into one 75-table DB and a 301-table distractor-augmented XL version (questions/gold unchanged, verified 60/60 identical gold results on both).
**Harshal's ruling (overrides the pivot):** explicitly NOT interested in long-context management ("context lengths are within bounds in our problem"). Redefined RLM = (a) reasoning-as-code, (b) execution environment, (c) self-improve + divide-and-conquer — **ReAct is a subset of RLM**, so Aziz's harness gains ARE RLM gains under this framing. Goal: prove RLM is more expressive than prior methods by exceeding SOTA on structured RAG via loop{find mistakes → fix with RLM(online) + offline mining}, cost-performance balanced. Two explicit asks: (1) read all 500 reasoning traces of Aziz's best agent, find the "one wrong turn" pattern, split between Aziz/Hanyan; (2) study Trampoline-AI/predict-rlm for transferable tricks (GEPA last).
**Actions & code:** Instrumentation shipped: token accounting (prompt/completion/reasoning) in `src/rlm/core.py`, transcript logging (`--transcript-dir`, JSONL) in both runners, model name recorded per result. predict-rlm studied → `docs/predict_rlm_notes.md`: key finding — their sub-agent calls are TYPED functions (DSPy signatures), ours are free-text `recursive_llm(query, context)` — plausible root cause for recursion underperforming; their GEPA is the automated version of Harshal's trace-folding idea, our new transcripts are its input format.
**Follow-up thread:** Hanyan asked clarifying questions on scope; Harshal confirmed the "gpt-5.4 vs mini trace comparison for targeted distillation" idea (compare traces, extract patterns the bigger model finds that mini doesn't → guidelines/few-shot) and endorsed keeping model fixed at gpt-5.4-mini until harness is optimized ("bitter-lesson compatible" design constraint — harness must not become obsolete as models improve). Simplified team plan (Hanyan's push after an overly complex first draft): ONE loop, not parallel tracks — generate traces → classify each failure KNOWLEDGE vs REASONING vs GOLD_NOISE → knowledge fixes go to offline mining (Hanyan), reasoning fixes go to scaffold (Aziz) → re-run → repeat.
**Takeaways:** Context-scaling work retained as appendix/future material, not the thesis spine. The team's actual differentiator per Harshal is systematic error-driven iteration, not a single architectural claim.

## 2026-07-10/11 — Traced run + manual trace-analysis workflow live

**Objective:** Generate the 500 traces for the wrong-turn analysis; build the shared workflow.
**Actions & code:** Ran best clean config (train-fewshot k=1 + reasoning-high) with transcripts on: **68.4% official** (5th replication of this config band: 70.2/67.2/69.2/68.6/68.4 → converges ~68.7±1). First real cost measurement: mean **4,072 reasoning tokens/question** (2.0M total) — the number trace-folding must reduce. Built `scripts/render_traces.py` (JSONL+results → readable HTML report, failures listed first) and `scripts/make_classification_sheet.py` (auto-generates the failure list with wrong_turn/error_class/subcategory/fix_idea/notes columns — deliberately blank; filling them IS the task). 158 failures split 79/79 Aziz/Hanyan. Packaged and sent to Hanyan (`traces_full_500.zip`); she initially expected the columns to be pre-filled/automated — clarified the workflow is manual by design (Harshal's own framing: "usually one wrong turn... you can divide these among yourselves").
**Manual classification in progress (Aziz's half, joint session w/ Claude as reading assistant):** ~13 of 79 done. Recurring pattern already visible: `wrong-source-table` in thrombosis_prediction (Diagnosis exists in both Patient and Examination tables; gold consistently uses Patient) hit twice (bird_1198, bird_1238) — candidate for a one-line offline insight fixing multiple questions at once. Also recurring: hint/gold self-contradictions in this DB around age-reference-date (current_timestamp vs record date) and inequality boundaries (">2" vs "two or more"=">=2") — several genuine GOLD_NOISE cases distinct from our earlier ceiling estimate, to be tallied once both halves are done.
**Takeaways:** Manual trace reading is slow (~5-10 min/question) but high-signal — every gold-noise case found is airtight (verifiable against hint text), every reasoning error found points at a concrete, fixable scaffold rule. The repeating-subcategory signal (2+ occurrences) is the practical trigger for "build this as an offline insight."

---

## Open items (rolling)

- Transcript + token logging in runner (prereq for trace folding & cost claims)
- Offline ingestion Stages 1-3 per spec (awaiting supervisor spec review)
- Reasoning-effort sweep (low/medium) + difficulty-aware routing
- Investigator×rhigh, v4×rhigh ablation cells
- Full BIRD dev (1,534) with best config after effort sweep
- Report skeleton + literature (2 papers/person/week)
