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

---

## Open items (rolling)

- Transcript + token logging in runner (prereq for trace folding & cost claims)
- Offline ingestion Stages 1-3 per spec (awaiting supervisor spec review)
- Reasoning-effort sweep (low/medium) + difficulty-aware routing
- Investigator×rhigh, v4×rhigh ablation cells
- Full BIRD dev (1,534) with best config after effort sweep
- Report skeleton + literature (2 papers/person/week)
