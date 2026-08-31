# Aziz's 10-Minute Segment — Content Plan

Target: ~10 min, 7 slides, first half of the joint 20-min talk (Hanyan takes
the second 10). Drop this content into the TUM template yourself — this is
a content plan, not the final slides.

---

## Slide 1 — Title (shared, ~15s)

- Project name, both names, supervisor, date
- One line: "Understanding where an inference-time harness pays off in
  Text-to-SQL, on a fixed small model"

---

## Slide 2 — Motivation & Research Question (~60s)

**Content:**
- Text-to-SQL: natural-language question → executable SQL. Checkable by
  execution, not just by reading — good testbed for agentic reasoning.
- Small models fail when given only a static schema: wrong joins, wrong
  columns, filters on values that don't exist in the real data.
- Research question: **how far can a harness push a fixed, small model —
  without training it or swapping it for something bigger?**
- Generator fixed at `gpt-5.4-mini` throughout every result in this half.

**Script:**
> "Text-to-SQL is a good test for reasoning because the output is checkable
> — you execute the query and see if it's right. But small models given
> just a schema fail in predictable ways: joining tables they don't need,
> filtering on values that don't exist. Our question was: how much of that
> is fixable by changing what the model can *do*, not what model we use?
> We fixed the generator at gpt-5.4-mini for everything I'm about to show
> you."

---

## Slide 3 — System Architecture (~75s)

**Content:** (reuse the 3-step diagram already built)
- ReAct-style loop, live sandboxed SQLite connection
- Two tools only: `db.execute(sql)`, `db.sample_values(table, column)`
- Turn structure: Read+Explore → Test → Finalize
- Up to 8 turns if a query errors or returns nothing; never finalize on an
  empty result

**Script:**
> "Instead of writing SQL blind from a schema, the model gets a live
> connection to the real database. It can run a query, see the real
> result, and revise before committing. Two tools only — execute a query,
> or sample real values from a column. That second one matters more than
> it sounds: a lot of failures come from filtering on a value that just
> doesn't exist in the data, in the format the model assumed."

---

## Slide 4 — Use Case: One Question, Start to Finish (~75s)

**Content — worked example, `bird_1265` (thrombosis_prediction):**
- Question: "How many patients have a normal level of anti-ribonuclear
  protein and have been admitted to the hospital?"
- Evidence hint: `RNP IN ('-', '+-'); '-' means 'negative'; '+-' refers
  to '0'`
- Naive approach: filter literally on `RNP IN ('-', '+-')` → **zero rows**,
  because those literal symbols never occur in the real column
- With the harness: model samples real values, sees the hint's symbols
  don't match stored data, translates to the real values, gets a
  non-empty, correct result

**Script:**
> "Here's a concrete case. The hint says the symbol '-' means 'negative'.
> A naive model uses the symbol itself as the filter value — and gets zero
> rows, silently, because that symbol never actually appears in the
> database. With live access, the model can check: sample the column,
> see the real stored values, and translate the hint correctly. This one
> pattern alone caused several failures in our benchmark, all fixed the
> same way once the model could actually look."

*(This slide doubles as informal demonstration if a live/recorded demo
isn't otherwise covered in Hanyan's half — flag with her.)*

---

## Slide 5 — Headline Ablation Chain (~100s)

**Content — table:**

| Configuration | Official EX | Δ |
|---|---|---|
| Baseline 1 — direct schema→SQL, no tools | 55.20% | — |
| Baseline 2 — + keyword table filter | 51.60% | −3.6 |
| DB-RLM harness — ReAct loop + live tools | 64.20% | +12.6 |
| + reasoning_effort = high | 70.20% | +6.0 |

**Script:**
> "Baseline 1: schema and question, one shot, no tools — 55.2%. Baseline
> 2 tries to help by pre-filtering which tables to show the model — and it
> actually *hurts*, down to 51.6%, because the filter removes tables the
> query genuinely needs. Giving the model the harness — live tools, the
> loop I just showed — jumps accuracy to 64.2%, a 12.6-point gain with
> zero change to the model. Adding more reasoning effort on top adds
> another 6 points, to 70.2%. The harness alone is the single largest
> lever in this entire chain — bigger than the reasoning-effort increase,
> bigger than any individual prompt fix we tried later."

---

## Slide 6 — The Gold-Set Ceiling (~90s)

**Content:**
- Same harness, same config, only the reference answers changed
- Original BIRD gold: 70.20%
- Arcwise-corrected gold: **85.54%** (+15.3 points)
- ~48% of classified failures traced to defects in the benchmark's own
  gold queries — not the model

**Script:**
> "This is the result I'd lead with if I only had one slide. Same model,
> same harness, same everything — we only changed which reference answers
> we scored against, using an independently corrected version of the gold
> set. Accuracy went from 70.2% to 85.5% — 15 points, from nothing but
> fixing the answer key. Close to half of our classified failures traced
> back to defects in the benchmark itself — a text column sorted as if it
> were numeric, a missing parenthesis that silently changed which rows
> qualified. The headline number on this benchmark says as much about the
> benchmark as it does about the model."

---

## Slide 7 — Does a Bigger Model Close the Gap? (~70s)

**Content — table:**

| Model | Effort | EX |
|---|---|---|
| gpt-5.4-mini | high | 70.20% |
| gpt-5.4 (normal) | high | 71.00% |

- Bigger model: +0.8 points at high effort (+3.6 at low effort)
- Small next to the harness (+9–15pts) and gold-correction (+15.3pts) gains

**Script:**
> "One more check: what if we just used the bigger model instead? Real
> gain, but modest — under 1 point at high effort. Compare that to the 15
> points from fixing the harness, or the 15 points from fixing the gold
> set. On this benchmark, model scale is not where the accuracy was
> hiding — the harness was."

**Transition to Hanyan:**
> "That's the foundation — harness over model scale, and a real ceiling
> effect from the benchmark itself. Hanyan is going to show you how far
> that foundation goes when you add more to the pipeline."

---

## Timing check

7 slides, ~485s of script (~8.1 min) + slide transitions/pauses ≈ 9–10 min.
Slide 4 (use case) can be cut to ~45s or dropped entirely if you're
running long — it's the least load-bearing for the core argument, though
it's the one slide that satisfies the official "use case scenario"
requirement, so cutting it means that has to live in Hanyan's half or the
conclusion instead.
