# Spec: Recursive vs Flat Schema Exploration at Scale (v0.1)

*Tests whether the RLM's recursive mechanism adds value where its premise
holds — schemas too large to stuff into context. Builds on AutoLink's
published experimental design (arXiv 2511.17190, AAAI'26), replacing their
flat exploration agent with our recursive one. Joint spec with Irene/Hanyan —
for supervisor review before implementation.*

## Hypothesis

On small schemas, flat agentic exploration ≈ recursive exploration (recursion
is overhead). As schema size grows, a single flat agent's context fills with
exploration transcript (context rot) while a recursive parent stays lean by
delegating regions to child agents that return distilled findings. Recursion
should therefore win on accuracy and/or tokens **only at scale** — this is
the original RLM claim, tested in the database domain (SQ2 + SQ3).

## Arms (minimal pair + references)

1. **Flat exploration (AutoLink-style)**: one agent, actions =
   explore_schema / retrieve_schema (vector store over schema) /
   verify_schema / add_schema / stop; ≤10 turns; no full schema in prompt.
2. **Recursive exploration (ours)**: identical actions and budgets, plus
   `spawn_child(subtask)` — children explore a schema region or sub-question
   with their own context and return candidate schema elements + notes.
   The ONLY difference vs arm 1.
3. *(reference)* Full-schema stuffing — our current pipeline, where it fits.

Generator model: gpt-5.4-mini everywhere (supervisor constraint). Same SQL
generation stage for all arms; only schema linking differs.

## Benchmarks & scaling axis

- **Phase 1 (have it today):** BIRD mini-dev questions over progressively
  larger schema contexts: single DB (~7 tables) → all 11 BIRD DBs attached as
  one schema (~80 tables) → +renamed distractor table copies (~300+ tables).
  Questions and gold unchanged; only the haystack grows.
- **Phase 2 (stretch):** Spider 2.0-Lite (547 cases, 158 DBs, up to 3,000+
  columns) for direct comparison with AutoLink's published numbers.

## Metrics (AutoLink's, adopted)

- **Strict schema-linking recall (SRR)**: linked set ⊇ gold schema elements
- **Execution accuracy** (official protocol, `shared/evaluator.py`)
- **Tokens/question** (input+output; requires token logging — instrumentation task)
- **Parent-context size at termination** (the context-rot signal, ours)

Each cell: ≥100 questions; deltas <2 points treated as noise (measured
variance). Incremental ablation format per supervisor's rules.

## Success criteria / possible outcomes

- Recursion > flat at large scale on SRR/EX or tokens → first positive
  evidence for recursive DB exploration (SQ2 answered yes at scale)
- Recursion ≈ flat everywhere → honest negative for SQ2 with the strongest
  test design available; flat exploration still validates SQ3 vs stuffing
- Both >> stuffing at scale → SQ3 answered regardless

## Non-goals

No bigger generator models; no training; schema vector store is built from
schema metadata only (never eval-set questions/gold).
