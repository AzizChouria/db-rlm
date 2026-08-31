# 2. Introduction

## 2.1 Motivation

Text-to-SQL — translating a natural-language question into an executable
SQL query against a real database — is a natural benchmark for whether a
language model can reason reliably about structured, verifiable data. Unlike
open-ended generation tasks, a Text-to-SQL answer has an objective, checkable
correctness criterion: the query either returns the right rows or it does
not.

In practice, small and mid-sized general-purpose models perform this task
poorly when given only a static schema and asked to produce SQL directly.
The typical failure modes recur consistently: the model joins tables that do not need to be joined, selects a
column whose name resembles the question's wording but is not the one the
question actually asks about, or filters on a literal value that does not
occur in the real data (a misremembered code, an incorrectly cased string,
a symbol from a hint that was never translated to the value it represents).
This project's own failure classification independently reproduces every
one of these patterns with concrete examples (§6.3, §6.4) — e.g.
`bird_1175`'s needless join and `bird_1265`/`bird_1267`'s untranslated
hint symbols — so the claim above is backed directly by this project's own
evidence, not asserted from the literature alone.
None of these are reasoning failures in the abstract; they are failures of
*grounding* — the model is answering from what it expects the database to
contain, not from what the database actually contains. A plausible but
untested account of why this worsens as schema and hint text grow —
attention spread across more irrelevant detail — is not directly
evaluated as an ablation in this project and is stated here as motivation,
not as a finding this document establishes. A closely related diagnosis
has been published independently outside this project: Feyn Inc.'s SQRL
system ("SQRL Digs Before It Queries," Hugging Face blog, July 2026,
https://huggingface.co/blog/feyninc/sqrl — a blog post, not a
peer-reviewed source) names the same
failure family — wrong joins, misread columns, filters against values
that do not exist — independently of this project, on a different
system and different data. This project's report treats it as one
converging account, not as an established consensus across "several"
independent sources, since only this one has been directly checked
against.

The Recursive Language Model (RLM) framework (Zhang, Kraska, and Khattab,
"Recursive Language Models," arXiv:2512.24601) proposes a specific answer to
this problem: instead of asking a model to *read* a large or complex
artifact and answer from memory of what it read, give the model a sandbox
in which it can *query* that artifact programmatically, and let it act as
the author of small, verifiable steps rather than the sole source of the
final answer. Applied to text, this means writing a Python or regex script
against a large string rather than scanning it token by token. Applied to
a database, the direct translation is a live, sandboxed connection: the
model does not need to hold the schema and its contents in its own working
memory at all — it can ask the database directly, observe the real result,
and only then decide what to do next.

## 2.2 Research Question

This project's research question, following the framing set by the
project's supervisor, is deliberately narrow: **how far can a harness
built around a fixed, small, general-purpose language model be pushed on
Text-to-SQL, without training that model or substituting a larger one?**
The generator model is held fixed at `gpt-5.4-mini` throughout every
experiment reported in this document (§4.4); every reported improvement is
a property of the harness — the tools available to the model, the
structure of its interaction loop, the content of its system prompt — not
of the model's own capability. This constraint is intentional. It isolates
the question of interest: whether careful harness design is a substitute
for model scale on this task, and by how much.

## 2.3 Contributions

This document reports three contributions, corresponding to the project's
three main experimental threads:

1. **A harness ablation on BIRD mini-dev**, isolating the effect of live
   database access and of increased reasoning depth from the effect of the
   underlying model, which does not change across any configuration
   compared. Moving from direct schema-to-SQL generation to a ReAct-style
   loop with a live, sandboxed database connection raises official
   execution accuracy from 55.2% to 64.2% with no change to the model
   (§5); enabling high reasoning effort on top of that harness raises
   accuracy further, to 70.20%, at a measured cost of roughly 13.7x the
   reasoning tokens and five times the latency per question (§5, §6).

2. **A verified failure taxonomy with named, recurring fix candidates.**
   Every classified failure in this project was checked against the
   actual execution results of the current pipeline, and — where the
   cause was not evident from those results alone — confirmed by
   re-executing an isolating query directly against the live database
   rather than inferred from reading the question and query text (§6.1).
   This process found that close to half of all remaining failures are
   attributable to defects in the benchmark's own gold queries or hint
   text, not to the model (§6.2), and identified several specific,
   recurring error patterns precise enough to motivate a targeted prompt
   fix rather than a general appeal to "better reasoning" (§6.3, §8).

3. **A recursion ablation, reported as a negative result.** The RLM
   literature's most distinctive claim beyond live tool access is
   recursive delegation — a parent agent pausing its own execution to
   spawn a child agent for a sub-problem. This project tested that
   mechanism directly on BIRD and found no measured benefit over a
   plain, non-recursive ReAct loop at equal cost; a teammate's
   independent ablation on a separate question sample reached the same
   conclusion. This is reported plainly, as a finding the data supports,
   rather than omitted or reframed as an implementation gap (§7).

## 2.4 Document Structure

Section 3 surveys the published work this project builds on and departs
from. Section 4 describes the dataset, evaluation protocol, system
architecture, and the data-integrity issues found and corrected during the
project. Section 5 reports the harness ablation results. Section 6
presents the failure taxonomy in full, including worked examples grounded
in real SQL. Section 7 discusses what the results imply about harness
design versus model scale, and Section 8 outlines the specific, mostly
already-scoped next steps this project's findings motivate.
