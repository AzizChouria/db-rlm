# 7. Discussion

## 7.1 What Worked, and Why

The largest single gain in this project came from the harness change with
the least engineering novelty: giving the model a live, sandboxed
connection to the target database and a fixed turn structure that forces
it to test a query before committing to it (§4.3). This alone raised
official execution accuracy from 55.2% to 64.2% (§5) — a larger gain than
any subsequent change to the prompt, the reasoning effort, or the few-shot
retrieval strategy. The mechanism is not subtle: most of the failure modes
documented in this project (§6) are grounding failures — a joined table
that does not need to be joined (`bird_1175`, §6.3), a filter value that
does not occur in the real column (the literal-symbol filters in
`bird_1265`/`bird_1267`, §6.4), a hint symbol used literally instead of
translated (same examples) — and a
tool that lets the model observe the real data before finalizing an answer
directly addresses exactly that class of error. This is consistent with
the second-largest gain observed, enabling high reasoning effort on top of
the same harness (64.2% → 70.20%, §5): more of the accuracy this project
recovered came from giving the model room to explore and verify than from
any specific instruction added to the prompt. Reasoning depth was a more
reliable lever than prompt engineering throughout this project's several
rounds of scaffold changes (§7.2).

Put plainly: on this benchmark, harness design and reasoning depth
substituted for a large fraction of what a bigger or fine-tuned model
would otherwise have to supply, without training and without changing the
underlying model at any point (§4.4). This is the central empirical
claim of the project and directly answers the research question posed in
§2.2.

## 7.2 What Did Not Work, and Why

Two negative results are reported here in summary, with full detail and
supporting numbers kept in Appendix A rather than the main text.

**Recursive delegation showed no measured benefit.** Tested directly on
BIRD (63.8% vs. a 64.2% non-recursive baseline), and confirmed
directionally by a teammate's independent ablation. The likely
explanation is a mismatch between the mechanism and the task: BIRD
questions rarely contain a sub-problem large or independent enough to be
worth delegating to a separate agent, and this project's own free-text
sub-call interface may compound the problem. See Appendix A.1 for the
full comparison, its limitations, and the untested hypotheses carried
into Future Work (§8.3).

**Most incremental scaffold changes net close to zero at full-set
scale.** Across the eight prompt rules added this cycle (§6.3, §8),
individually validated on their target failure subsets, the aggregate
effect on full-500 accuracy stayed within this project's measured 5%
noise floor (§4.6) — a more surprising result now than when this project
believed the noise floor was closer to 42%. See Appendix A.2 for the
full argument and the open question of whether the fixes' individual
effects are cancelling out rather than absent.

## 7.3 Relation to Independent External Evidence

This project's central mechanism — inspect the real data before
committing to an answer, rather than reasoning from a static description
of it — is not a claim unique to this project. An independently published
analysis (the SQRL "ask the database first" account: Feyn Inc., "SQRL
Digs Before It Queries," Hugging Face blog, July 2026,
https://huggingface.co/blog/feyninc/sqrl — a blog post, not a
peer-reviewed paper; flagged as such since it carries different weight
as evidence) names the same
failure family this project observed directly: wrong joins, misread
columns, filters against values that do not exist in the real data. That
account and this project were produced independently, on different
systems and different data, and converge on the same diagnosis. This
project's contribution relative to that convergence is not the diagnosis
itself but a demonstration that the fix requires no training and no larger
model — a fixed, general-purpose small model, given the right harness,
recovers a substantial share of the gap on its own (§7.1).

## 7.4 An Effective Ceiling, Not Just a Score

Roughly half of the failures classified in this project — 48% of Aziz's
64-question classified portion (§6.2), with independent corroboration
from a teammate's separately taxonomized classification (§6.6) — are not
model errors at all. They are defects in the benchmark's own reference
queries or hint text: a text column sorted as if numeric
(`bird_115`, §6.4), an
unparenthesized `AND`/`OR` clause that silently changes which rows
qualify (`bird_1247`, §6.4), a hint formula that does not compute what its own prose claims it
computes (`bird_1092`, §6.4). This matters for how the accuracy figures in §5 should be read:
70.20% official execution accuracy on this benchmark's original gold set
is not directly comparable to a hypothetical 100% ceiling, because a
substantial share of the remaining gap to that ceiling is not currently
reachable by any model answering the question as intended — the reference
answer itself would have to be scored wrong to close it.

This is not only an estimate from manual classification. A same-harness,
identical-configuration run of this project's best pipeline
(`reasoning_effort=high`, dedup-convention fix, hints off, 240s timeout)
was repeated against Arcwise's independently corrected version of the BIRD
mini-dev gold set, with no other change to the model, prompt, or harness.
Accuracy rose from 70.20% (original gold) to 85.54% (corrected gold,
426/498, 0 unresolved errors) — a 15.3-point gain attributable purely to
the correctness of the reference answers being scored against, holding
every other variable fixed. The gain is not uniform across difficulty:
simple questions reach 91.9% against corrected gold, moderate 83.5%,
challenging 81.4%, suggesting that gold-side defects are not evenly
distributed and concentrate somewhat more in the harder, more complex
reference queries. One plausible explanation, not directly tested in this
document, is that more elaborate gold SQL (more joins, more clauses) has
more surface area for a defect like a fanned-out join or an
operator-precedence bug (§6.4) to occur in the first place; confirming
this would require measuring gold SQL complexity against defect rate
directly, which has not been done here. This result is the single
cleanest piece of evidence
in this project for the ceiling argument: it isolates the effect of
gold-set correctness from every other variable this project varied, and
its magnitude (+15.3 points) is larger than what the 48%-of-failures
estimate alone would suggest is recoverable, though the two figures are
not directly comparable (one is a share of failures, the other a share of
all questions).

This run also surfaced one small, genuine harness bug, disclosed here for
completeness: two questions (`bird_1507`, `bird_1528`) initially failed
with an unhandled exception, not a wrong answer. The corrected dataset
encodes a question with no evidence field as `null`, whereas the original
dataset used an empty string; the harness called `.strip()` on the
evidence value without a null guard (`scripts/run_bird_indomain_fewshot.py`,
`example.get("evidence", "")`, which only applies its default when the key
is absent, not when its value is `null`). This was fixed
(`example.get("evidence") or ""`) and both questions were re-run
successfully — both landed correct. The 85.54% figure above reflects this
fix; it is a one-line dataset-format compatibility fix, not a change to
any reasoning behavior, and is noted here rather than silently folded in,
consistent with this project's practice of disclosing every correction
made during data collection (§4.6).

Reporting a single accuracy number without this context risks
understating how close a well-grounded small model already comes to the
benchmark's real, answerable ceiling, and risks setting the wrong bar for
what a "better" model or harness should be expected to close.
