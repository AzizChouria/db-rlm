# Appendix A. Negative Results and Ablations

This appendix collects the full detail behind negative results and
failed ablations referenced briefly in the main text, per the project's
convention of keeping the main narrative focused on what worked and
pointing detail on what did not to this appendix (§7.2).

## A.1 Recursive Delegation (referenced at §5.4, §7.2)

**What was tested.** A Reactive+Recursive configuration — a parent agent
capable of pausing its own execution to spawn a child agent for a
sub-query, the mechanism most distinctive to the RLM literature beyond
live tool access — was compared against the non-recursive harness
reported in §5.1.

**Result.** It scored 63.8%, at or slightly below the 64.2% non-recursive
baseline it is compared against. This comparison draws on a multi-variant
configuration board from an earlier project phase with an acknowledged
±1.5-point noise band across variants, not a single controlled A/B pair
varying only recursion — the gap should be read as "no measured
benefit," not as a precisely quantified cost. A teammate's independent
ablation on a separate 50-question sample reached the same directional
conclusion (recursion −4% vs. a non-recursive baseline).

**Why this comparison is weaker evidence than a controlled ablation.**
Two limitations apply simultaneously: the comparison is drawn from an
earlier project phase, before the dedup-convention fix and other prompt
changes that later raised the non-recursive baseline from 64.2% to
70.20% (§5.1); and it was never a clean single-variable swap to begin
with — the compared configurations differed in more than just the
presence of recursion. A same-pipeline recursion re-test under the
current, post-fix configuration has not been run (§5.6, §8).

**Working explanation, untested.** The most likely reason recursion did
not help is not implementation failure but a mismatch between the
mechanism and the task: recursion is a specific tool for handing off a
sub-problem to an isolated agent when that sub-problem is complex enough
to be worth the overhead of a separate context. BIRD's own SQL rarely
uses recursion in the query-language sense (`WITH RECURSIVE`), and the
multi-step reasoning BIRD questions do require — e.g. "look up an ID,
then use it in the main query" — is usually cheap enough to do inline,
within the same turn, rather than delegate. A target-density check found
that only 1–3% of failing questions contained a sub-problem of the kind
recursion is designed to solve, consistent with this explanation.

A second, compounding hypothesis: this project's recursive sub-calls
pass free-text context between parent and child, whereas comparable
systems that do report a benefit from recursion appear to rely on typed,
narrow sub-call contracts (e.g. "return the id for value X in table Y")
rather than an open-ended context dump. Neither hypothesis has been
tested directly; both are carried forward to Future Work (§8.3).

## A.2 Incremental Scaffold Changes Net Close to Zero (referenced at §7.2)

**What was tested.** Across several rounds of targeted prompt fixes —
including the eight rules added this project cycle in response to the
verified failure classification (§6.3, §8) — the aggregate effect on
full-500 accuracy was measured before and after each round of merges.

**Result.** The aggregate effect has repeatedly been small relative to
this project's own measured run-to-run noise floor (§4.6: 5.0%, 1/20, on
a fresh identical-configuration rerun — a smaller noise floor than an
earlier, since-retracted 42% estimate an earlier draft of this argument
rested on). This does not mean the individual fixes are wrong: several
were independently validated on the specific failure subset they
targeted before being merged (§4.5, §8), and the mechanism each addresses
is real and verifiable, confirmed by live SQL re-execution in each case.

**Why this is a more surprising result than it first appears.** With the
noise floor now measured closer to 5% than the originally assumed 42%, a
full-500 accuracy delta that stays flat across eight merged fixes is
harder to dismiss as noise than this project initially treated it. A
plausible explanation, not yet confirmed, is that the eight fixes'
individual gains and losses are approximately cancelling across the full
question set — some fixes correct their target cases while incidentally
disturbing others — rather than the aggregate signal being genuinely
absent. This remains an open question; distinguishing "cancels out" from
"genuinely near-zero net effect" would require re-running the full set
with each of the eight fixes toggled independently, which has not been
done.
