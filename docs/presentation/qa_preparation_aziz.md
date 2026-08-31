# Q&A Preparation — DB-RLM Final Presentation

Answers are written to be spoken in 20–40 seconds each.
**Bold** = the one-line answer if you're short on time.
⚠️ = a question where the honest answer admits a weakness — say it plainly,
don't dodge. Examiners reward this.
🔧 = you need to fill in a detail I don't have.

---

## 1. Methodology & Validity

**Q: Why only 500 questions? Why not the full BIRD set?**
> **BIRD mini-dev is the official 500-question subset, designed for exactly
> this kind of iteration.** The full dev set is 1,534 questions. We chose
> mini-dev so we could run many configurations repeatedly at reasonable
> cost — the ablation needs each layer run end-to-end. Scaling the best
> configuration to the full dev set is listed as the next step in our
> future work.

**Q: Why does your denominator change between 500 and 498?**
> **The set has two exact duplicate questions.** 500 entries, 498 unique.
> We disclose it rather than silently pick one. On the original benchmark
> we report over 500; on the corrected version, which ships 498, we report
> over 498. The difference is 0.12 points — 70.20% versus 70.08% — so it
> doesn't affect any conclusion.

**Q: How many runs per configuration? ⚠️**
> **Mostly one, and that's a real limitation.** We measured the noise
> directly: 20 questions run twice under identical settings, one flipped —
> a 5% flip rate. So differences under roughly two points on a single run
> shouldn't be treated as reliable. The 9-point tool-loop gain and the
> 15-point benchmark effect are well outside that. The 2.2-point
> reasoning-effort result is closer to the margin, and I'd want repeats
> before making a strong claim about it.

**Q: Did you control sampling? Is temperature fixed? ⚠️**
> **We set temperature to zero, but we later learned the gpt-5 family
> rejects that parameter and the client library dropped it silently.** So
> sampling was not actually pinned. That's a plausible contributor to the
> 5% flip rate we measured, and it's in our limitations.

**Q: How do you know there's no data leakage?**
> We found leakage once and fixed it. An early few-shot retriever drew
> examples from a pool containing the evaluation set, so a question could
> retrieve *itself* — with its own gold answer — as a worked example. We
> caught it, invalidated the affected runs, and rebuilt the retriever to
> draw only from BIRD's official training split, which has zero overlap
> with the evaluated questions. **That makes this class of leakage
> structurally impossible rather than merely filtered.**

**Q: What exactly is your metric?**
> **BIRD's official execution accuracy.** Both the predicted and reference
> SQL are executed against the live database and the result sets are
> compared as sets — row order and formatting don't count. We used a
> stricter ordered comparison early on, noticed it deviated from the
> published protocol, and corrected it. All reported numbers use the
> official protocol.

**Q: Why gpt-5.4-mini specifically?**
> It was fixed as a project constraint by our advisor. The research
> question is what a harness buys on a *fixed* small model — if we swapped
> models mid-experiment, we couldn't attribute any gain to the system.
> **The constraint is what makes the ablation meaningful.**

---

## 2. System & Implementation

**Q: Why only two tools? Why no schema introspection?**
> The schema is already in the prompt, so an introspection call would be
> redundant. What the model *can't* get from the schema is what's actually
> stored — the real values, formats, and casing. **That's the gap
> `sample_values` fills, and it's where most of our grounding failures
> came from.**

**Q: Why a maximum of 8 turns? What happens at the limit?**
> Empirically almost every question finishes in two to three calls, so 8 is
> a generous ceiling rather than a binding constraint. If it's hit, the run
> terminates with a max-iterations error and counts as a failure — we don't
> silently accept a partial answer.

**Q: What if the model writes a query that hangs?**
> There's a 30-second query timeout enforced at the SQLite level via a
> progress handler. We added it after runaway joins caused multi-hour
> stalls — CPU-bound queries don't respond to normal async timeouts.

**Q: Is the sandbox actually safe?**
> Queries run against a read-only connection, and the databases are local
> copies. The Python environment is sandboxed. It's a research setup, not
> a hardened production one — for real deployment you'd want stricter
> isolation.

**Q: Why one few-shot example and not more?**
> The example is there to demonstrate output *conventions* — column
> selection, yes/no formatting — not to supply facts about the target
> database. One example does that. Adding more from a different domain was
> tested earlier in the project and destabilised results.

**Q: What does a question cost? 🔧**
> 🔧 *Fill in if you tracked spend.* What you can say confidently: at high
> reasoning effort, about 4,400 reasoning tokens and 67 seconds per
> question; at low effort, 323 tokens and 13 seconds. **The accuracy
> difference between those is 2.2 points — so the cost-optimal setting
> depends entirely on how much that's worth to you.**

---

## 3. Interpreting the Results

**Q: Why does Baseline 2 hurt? Schema pruning is standard practice.**
> **Because our pruner was deliberately naive — keyword overlap, top-five
> tables.** It removes structural information the query later needs, and a
> dropped table is unrecoverable, whereas a redundant one is merely noise.
> It's a negative control, not a serious retrieval method. Hanyan's half
> shows that a *well-built* schema retriever does help — which is the real
> lesson: the idea is sound, the naive implementation isn't.

**Q: Is 70% good? How does it compare to the leaderboard? 🔧**
> 🔧 *Don't quote a leaderboard number you haven't verified.* Safe framing:
> **the original BIRD paper reports GPT-4 at 54.89% and human performance
> at 92.96%.** We're not claiming state of the art — our contribution is
> the decomposition of *where* inference-time gains come from on a fixed
> small model, not a leaderboard position.

**Q: Why does more reasoning make simple questions worse?**
> Our reading: on easy questions the model usually has the right answer on
> the first pass, and extra reasoning gives it room to reconsider and talk
> itself out of it. We see this concretely in one recurring case — a rule
> the model follows correctly at low effort, then reasons its way back
> into violating after extended thinking. **It's a small effect, inside
> our noise band, so I'd call it a suggestive pattern rather than a
> finding.**

**Q: Your tool-loop gain is +9, the second half reports +13.85. Why different?**
> **Different benchmark versions.** Ours is measured on the original BIRD
> gold, the second half on the corrected version. Bad reference answers
> suppress the measured gain — some correct answers get marked wrong — so
> the same mechanism looks smaller on the noisier ruler.

**Q: What's the real ceiling then?**
> That's the point of the ceiling slide: **there isn't a fixed one, because
> it depends on the reference answers.** The same system scores 70% or 85%
> depending purely on which version of the benchmark you score against. A
> ceiling is a property of the measurement, not only of the model.

---

## 4. Failure Analysis

**Q: Who classified the failures? Was it independently verified? ⚠️**
> **I classified 64 myself; my teammate independently classified a separate
> 163 under a different taxonomy.** There was no blind second review of the
> same questions, which is a genuine limitation. What we do have is
> convergence: we independently flagged several of the same specific
> defects by question ID without coordinating, which is some evidence the
> classification isn't arbitrary.

**Q: Isn't classifying your own system's failures biased? ⚠️**
> Yes, and in a specific direction we can name. **A failure-only audit can
> only see cases where a bad reference hurt us — never cases where a bad
> reference accidentally gave us a point.** That's exactly why the second
> half's full-dataset comparison matters: it captures both directions and
> shows the net effect is much smaller than a failure-only audit suggests.

**Q: How did you verify a classification was right?**
> Not by reading the query — by executing it. Where the cause wasn't clear
> from the stored results, we ran an isolating query directly against the
> live database. For example, to confirm the text-sorting defect, we ran
> both orderings and compared which district each returned.

**Q: What's the single most common fixable pattern?**
> A deduplication convention: BIRD's reference answers usually don't
> deduplicate joined rows for counts and averages, and the model does. It
> was the largest recurring pattern we found. We wrote a prompt rule for
> it, and it's now **partially** fixed — one case still violates the rule
> even though the rule explicitly forbids it, which suggests more prompt
> text isn't the answer.

---

## 5. The Benchmark Critique

**Q: If BIRD is this defective, why use it at all?**
> Because it's the standard benchmark in this area and comparability
> matters. **Our point isn't that BIRD is unusable — it's that a single
> accuracy number on it should be read alongside its annotation quality.**
> And this isn't only our claim: the corrected version we used comes from
> a published audit that reports 52.8% of these questions carrying
> annotation errors.

**Q: Why trust Arcwise's corrections over the original?**
> We don't take them on faith — the value is that they're *independent*.
> They were produced without seeing our system, so when their corrections
> agree with defects we found ourselves by execution, that's genuine
> cross-validation. We also don't claim their version is perfect; we
> report both rulers.

**Q: Did you report the defects back to the benchmark authors? 🔧**
> 🔧 *Answer honestly — I believe you haven't.* Good response: "No, and
> that would be a reasonable contribution to make. Our defects are
> documented per question ID, so they're in a form that could be
> submitted."

---

## 6. Related Work & Novelty

**Q: What's novel here beyond applying an existing framework? ⚠️**
> Fair challenge. **We're not claiming a new architecture — we're claiming
> a decomposition.** The RLM paper proposes three mechanisms as a bundle.
> What we contribute is measuring them separately on a structured-data
> task and showing the return is extremely uneven: nearly all of the gain
> comes from one mechanism, and one shows no measurable benefit at all.
> That's information the original framework doesn't give you.

**Q: SQRL reports ~70% on BIRD with training. You got 70% without. Isn't that a wash?**
> **It's actually the interesting comparison.** Same architectural idea —
> inspect the database before answering. They reach it with
> execution-based reinforcement learning; we reach a comparable number on
> a frozen model with no training at all. That suggests how much of their
> result comes from the architecture versus the training. I'd note their
> figure is on the full dev set and ours on mini-dev, so it's indicative,
> not a like-for-like comparison.

**Q: How does this relate to CHESS, DAIL-SQL, CHASE-SQL? 🔧**
> 🔧 *Only answer in detail if you've read them.* Safe response: "Those
> are stronger, more engineered Text-to-SQL pipelines with schema linking
> and candidate selection. We weren't trying to compete on accuracy — our
> constraint was a fixed small model and no training, which rules out most
> of what those systems do."

---

## 7. Process & Reflection

**Q: How did you split the work?**
> I built and evaluated the core loop — the baseline chain, reasoning
> effort, the benchmark-ceiling comparison, the model-scale test, and a
> 64-question failure classification. Hanyan built the three layers on top
> and the mechanism-attribution analysis. We ran independent
> classifications and compared them afterward, which gave us a
> cross-check.

**Q: What surprised you most?**
> **That correcting the benchmark moved the number more than any change we
> made to the system.** We spent weeks on prompt fixes worth fractions of
> a point, and fixing the reference data was worth fifteen.

**Q: What would you do differently? ⚠️**
> Two things. **Repeat runs from the start** — we ended up with single runs
> for several results and had to measure our own noise floor retroactively.
> And **pin the sampling parameters properly**, which we assumed were fixed
> and weren't.

**Q: What's the most important next step?**
> Re-running the reasoning-effort comparison on the corrected benchmark.
> We know the benchmark version shifts results by 15 points; we don't yet
> know whether it changes the *shape* of the effort curve. That's cheap to
> run and it's the one open question that could change an interpretation.

---

## 8. Sharp / Adversarial

**Q: Your +6.0 step bundles several changes. Isn't that poor experimental practice? ⚠️**
> **Yes — that step isn't a clean single-variable comparison, and I
> wouldn't present it as one.** It bundles reasoning effort with prompt
> fixes from the same cycle. That's exactly why we ran the isolated
> comparison: reasoning effort alone is +2.2, not +6.0. The chain shows
> the pipeline's progression; the controlled experiment shows the
> mechanism.

**Q: You retracted a noise figure. How do we trust the rest? ⚠️**
> **Because we retracted it ourselves, during our own audit, rather than
> being caught.** A 42% flip-rate figure appeared in an early working note
> and we couldn't trace it to any source file. We removed it and ran a
> fresh measurement — 20 questions, two identical runs, one flip. Every
> number in this talk traces to a result file we can re-execute.

**Q: Your recursion result predates your own later fixes. Is it still valid? ⚠️**
> **Not fully, and we say so.** It was measured on an earlier pipeline
> before our prompt fixes, and it came from comparing configurations that
> differed in more than just recursion. We report it as "no measured
> benefit," not as a quantified cost, and a re-test under the current
> pipeline is listed as outstanding work.

**Q: Isn't 48% of failures being the benchmark's fault suspiciously convenient?**
> It would be, if it were only our judgment. **Three things support it:**
> each classification was verified by executing the queries, not by
> reading them; an independent teammate classification flagged several of
> the same defects by ID; and a published external audit of these same
> questions reports a comparable rate. I'd still frame it as 48% *of the
> 64 I classified* — not of all questions.

---

## If You Genuinely Don't Know

> "I don't have that measured — what I can tell you is [nearest thing you
> did measure]. That'd be worth checking."

Never invent a number. An examiner will forgive a gap far more readily
than a figure that doesn't survive follow-up.
