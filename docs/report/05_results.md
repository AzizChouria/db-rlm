# 5. Experiments & Results

## 5.1 Harness Ablation

Each row below adds exactly one change to the previous row, holding the
generator model fixed at `gpt-5.4-mini` throughout (§4.4). All figures are
official BIRD execution accuracy (§4.2), full 500-question set (498
unique).

| Configuration | Official EX | Simple | Moderate | Challenging | Δ vs. previous | What it isolates |
|---|---|---|---|---|---|---|
| Baseline 1 — direct schema→SQL, no tools | 55.20% (276/500) | 71.6% | 50.8% | 42.2% | — | No-harness floor |
| Baseline 2 — + keyword table/column filter | 51.60% (258/500) | 68.2% | 47.6% | 37.3% | −3.6 | Naive schema pruning *hurts*, not helps |
| DB-RLM harness (ReAct loop + live tools) | 64.20% (321/500) | 77.0% | 60.8% | 53.9% | +12.6 vs. B2 / +9.0 vs. B1 | Harness alone, `reasoning_effort` unset |
| + `reasoning_effort=high` (current pipeline) | 70.20% (351/500) | 76.4% | 71.6% | 57.8% | +6.0 | Reasoning depth on top of the harness |

Two results stand out. First, Baseline 2's keyword-based table/column
filter *reduces* accuracy relative to the unfiltered Baseline 1, rather
than improving it. Restricting the schema shown to the model removes
tables and columns the filter judges irrelevant to the question's surface
wording; in practice this filter is imprecise enough that it drops tables
the query genuinely needs often enough to outweigh whatever benefit a
smaller, more focused schema provides. This is reported as a negative
result rather than omitted, since it directly bears on this project's
framing: schema pruning is not a free win, and a harness that lets the
model discover what it needs from the live database (rather than being
told, incorrectly, what it needs in advance) avoids this failure mode
entirely.

Second, the single largest gain in the entire ablation — larger than
reasoning effort, larger than any individual prompt fix reported in §6 and
§8 — comes from replacing static schema-to-SQL generation with a live,
sandboxed database connection and a fixed explore-test-finalize turn
structure (§4.3), with no other change to the model. The gain from the
harness is also where it is needed most: on challenging questions the
harness adds +11.7 points over Baseline 1 (42.2% → 53.9%), against +5.4 on
simple questions (71.6% → 77.0%) — live verification pays off more on
questions that are already hard, not less. This is the empirical basis for
this project's central claim (§2.2, §7.1): harness design
substitutes for a meaningful fraction of what model scale would otherwise
have to supply.

Third, enabling high reasoning effort on top of the harness produces a
small *decline* on simple questions (77.0% → 76.4%) alongside its large
gain on moderate questions (60.8% → 71.6%). This is the same pattern
examined in more detail, with a matched high-vs-low comparison, in §5.2:
extra reasoning is not uniformly beneficial, and can occasionally talk the
model out of an answer the harness alone would have gotten right.

## 5.2 Reasoning Effort: A Cost/Accuracy Tradeoff

Holding the harness fixed at its best configuration (dedup-convention
fix, hints off, 240s timeout — §4.6), reasoning effort was compared
directly, high vs. low, on the full 500-question set, with all infra
noise resolved on both sides (0 timeouts either way):

| Reasoning effort | Official EX | Avg. reasoning tokens | Avg. latency | Avg. LLM calls/question |
|---|---|---|---|---|
| `low` | 340/500 = 68.00% | 323 | 13.4s | 2.46 |
| `high` | 351/500 = 70.20% | 4,419 | 66.8s | 2.59 |

High reasoning effort buys 2.2 accuracy points at roughly 13.7x the
reasoning-token cost and 5x the latency per question. Per-difficulty, the
gain is concentrated in the moderate tier and is close to flat or slightly
negative at the extremes:

| Difficulty | `low` EX | `high` EX | Δ |
|---|---|---|---|
| Simple | 79.1% (117/148) | 76.4% (113/148) | −2.7 |
| Moderate | 65.2% (163/250) | 71.6% (179/250) | +6.4 |
| Challenging | 58.8% (60/102) | 57.8% (59/102) | −1.0 |

This pattern — the largest effect in the moderate tier, not the hardest
questions — is consistent with the mechanism documented in §6.5 and
§7.2: extra reasoning helps most when a question needs a non-obvious but
findable workaround, and can occasionally *hurt* on questions the harness
would otherwise get right quickly, by giving the model more opportunity to
reconsider and second-guess a correct first pass (§6.3's dedup-convention
relapse cases are a concrete instance of this). Framed against this
project's stated optimization target — highest accuracy per cost, not
raw accuracy — reasoning effort is a real but expensive lever, not a
free improvement, and the per-difficulty breakdown suggests it is not
uniformly worth its cost across question types.

This project's own measured run-to-run noise floor (§4.6: 5.0%, 1/20, on
a fresh identical-configuration rerun) is well below the 2.2-point
reasoning-effort gap measured on the full 500-question set, which
suggests this specific gap is more likely a real effect than pure noise —
a stronger conclusion than an earlier draft of this document supported,
since that draft relied on a since-retracted 42% noise estimate that
could not be traced to a source. The 20-question check is still a small
sample (§4.6 gives the range this single flip is consistent with), so
this should be read as "probably real," not as definitively settled
without a larger repeated-run study.

## 5.3 The Gold-Set Ceiling: A Same-Harness Comparison

Section 6 argues from manual failure classification that close to half of
this project's remaining failures are defects in the benchmark's own gold
queries or hints, not model errors. That argument is corroborated here by
a direct experiment: the current best pipeline (dedup-convention fix,
hints off, `reasoning_effort=high`, 240s timeout) was run, unchanged, on
Arcwise's independently corrected version of the BIRD mini-dev gold set
(§6.6), rather than the original gold set.

| Gold set | Official EX | Simple | Moderate | Challenging |
|---|---|---|---|---|
| Original BIRD mini-dev | 70.20% (351/500) | — | — | — |
| Arcwise-corrected | 85.54% (426/498) | 91.9% (136/148) | 83.5% (207/248) | 81.4% (83/102) |

Every variable other than which reference answers were scored against —
model, prompt, harness, turn structure, reasoning effort — is identical
between the two rows. The 15.3-point difference is therefore attributable
specifically to the correctness of the gold set, and represents the
cleanest single piece of evidence in this project that a meaningful share
of the accuracy gap on the original benchmark is not reachable by any
model answering the question as intended (discussed further at §7.4).
This run also surfaced and led to the correction of a small, genuine
harness bug — a `null`-vs-empty-string evidence-field handling gap — noted
in full at §7.4 for completeness rather than folded in silently.

## 5.4 Recursion

Recursive delegation — a parent agent pausing its own execution to spawn
a child agent for a sub-query — showed no measured benefit over the
non-recursive harness reported in §5.1 (63.8% vs. 64.2%), a result
confirmed directionally by an independent teammate ablation. Full detail,
including why this comparison is not a clean controlled A/B test and the
working explanation for the null result, is reported as a negative
result in Appendix A rather than in the main text, per this project's
convention of keeping negative/ablation detail out of the main narrative
(§7.2).

## 5.5 Generator Model Comparison (Side Comparison, Not Part of the Ablation)

Every result in §5.1–§5.4 holds the generator model fixed at
`gpt-5.4-mini` (§4.4), by design: the project's research question is about
harness contribution, not model scale, and mixing a model change into the
ablation chain would confound the two. This section reports one bounded
exception, run as a single labeled side comparison rather than folded
into the ablation table above, per the scope noted in Future Work
(§8.8): the same harness, at the same configuration used throughout this
document (dedup-convention fix, hints off, 240s timeout, `k=1`), run
against the larger `gpt-5.4` deployment instead of `gpt-5.4-mini`.

| Model | Reasoning effort | Official EX | Simple | Moderate | Challenging | Avg. reasoning tokens | Avg. latency |
|---|---|---|---|---|---|---|---|
| `gpt-5.4-mini` | low | 68.00% (340/500) | 79.1% | 65.2% | 58.8% | 323 | 13.4s |
| `gpt-5.4-mini` | high | 70.20% (351/500) | 76.4% | 71.6% | 57.8% | 4,419 | 66.8s |
| `gpt-5.4` (normal) | low | **71.60%** (358/500) | 81.8% | 70.8% | 58.8% | 159 | 12.4s |
| `gpt-5.4` (normal) | high | 71.00% (355/500) | 81.8% | 71.6% | 53.9% | 2,268 | 46.1s |

The larger model improves accuracy over mini by 3.6 points at low
reasoning effort and 0.8 points at high effort — a real but modest gain,
well below the 9–15-point gains obtained from harness design and gold-set
correction alone (§5.1, §5.3). This is consistent with this project's
central claim (§7.1): most of the achievable gain on this benchmark comes
from the harness, not from model scale, even when scale is actually
tested rather than assumed.

A second observation is worth flagging without overstating it: on
`gpt-5.4` normal, low reasoning effort slightly *outperforms* high
(71.60% vs. 71.00%), the reverse of the pattern on mini (68.00% vs.
70.20%). The gap is 3 questions on 500, inside this project's measured
noise band (§4.6, 5.0%), so this is reported as a data point, not a
reliable reversal — but it does mean the reasoning-effort/accuracy
tradeoff observed on the mini model (§5.2) should not be assumed to
transfer to a larger model without checking, which this comparison now
has checked, once, at this scale.

This comparison was run once per condition (no repeat), on the original
BIRD gold set, and is not combined with the corrected-gold experiment
(§5.3) or the recursion ablation (§5.4).

## 5.6 Status

§5.1 and §5.2 are final. §5.3 is final as of this writing (426/498, 0
unresolved errors). §5.4's headline numbers are drawn from an earlier
project phase (pre-dedup-fix); a same-pipeline recursion re-test under the
current, post-fix configuration has not been run and is not claimed here
as equivalent — noted as a gap rather than assumed away. §5.5 is a single
run per condition, not repeated, and is reported as a bounded side
comparison rather than as part of the main ablation.
