# 6. Failure Analysis

## 6.1 Verification Methodology

Every failure discussed in this section was classified against the actual
execution results of the current pipeline (dedup-convention fix, no
per-database hints, `reasoning_effort=high`, 240s timeout), not against
stale results from an earlier configuration. Classification proceeded in
three passes:

1. **Reuse where unchanged.** For each question that had been classified
   in an earlier pass of this project, the predicted SQL and answer under
   the current pipeline were compared against the mechanism recorded
   previously. If the mechanism was unchanged, the classification was
   reused as-is, with the new predicted values recorded as confirmation.
2. **Reclassify where the mechanism shifted.** In several cases the
   underlying bug had changed between passes — for example, a prior
   prompt fix resolved one component of a two-part failure, leaving a
   second, previously-masked issue as the sole remaining cause. These
   were reclassified fresh rather than carried forward.
3. **Live verification where the cause was unclear from the stored
   result alone.** A subset of classifications required executing an
   isolating query directly against the target SQLite database — for
   example, confirming the true numeric maximum of a column independent
   of any SQL bug, or confirming how many rows in a table actually match
   a given filter — rather than inferring the cause from the text of the
   question and query alone.

This process produced 64 classified failures (Aziz's assigned portion of
the current failure population; Hanyan's portion is tracked separately,
see §6.6). One correction of note: an earlier classification of a
question involving a "top four" ranking question was revised from
"ambiguous question" to a plain model misreading, after direct
verification and discussion showed the model's interpretation was the
less natural reading of standard BIRD phrasing, not a defensible
alternative.

## 6.2 Results by Class

| Class | Count | Share | Meaning |
|---|---|---|---|
| GOLD_NOISE | 31 | 48% | The benchmark's own gold query or evidence text is defective |
| REASONING | 21 | 33% | The model had the necessary information and misapplied it |
| KNOWLEDGE | 10 | 16% | The model lacked a fact it could not have inferred from the schema or evidence |
| INFRA_ERROR | 1 | 2% | An infrastructure failure prevented any answer from being produced |
| Mixed (KNOWLEDGE + REASONING) | 1 | 2% | Both a knowledge gap and a reasoning error contributed |

Nearly half of all classified failures are attributable to the benchmark
itself, not the model or the harness. This is corroborated externally in
§6.6.

One case (`bird_159`) was a genuine borderline call between REASONING and
GOLD_NOISE — gold answers in an outlier id-only format that the question's
phrasing does not clearly rule out — and is counted above under
GOLD_NOISE. Disclosed here rather than presented as a clean-cut case, in
keeping with this document's practice elsewhere (e.g. §4.6) of disclosing
judgment calls rather than absorbing them silently into a total.

## 6.3 Recurring, Named Patterns

The following patterns each recurred across two or more independently
classified questions, distinguishing them from one-off defects that do
not generalize into an actionable rule. Counts below were re-derived
directly from `docs/new_classification_sheet_aziz.csv` (subcategory and
notes fields) rather than carried forward from an earlier hand tally; an
initial pass of this table contained several miscounts, corrected here.
Each pattern below is defined to be mutually exclusive of the others (no
question is counted twice), so the counts sum exactly to the number of
classified failures they account for.

| Pattern | Class | Count | Example |
|---|---|---|---|
| Hint gives a defective or contradicted formula | GOLD_NOISE | 6 | `bird_1092` |
| Fanned-out join multiplies rows in gold SQL | GOLD_NOISE | 3 | `bird_197` |
| Hint symbol-legend not translated to real values | REASONING | 2 (+1 external) | `bird_1265` |
| No aggregation before ranking a superlative | REASONING | 2 | `bird_1472` |
| Column-count mismatch (unasked or dropped column) | GOLD_NOISE | 4 | `bird_1144` |
| Column-count mismatch (unasked or dropped column) | REASONING | 2 | `bird_1241` |
| Dedup-convention violation | KNOWLEDGE | 4 | `bird_145` |
| Dedup-convention violation (relapse after fix) | REASONING | 2 | `bird_1227`, `bird_1254` |
| Wrong column selected for the concept asked | KNOWLEDGE | 5 | `bird_1014` |
| Yes/no output rule over-triggered | GOLD_NOISE | 2 | `bird_1205` |
| Yes/no output rule over-triggered | REASONING | 2 | `bird_1338` |
| AND/OR operator-precedence bug in gold SQL | GOLD_NOISE | 2 | `bird_1247` |
| Needless join excludes a valid entity (model- and gold-side mirror pair) | REASONING/GOLD_NOISE | 2 | `bird_1175`, `bird_1251` |

These 13 patterns account for 38 of the 64 classified failures. The
remaining 26 are individually documented defects — mostly gold-side
idiosyncrasies specific to one question — that do not share a mechanism
with any other classified case, and are therefore not actionable as a
single fix.

Note the fanned-out-join pattern above (rows multiply, inflating an
aggregate) is a distinct mechanism from the needless-join-excludes-a-row
pattern below it (a join drops rows that should have counted); an earlier
draft of this table conflated the two into a single inflated count for
the latter, which has been split apart here.

Two patterns are worth flagging as active, if partial, corrections
implemented during this project (§8):

- **Dedup-convention** was the single largest fixable pattern identified
  in an earlier pass of this project (13 of 79 classified failures at
  that time). A prompt rule against unnecessary `DISTINCT`/deduplication
  was added and validated. It remains only partially effective: 6 of the
  64 current failures are dedup-convention violations, including 2 cases
  where the model reintroduces the exact behavior the rule prohibits
  after extended reasoning (`bird_1227`, `bird_1254`), and one case
  (`bird_1227`) where the model achieves the same effect via an `EXISTS`
  subquery rather than the literal `DISTINCT` keyword the rule targets —
  a gap in the rule's coverage, not a failure to follow it.
- **Hint symbol-legend not translated** was identified during this
  project's final week: when a hint provides a mapping such as
  `RNP IN ('-', '+-'); '-' means 'negative'; '+-' means '0'`, the model
  in three independently classified cases (`bird_1265`, `bird_1267`, and
  a third instance surfaced independently by a teammate's parallel
  classification, `bird_1275`) used the left-hand symbol literally as a
  database filter value, rather than translating to the value on the
  right. A corresponding prompt rule was added; see §8.

## 6.4 Worked Examples

**Gold-side TEXT-sorted-as-numeric (`bird_115`).** The question asks: for
the branch (district) in South Bohemia with the largest number of
inhabitants, what percentage of its clients are male? The number of
inhabitants (`A4`) is stored as `TEXT`. Gold's query selects the target
district by sorting this column directly, `ORDER BY A4 DESC`, without
casting. Sorted as text, `'93931'` (Jindrichuv Hradec) outranks
`'177686'` (Ceske Budejovice) because `'9'` precedes `'1'`
lexicographically, despite 177,686 being the larger number by a wide
margin — so gold silently computes its percentage over the wrong
district. The model's query casts the column
(`ORDER BY CAST(A4 AS INTEGER) DESC`) and correctly selects Ceske
Budejovice, the true most-populous district, before computing the male
percentage — confirmed by directly querying both sort orders against the
live database. The two final numbers disagree as a downstream consequence
(gold 44.26%, predicted 40.0%), but the root defect is entirely in the
district-selection step, not in how either side computes the percentage
itself. This is not an interpretation difference; it is a data-type bug
in the gold query's `ORDER BY` clause.

**Gold-side operator-precedence bug (`bird_1247`).** The question asks
for male patients with a normal white-blood-cell count who also have an
abnormal fibrinogen level. Gold's `WHERE` clause is written without
parentheses: `T2.FG <= 150 OR T2.FG >= 450 AND T2.WBC > 3.5 AND T2.WBC <
9.0 AND T1.SEX = 'M'`. Because `AND` binds tighter than `OR` in standard
SQL operator precedence, this parses as `FG <= 150 OR (everything else)`
— any row with `FG <= 150` alone satisfies the condition, regardless of
sex or white-blood-cell count. The model's query parenthesizes the
condition correctly and returns 6 matching patients; gold's unparenthesized
version returns 75, most of which do not meet the stated criteria.

**Gold hint gives an unimplementable formula (`bird_1092`).** The
question asks which league had the most matches in the 2008/2009 season.
BIRD's own evidence field states: *"league that had the most matches in
the 2008/2009 season refers to `MAX(league_name WHERE season =
'2008/2009')`"* — a formula that does not compute what it claims to
(`MAX` on a text column selects alphabetically, not by match count). The
model's own reasoning trace shows it recognized a genuine 4-way tie in
match counts before committing to a query, but deferred to the evidence
field's literal formula per the system prompt's instruction to treat
evidence as ground truth, producing `MAX(League.name)` rather than
correctly returning all 4 tied leagues. This is the clearest documented
case in this project of the "follow the hint literally" instruction
actively working against a question the model would otherwise have
answered correctly.

**Hint symbol-legend not translated (`bird_1265`, `bird_1267`,
`bird_1275`).** All three questions concern the `thrombosis_prediction`
database and share an identical evidence phrasing pattern: a
lab-result column is defined via a legend (e.g. `RNP IN ('-', '+-');
'-' means 'negative'; '+-' means '0'`). In each case, the model filtered
using the literal symbols (`RNP IN ('-', '+-')`) rather than the values
they denote. Live inspection of the database confirms the literal
symbols never occur in the actual column values, so each such query
returns zero rows unconditionally. Once identified, a corresponding rule
was added to the prompt and confirmed to correctly resolve the symbol
translation on direct re-test, though residual, unrelated gaps remained
on two of the three questions (see §8).

## 6.5 Where Failures Diverge From the Common Reasoning Path

Independent of the root-cause classification above, traces from a
50-question sample (both correct and incorrect) were tagged by reasoning
stage — UNDERSTAND, EXPLORE, DRAFT, TEST, REFINE, FINALIZE — to locate
*where* in the model's process a wrong turn occurs, not just *why*. Of
the original 50, 47 traces were tagged (37 correct, 10 incorrect); the
remaining 3 are not accounted for in the tagging sheets and are not
included in the counts below — noted as a gap in this sample rather than
silently omitted.

Of the 10 incorrect traces tagged, 3 involved no real model error at all
(the gold query itself was defective, independent of what the model did:
`bird_1481`, `bird_1526`, `bird_1322`). Of the remaining 7 genuine model
mistakes, 5 occurred at the DRAFT stage and 2 at UNDERSTAND — the model
correctly framed what the question was asking in most cases; the error
was more often introduced while translating that understanding into SQL
than while reading the question, though the sample is small enough
(n=7) that this should be read as a directional finding, not a precise
ratio. Four of those five DRAFT-stage errors are the same recurring bug
in one database (`debit_card_specializing`): ranking a single raw row
instead of aggregating per entity across a period first.

## 6.6 External Cross-Validation

Two independent sources corroborate this classification effort without
having seen it in advance:

**A teammate's independent 163-question classification**, using a
distinct nine-category taxonomy, found several of the same specific
defects by question id, including the operator-precedence bug in
`bird_1247`, the TEXT-sorted-as-numeric defect in `bird_115`, a
boundary-inequality bug matching this project's `bird_1239`
classification, and a third independent instance of the hint
symbol-legend pattern (`bird_1275`, above). One real methodological
difference was identified and remains to be reconciled before the two
classification sets are merged into a single table: the teammate's
convention records a case where gold answers correctly despite a
defective hint as a model error with a defective-hint flag, rather than
as a gold defect outright, which is stricter than the convention used in
this document (§6.1) and would shift some fraction of the GOLD_NOISE
share reported in §6.2 toward REASONING once harmonized.

**Arcwise's published, independently corrected version of the BIRD
mini-dev gold set** (VLDB 2026, arXiv:2601.08778 — the same publication
audits these 498 Mini-Dev items directly and reports 52.8% carrying
annotation errors) provides a second form of external validation at
much larger scale. A same-harness comparison run against the corrected
gold set is reported in §5; the scale of the accuracy gain observed
there is consistent with — and larger than — the roughly half of all
failures attributed to gold defects in this section, reinforcing that
this is not an artifact specific to this project's classification
judgment.

## 6.7 Status

Aziz's portion (64 questions, this document) is complete and
live-verified. Hanyan's portion, classified independently under a
different taxonomy, is tracked separately pending the reconciliation
noted in §6.6; the combined table and final percentages in this section
will be updated once that reconciliation is complete.
