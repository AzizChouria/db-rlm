# 4. Methodology

## 4.1 Dataset

All experiments are evaluated on the BIRD mini-dev set, a 500-question
subset of the BIRD (BIg Bench for LaRge-scale Database Grounded Text-to-SQL
Evaluation) benchmark (Li et al., "Can LLM Already Serve as A Database
Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs,"
NeurIPS 2023, arXiv:2305.03111), spanning 11 SQLite databases: `california_schools`,
`card_games`, `codebase_community`, `debit_card_specializing`,
`european_football_2`, `financial`, `formula_1`, `student_club`,
`superhero`, `thrombosis_prediction`, and `toxicology`. The 500 questions
contain 2 exact duplicates, giving 498 unique questions; this is disclosed
here rather than silently affecting reported counts.

Each question is provided with a natural-language question, an *evidence*
field (a short piece of external knowledge or definitional hint, part of
BIRD's official task format), the target database, and a difficulty label
(simple / moderate / challenging) assigned by the benchmark's authors. The
gold answer for each question is a reference SQL query; execution results
are compared, not query text.

## 4.2 Evaluation Protocol

Accuracy is measured using BIRD's official execution-accuracy (EX)
protocol: the predicted SQL and the gold SQL are each executed against the
live database, and the two result sets are compared as sets (row order and
exact formatting are not significant, matching how BIRD's own scoring
script evaluates result equivalence).

An earlier phase of this project used a stricter, self-built comparison
(effectively an ordered-list match) before this was identified as a
deviation from the published protocol and corrected. All accuracy figures
reported in this document use the official set-comparison protocol;
figures from before the correction are not carried forward for
comparability.

## 4.3 System Architecture: DB-RLM

The system under test, DB-RLM, is a ReAct-style agent loop in which the
generator model interacts with a live, sandboxed SQLite connection before
committing to a final answer, rather than producing SQL in a single
forward pass from a static schema description.

**Tools.** The model has access to two functions inside a Python
sandbox: `db.execute(sql)`, which runs an arbitrary read-only query
against the target database and returns the result, and
`db.sample_values(table, column)`, which returns a sample of the actual
stored values in a given column. Both are the model's only means of
grounding its query in the real state of the database; no other tool
calls (schema introspection, etc.) are exposed, since the schema is
already provided in the prompt.

**Turn structure.** Each question proceeds through a fixed number of
turns, enforced by the system prompt:

1. *Read + explore* — the model reads the evidence field and the schema,
   and may issue one exploratory `db.execute`/`db.sample_values` call if
   the evidence does not fully define the values or formats needed.
2. *Test* — the model drafts a candidate SQL query and executes it via
   `db.execute`, observing the real result.
3. *Finalize* — the model commits to a final answer via `FINAL("sql")`,
   in plain text, outside of any code block.

The loop may repeat turns 1–2 (up to a configured maximum, 8 in all
experiments reported here) if a query returns zero rows or an execution
error; the model is explicitly instructed never to finalize on a query
that returned no rows. A short list of stop sequences prevents the model
from hallucinating a subsequent turn of the conversation inside its own
response.

The `llm_calls` field recorded per question in the results files is not
the same quantity as the turn cap above: the run harness retries a
question up to 3 times on a transient API error (`scripts/run_bird_
indomain_fewshot.py`), and each retry restarts the turn loop from
scratch without resetting the per-question call counter — so
`llm_calls` can legitimately exceed 8 (observed up to 13–14 in this
project's result files) without the 8-turn-per-attempt cap having been
violated in any single attempt. This is noted here because `llm_calls`
is otherwise easy to misread as a direct measure of turns actually used
within one attempt.

**Few-shot examples.** One in-context example (`k=1`) is retrieved per
question from BIRD's official training split (9,428 question/SQL pairs,
disjoint from the 500 evaluated questions) via sentence-embedding
similarity (`all-MiniLM-L6-v2`, a distilled model built on the
Sentence-BERT framework: Reimers & Gurevych, "Sentence-BERT: Sentence
Embeddings using Siamese BERT-Networks," EMNLP 2019, arXiv:1908.10084),
and injected into the prompt to
illustrate BIRD's output conventions (column selection, formatting of
yes/no answers, etc.), not to supply facts about the target database.

## 4.4 Generator Model

The generator model is fixed at `gpt-5.4-mini` (Azure) for every
experiment reported in this document. This is a deliberate constraint set
for the project: the object of study is how far a harness built around a
fixed, small, general-purpose model can be pushed, rather than how much
accuracy a larger or domain-tuned model would provide on its own. No
experiment in this report varies the generator model; where a
larger-model comparison becomes part of the project's scope, it is
reported as a separate, explicitly labeled ablation, not folded into the
harness results above.

## 4.5 Ablation Protocol

Improvements to the harness are evaluated incrementally, one change at a
time, against the immediately preceding configuration ("Baseline",
"Baseline + X", "Baseline + X + Y", ...), rather than combining multiple
untested changes into a single run. Each change reported as adopted in
this document was validated on a targeted subset before being confirmed
on the full 500/498-question set, to keep the cost of a negative result
low.

## 4.6 Data Integrity and Verification

Two issues were found, disclosed, and corrected during the project,
rather than silently patched:

**Few-shot retrieval leakage.** An early version of the few-shot
retriever selected examples from a pool that included the dev set itself,
without excluding the query question from its own candidate pool. This
allowed a question to retrieve itself as its own worked example on
proximate re-runs, artificially inflating accuracy. The fix excludes any
candidate with an exact text match or near-duplicate embedding similarity
to the current question. All results in this report use the corrected
retriever, which additionally draws exclusively from BIRD's official
training split — a dataset with zero overlap with the 500 evaluated
questions — making this class of leakage structurally impossible rather
than merely filtered.

**Per-call timeout.** The harness enforces a hard timeout on each
individual call to the generator model. This was initially set to 60
seconds, a value that proved too aggressive once `reasoning_effort=high`
was adopted: later turns in a long conversation, with a large accumulated
context, routinely exceeded it, causing 12–13% of questions in early
batches to fail outright with no answer produced. The timeout was raised
in two steps (60s → 120s → 240s), with each step's effect measured
directly by re-running the previously-timed-out questions: at 120s, 3.4%
of the full run still timed out; at 240s, the timeout rate was 0% across
the full evaluated set, and roughly a third of the previously-affected
questions recovered a correct answer once given the time to actually
respond.

**Failure classification methodology.** All failure classifications
reported in Section 6 were verified against the actual execution results
— predicted SQL, predicted answer, gold SQL, and gold answer — rather
than inferred from reading the question and query text alone. Where the
mechanism of a discrepancy was not immediately clear from the stored
results, it was confirmed by re-executing the relevant query directly
against the live SQLite database (e.g., to distinguish a database-side
data artifact from a genuine query defect).

**Run-to-run stability.** Some fraction of any single accuracy figure in
this report is measurement noise rather than a stable property of a
configuration. An earlier working note from this project cited a 42%
flip rate on a 19-question identical-configuration re-run; that specific
figure could not be traced to a source file during a later audit of this
report and is not used here. In its place, a fresh, freshly re-verifiable
test was run for this document: 20 questions, sampled at random from the
full set, run twice through the identical current-best pipeline
(dedup-convention fix, hints off, `reasoning_effort=high`, 240s timeout,
no other change). 1 of 20 questions (5.0%) flipped between runs
(`bird_1239`: correct on the first run, incorrect on the second). At this
sample size a single flip is consistent with anywhere from roughly 0% to
20% true noise, so this should be read as "noise exists and is on the
order of single digits to perhaps 10-15%," not as a precise constant —
but it is measured, and it noticeably narrows the room for the "everything
is noise" reading of small effects elsewhere in this document (§5.2,
§7.2), which should be revisited against this figure rather than the
earlier, unverifiable one.
