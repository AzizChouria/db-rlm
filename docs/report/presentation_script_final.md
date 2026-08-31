# Final Presentation — Speaking Script (Aziz, first 10 minutes)

Slide numbers match the compiled TUM deck.
Total spoken time ≈ 8.5–9 min, leaving buffer inside the 10-minute half.

---

## Slide 1 — Title  ·  ~15s

> "We're Aziz and Hanyan, and this is our project on DB-RLM — extending
> Recursive Language Models to Text-to-SQL. I'll cover the foundation and
> a few core findings, then Hanyan will take over with the extended
> pipeline."

---

## Slide 3 — Why Text-to-SQL Is Hard  ·  ~75s

> "Text-to-SQL is a good setting to study reasoning because the answer is
> verifiable — you run the query and check the rows.
>
> But failures happen at four different layers. A query can pick the wrong
> table. It can execute fine but count rows when it should count entities.
> It can filter on a value that simply isn't in the database in that form.
> And it can compute exactly the right thing and still be marked wrong
> because the benchmark expected two columns instead of one.
>
> The third one — execution grounding — motivates everything I'll show
> next: **a query can be perfectly valid and still wrong, because the model
> doesn't know what's actually stored in the database.**"

---

## Slide 4 — State of the Art: Recursive Language Models  ·  ~70s

> "The framework we build on is Recursive Language Models, from MIT. The
> idea: instead of stuffing everything into the context window and asking
> the model to answer from what it read, treat the data as an external
> environment the model can *query with code*. On text, that means writing
> a script instead of reading six hundred thousand characters.
>
> RLM defines three mechanisms — programmatic exploration, an executable
> environment, and self-improvement plus divide-and-conquer.
>
> Our project asks what happens when that external environment is a live
> SQL database. And a big part of our result — mostly in Hanyan's half — is
> that these three mechanisms do **not** pay off equally."

---

## Slide 5 — Research Questions & Experimental Setup  ·  ~65s

> "Three questions. How much can we improve a frozen model by changing only
> what it can do at inference time. Which mechanisms actually cause the
> gain. And what's blocking further improvement.
>
> The constraints are part of the research question. We never swap the
> model, never fine-tune it. Gold answers are used only to grade after a
> run and to diagnose failures afterward — never inside the loop.
>
> That rule matters. Early in the project we found our own few-shot
> retriever was pulling a question's *own* gold answer back in as an
> example. We caught it, disclosed it, and rebuilt the retriever to draw
> only from the training split. Every number after that point is clean.
>
> What we *are* allowed to change: the tools, the environment, precomputed
> knowledge, and post-processing — as long as each can be switched off and
> measured separately."

---

## Slide 7 — DB-RLM Architecture  ·  ~85s

> "This is the complete system. The root agent works inside a persistent
> Python environment — it can execute SQL against the live database, sample
> the values actually stored in a column, see errors or empty results, and
> revise before it commits. That revise loop is the core mechanism.
>
> It has two tools. Execute a query and see the real result. Or sample real
> stored values before filtering on them — that second one matters more
> than it sounds, and I'll show you why on the next slide.
>
> The three dashed boxes — schema retrieval before the agent, an optional
> sub-agent, and post-processing after — are the layers Hanyan covers in
> the second half. I'm covering the core loop."

---

## Slide 8 — Architecture as Experimental Design  ·  ~60s

> "The architecture is also the experimental design. Rather than comparing
> a simple baseline against one big agent and reporting a single number, we
> add exactly one capability at a time. That means the final score
> decomposes — we can say how much each mechanism actually contributed,
> instead of just that the whole thing works.
>
> I'll cover layers zero and one — the baseline and the tool loop. Hanyan
> covers layers two through four. I also have two studies that sit outside
> this chain: a negative control, where naive schema pruning made things
> *worse*, and a reasoning-effort sweep."

---

## Slide 10 — Use Case: From Hint to Correct Filter  ·  ~75s

> "Here's one real question, start to finish. It asks for patients with a
> 'normal' level of a lab marker, and the hint gives a legend: the symbol
> minus means *negative*.
>
> A model working blind from the schema uses that symbol literally as the
> database filter — and gets zero rows, silently, because that symbol never
> actually appears in the real column. It's not an error. It's just wrong,
> and quiet.
>
> With live access, the model can sample the actual column, see the stored
> values don't match the symbol, and translate the hint correctly before
> finalizing. This exact pattern caused multiple failures in our benchmark
> — all fixed the same way, once the model could actually check."

---

## Slide 12 — Ablation Results  ·  ~95s

> "So how much does this buy? Baseline 1: schema and question, one shot, no
> tools — 55.2%.
>
> Baseline 2 tries to help by pre-filtering which tables the model sees —
> and it actually *hurts*, down to 51.6%, because the filter removes tables
> the query genuinely needed. That's a useful negative result on its own:
> naive schema-shrinking isn't automatically good.
>
> Giving the model the tool loop jumps accuracy to 64.2% — a 12.6-point
> gain, with zero change to the model itself. Adding reasoning effort on
> top adds another 6 points, to 70.2%.
>
> And the per-difficulty breakdown shows *where* it pays off: plus 5.4
> points on simple questions, but plus 11.7 on challenging ones. Live
> verification helps most where it's needed most."

*(If asked: the +6.0 step also bundles other prompt fixes made in the same
cycle. Reasoning effort in isolation is +2.2 — that's the next slide.)*

---

## Slide 13 — Reasoning Effort: Accuracy vs. Cost  ·  ~70s

> "One clean controlled experiment — same system, same data, only the
> reasoning budget changes. High effort buys 2.2 points, for nearly
> fourteen times the reasoning tokens and five times the latency per
> question. That's a real tradeoff, not a free win.
>
> The per-difficulty breakdown is more interesting than the average. The
> entire gain sits in the moderate tier — plus 6.4 points. Simple questions
> actually get slightly *worse* with more reasoning, and challenging ones
> barely move.
>
> So more thinking helps when a question needs a non-obvious workaround the
> model can find. But on easy questions, it mostly gives the model room to
> talk itself out of an answer it already had right."

---

## Slide 14 — A Benchmark-Imposed Ceiling  ·  ~90s

> "This is the result I'd lead with if I only had one slide. Same model,
> same system — we only changed which version of the benchmark we ran
> against, using an independently corrected version. Accuracy went from
> 70.2% to 85.5%. Fifteen points.
>
> And look at the scale of what was corrected: of 498 questions, 215 gold
> queries, 147 question texts, and 140 hints were revised.
>
> We traced this ourselves. Of the 64 failures I classified in detail, 31 —
> about half — came from defects in the benchmark. A text column sorted as
> if it were a number, so ninety-three thousand ranked *above* a hundred
> and seventy-seven thousand. A missing parenthesis that silently changed
> which rows qualified. A hint whose formula didn't compute what it
> claimed.
>
> The headline accuracy number on this benchmark says as much about the
> benchmark as it does about the model. This also explains where the second
> half's numbers start: the same one-shot baseline scores 55% on the
> original benchmark and about 70% on the corrected one."

---

## Slide 16 — Model Scale Comparison  ·  ~60s

> "One last check: what if we just used the bigger model instead of
> improving the system? Real gain, but modest — under one point at high
> reasoning effort, 3.6 points at low.
>
> Compare that to nine points from the tool loop, or fifteen from
> correcting the benchmark. On this benchmark, the accuracy wasn't hiding
> in model scale."

---

## Handoff to Hanyan  ·  ~10s

> "That's the foundation — the tool loop beats model scale, and the
> benchmark itself imposes a real ceiling. Hanyan will now show how much
> further that foundation goes once you add the remaining three layers."

---

# Timing Summary

| Slide | Topic | Time |
|---|---|---|
| 1 | Title | 0:15 |
| 3 | Why Text-to-SQL Is Hard | 1:15 |
| 4 | State of the Art: RLM | 1:10 |
| 5 | Research Questions & Setup | 1:05 |
| 7 | DB-RLM Architecture | 1:25 |
| 8 | Architecture as Experimental Design | 1:00 |
| 10 | Use Case | 1:15 |
| 12 | Ablation Results | 1:35 |
| 13 | Reasoning Effort | 1:10 |
| 14 | Benchmark-Imposed Ceiling | 1:30 |
| 16 | Model Scale Comparison | 1:00 |
| — | Handoff | 0:10 |
| | **Total spoken** | **~12:50** |

> **Note:** this is over the 10-minute half. Section-divider slides (2, 6,
> 9, 11, 15) add a few more seconds each. To land at 10 minutes, trim the
> three longest — slides 12, 14, and 7 — or agree an 11/9 split with
> Hanyan, since this half carries the architecture and experimental design
> for both.
>
> **Fastest cuts if running long:** drop the leakage anecdote on slide 5
> (−20s), shorten slide 12 to the chain without narrating each difficulty
> row (−25s), and cut the last sentence of slide 13 (−15s).

---

# Likely Q&A — Prepared Answers

**"Is the +6.0 from reasoning effort alone?"**
> No. That step bundles reasoning effort with other prompt fixes made in
> the same cycle. Isolated, reasoning effort is +2.2 points — 68.0 to 70.2.

**"Why is your baseline 55% but the second half starts at 70%?"**
> Same baseline, different benchmark version. One-shot generation scores
> 55.2% on the original BIRD gold and about 70% on the corrected version.
> That 15-point gap is the ceiling effect on slide 14.

**"How do you know these differences aren't noise?"**
> We measured it: 20 questions run twice under identical settings, one
> flipped — a 5% flip rate. Differences under about two points on a single
> run shouldn't be treated as reliable.

**"Isn't 48% of failures being benchmark defects a very strong claim?"**
> It's 48% of the 64 failures I classified in detail, not of all questions
> — and a failure-only audit can only see cases where a bad reference hurt
> us, never cases where it accidentally helped. Hanyan shows the
> full-dataset picture, which is more nuanced.
