# predict-rlm — what they do differently (and what we should steal)

Study notes on Trampoline-AI/predict-rlm ("self-harnessed LM runtime", RLM
adapted for spreadsheets — closest published cousin to our SQL setting).
Per supervisor's ask 2026-07-10.

## Their architecture in one line

The root LM writes Python in a sandboxed REPL and *generates its own control
flow* ("self-harnessed") — no fixed tool-choreography; sub-LM calls are typed
functions (DSPy signatures) invoked from the model's own code.

## Trick-by-trick, mapped to our setup

| Their trick | What it is | Us today | Action |
|---|---|---|---|
| Engine as verifier | model writes formulas symbolically; the spreadsheet engine computes/verifies | ✅ same idea — SQL executed against live DB | none, cite as convergent design |
| Persistent REPL state | Python kernel keeps state across iterations; on timeout, restore a snapshot and tell the model what was lost | 🟡 our repl_env persists within a question, but timeouts lose work silently | low-cost: report lost state to the model after our 30s abort |
| Typed sub-LM calls | children invoked as typed functions (inputs/outputs as fields), not free-chat | ❌ our `recursive_llm(query, context)` is free-text — likely a reason recursion underperforms | **Hanyan's recursion-retry: give children typed, narrow signatures** (e.g. FindJoinPath(tables) → path) |
| Skills | domain bundle = instructions + packages + tools, reused across tasks | 🟡 our prompt+tools is effectively one hand-built skill | frame our harness as a "BIRD-SQL skill"; report vocabulary |
| Self-harnessing | minimal fixed rules; the model directs its own flow | 🟡 we accumulated rule piles — measured ~neutral! | supports our finding; consider *removing* mechanical rules when reasoning-high is on |
| Bitter-lesson compatibility | "performance, speed, and cost of RLM calls correlate directly with improvements to base model capabilities" | ✅ matches our mini→5.4 observation and Harshal's design constraint | quote in report |
| **GEPA / trace-driven optimization** | traces (code, subcalls, timings, tokens) feed an optimizer that *evolves the agent spec* from trajectories | ❌ not built — but **this is exactly the trace-folding direction**: our new transcript logs are the input format | after manual trace analysis, GEPA-style automated folding is the stretch goal (supervisor: "keep GEPA for last") |

## Three takeaways for our roadmap

1. **Recursion may fail because our child calls are unstructured.** Their
   sub-calls have typed signatures with narrow contracts; ours pass free text
   and hope. Before concluding recursion is useless, retry it typed (this
   slots directly into Hanyan's "recursion with problem-specific
   instructions" task).
2. **Our transcript logging = their trace substrate.** They treat traces as
   both interpretability AND training signal (GEPA evolves agent configs from
   them). Manual wrong-turn analysis first (supervisor's ask), automated
   folding second, GEPA-style optimization last.
3. **Less harness, more model** is their philosophy — and our own ablations
   agree (rule piles measured neutral; reasoning depth was the real lever).
   When designing new scaffold pieces, prefer giving the model information
   (precomputed insights) over giving it procedures (rules).
