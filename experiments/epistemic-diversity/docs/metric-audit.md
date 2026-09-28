# Metric audit — metric version 2.0.0, before real outcomes

RQ unchanged: compare prompt-level role diversity with information separation.
Primary comparison remains P1 = C3 minus C2. Role/access interventions are unchanged.

## Definitions and amendments

| Metric | Operational definition / audit judgment |
|---|---|
| Task success | Successful runtime; correct canonical conclusion/action sequence; all required facts and insights with valid citations; no unsupported final statements/conflicts; required uncertainty gaps present and no unallowed final unknowns |
| Gold claim coverage | Distinct valid final required fact keys / gold required fact keys; not word overlap |
| Relevant evidence coverage | Distinct relevant IDs supporting valid statements / gold relevant IDs, workers and final separately |
| Useful uniqueness | Union items owned by exactly one worker / union items; separate relevant-evidence, valid-required-fact and required-insight sets |
| Redundancy | (Sum of worker set sizes − union size) / sum; separately evidence/facts/required insights |
| Pairwise overlap | Mean nonempty-pair Jaccard for those same valid sets; not lexical style |
| Unsupported statements | Statement occurrences absent from annotated valid facts/insights or having incomplete/extraneous citation support |
| Contradictions | A canonical subject asserted with multiple normalized values; source/time/scope-qualified reports have distinct subjects |
| Leakage | Known unauthorized source IDs/canaries in observed Context/structured Response; hidden gold markers/keys separately |
| Tokens / latency | Provider-reported tokens (mock character-quarter estimates), monotonic wall time including checkpoints; attempted dispatches count failures |

Required facts cover case-relevant observations, not only the smallest proof of
the selected decision. Optional weak-source reports can be valid without earning
required-fact or relevant-evidence credit. Intermediate insights can be valid but
do not inflate required-insight coverage. Complete supporting sets are exact;
an alternative *annotated* minimal proof is accepted. A true but unannotated claim
can still be marked unsupported: closed-world evaluation is explicitly limited.

V1's `claim_*` sets combined facts and insights; v2 separates them. V1 zeroed
worker evidence recovery when a downstream stage failed. V2 retains actually
observed worker coverage even on synthesis failure, while failed final quality
is zero. This avoids confounding information recovery with final-stage reliability.
Failures remain in run/task denominators. The v1 recorded results are not
recomputed or overwritten. Metrics version is saved in every new record.

## Collective Coverage Gain

For target universe U and worker sets S_i:

`gain = |union(S_i) ∩ U| / |U| − max_i |S_i ∩ U| / |U|`.

Computed separately for relevant evidence, valid gold facts and required insights.
One worker has gain zero. A disjoint allocation can mechanically raise this metric;
it is useful information aggregation, not a measure of creativity or a proof of
superior final accuracy. Unknown/invented claims never contribute.

## Marginal Agent Contribution: a deliberately bounded definition

`marginal_final_support_loss` holds the observed final output fixed. Let F be its
valid required gold fact keys. For each worker, remove its published valid evidence
provenance and recompute what fraction of gold facts in F still has at least one
complete supporting set among the remaining workers' publications. The difference
from the all-worker supported coverage is that worker's marginal support loss.
Per-worker results, mean and maximum are saved. Required-insight support losses
are also saved in diagnostics. A worker contributing nothing can have zero loss;
one dominant worker can account for all support. Alternative proofs are honored.

**This is NOT the change in a newly generated final answer.** It does not run a
counterfactual LLM, estimate causal effect or compute a Shapley value. Losses need
not sum to one: a conjunctive insight can depend on each of several workers.
Publication support is an upper-bound proxy for what a synthesizer could use,
not a guarantee that it reasons correctly. A true leave-one-agent-out generation
ablation would require extra calls and a separate preregistration/budget; none is
silently charged to the 48-call pilot.

## Boundary / interpretation audit

Access authority is derived from stored policies and explicitly released artifacts,
not from the request under inspection. Shared raw access is authorized and must not
be counted as a leak. Counterfactual extra raw exposure remains a separate metric.
Response auditing includes structured outputs rejected later by the executor;
malformed non-JSON HTTP bodies rejected in the existing adapter are not available
as typed outputs. Safe errors, reservations and call journals remain observable.
Canaries detect literal routing failures, not semantic paraphrases or model guesses.

Schemas do not ask for hidden chain-of-thought. Reported source claims, concise
decisions and supporting evidence are the analysis material. No LLM judge or
semantic embedding metric is used. Lexical similarity is only a dataset duplicate
screen, never the primary diversity outcome.

## Statistical checks

Final gold-fact coverage and worker relevant-evidence coverage remain the two
co-primary endpoints. Pilot only runs P1, so its two tests form one Holm family;
P2–P5 are not estimated from absent conditions. Full mock can exercise all five
contrasts (ten tests). Average repetitions within task, then matched task
differences within structural family. Bootstrap (5000 draws), paired sign flips
(exact ≤16 units; otherwise 20,000 seeded draws) and dz use family means for v2.
Report `n_units` and actual `n_tasks` separately. Zero SD gives null dz.

Task descriptives and paired differences remain available. Binary McNemar uses
repetition zero only when there is one task per family (the pilot); with multiple
related tasks/family, only discordance counts are reported, not an independence-
violating p-value. Missing planned pairs are listed; never-attempted records are
not invented. Version/model/protocol cohorts cannot be silently pooled. Six pilot
units cannot establish generalization or equivalence. No primary endpoint was
selected from model performance.
