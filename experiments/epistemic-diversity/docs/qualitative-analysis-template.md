# Qualitative review template

Use `pilot-human-review.md` alongside paired C2/C3 records. Inspect successful and
failed cases; do not infer a cause from an aggregate correlation. Automatic tags
in the report are candidates only; role/partition causation needs further evidence.

| Pattern | Evidence to inspect | Alternative explanation / caution |
|---|---|---|
| all agents repeat same evidence | Valid evidence/fact sets and pairwise overlap | Appropriate agreement is not necessarily waste |
| useful unique contribution | Gold-valid unique facts, sources or required insights | Disjoint routing mechanically forces some uniqueness |
| conflicting interpretations | Same resolved subject, incompatible values, source scope | Different attributed sources/times are not automatically contradictions |
| missing global context | An inference's missing premises in each worker Context | Deliberate local uncertainty may be correct |
| synthesis failure | Worker publications contain valid support but final output omits/distorts it | Lost citation provenance versus actual reasoning failure |
| role bias | A role systematically omits/counters supported claims across shuffled assignments | One case cannot establish role causality |
| partition-induced failure | Required premises split, subsequent synthesis cannot reconstruct | Model sampling or schema issues may instead explain it |
| hallucinated bridge claim | Derived claim lacks a complete supported premise chain | Strict gold may be incomplete; reviewer checks source |
| dominant agent effect | Only one worker's removal loses fixed-output support | Provenance proxy is not a regeneration ablation |

For each case record: task/version, condition/run IDs, exact relevant excerpts,
source IDs, valid/missing claims, tentative labels, competing explanation,
reviewer, confidence, and follow-up that could falsify the interpretation.
Assign direction (C2 only success / C3 only success / both / neither), but do not
limit review to favorable discordant cases. Do not edit benchmark gold to match
an output without a separately documented annotation correction/new version.
