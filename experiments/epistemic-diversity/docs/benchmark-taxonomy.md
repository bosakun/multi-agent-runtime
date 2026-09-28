# Benchmark taxonomy — 2.0.0

30 independently authored configurations, ten structural families, three cases
per family (easy, medium, hard). These replace neither the 24 v1 files nor their
results: they live under `benchmarks/v2/`. Selection was made before v2 named runs.

## Families and integration structures

| Family | Reasoning structure (easy → medium → hard) | Required information pattern | Characteristic failure mode |
|---|---|---|---|
| synthesis | independent corroboration → alternative support paths → fork/join certificates | Complementary source observations, clock/identity checks, then source/destination agreement | Repeating one source while omitting a required branch |
| diagnosis | negative control → intervention plus matched control → two interventions eliminating a confounder | Symptoms AND discriminating controls, not temporal coincidence | Selecting the most salient/recent change as the cause |
| constraints | intersection → candidate elimination → infeasibility certificate | Feasible sets, budgets, compatibility, independent mandatory vetoes | Choosing an attractive candidate that violates one mandatory constraint |
| contradiction | temporal revision → scope reconciliation → condition/reliability/time precedence | Attributed reports AND applicability metadata | Counting reports as votes or treating different scopes as a logical conflict |
| missing | missing measurement → absent counterfactual → missing preference weights | Evidence inventory AND an explicit information requirement | Filling an unknown with a plausible guess or invented values |
| causal | two-stage mechanism → gated three-stage propagation → four-stage failed-barrier cascade | Intermediate states AND whether a barrier blocks propagation | Unsupported bridge from initial event to outcome |
| decision | stated preference → Pareto dominance → veto plus reversible alternative | Multiple criteria with explicit decision authority and non-compensatory constraints | Optimizing a single perspective, or averaging away a veto |
| failure | trigger versus amplifier → initiating fault/defense/duration → joint cut set and consequential alarm | Event order, barrier capability, component conjunctions and common contributor | Confusing symptom, primary cause and recovery amplifier |
| planning | ordered prerequisites → parallel preparation then resource join → rollback branch before irreversible cleanup | Prerequisites, resources, test outcome and commit gate | Correct actions in the wrong order or destructive cleanup before success |
| ranking | direct measurement → dependence-aware corroboration → diagnostic intervention versus popularity/recency | Provenance, calibration/scope, independence and controlled interventions | Treating repeated/weak evidence as independent decisive support |

This is not ten entirely separate logical calculi. All tasks are represented by a
small public positive-rule language for auditable deterministic scoring. The
variation is in dependency topology, alternative supports, source attribution,
veto/negative observations, causal roles and ordered decision outputs. There is
no numeric constraint solver, temporal theorem prover or simulator hidden in the
runtime. The easy synthesis/decision and diagnosis/constraint controls share
coarse graph signatures; they are disclosed, not counted as independent proofs of
structural novelty. More difficult members introduce different relationships.

## Task schema / visibility

| Requested concept | Stored field / location | Sent to workers? |
|---|---|---|
| task_id, family | PublicTask.id, family | No; used for selection/provenance only |
| prompt | PublicTask.question | Yes, identical across conditions |
| evidence_items | PublicTask.evidence | According to ContextAccess |
| gold_claims / gold_evidence_ids | Gold.claims / relevant_evidence_ids | Never |
| required/optional insights | Gold.required_insights / optional_insights | Never |
| distractors / weak sources | Gold.distractor_ids / weak_evidence_ids | Labels never; documents follow policy |
| allowed_uncertainty | Gold.allowed_uncertainty / required_unknowns | Never; public rules enumerate possible gaps |
| difficulty, dependency_depth | PublicTask metadata | Not included in model inputs |
| evidence_interaction_type | PublicTask.evidence_interaction_type | Not included in model inputs |
| benchmark version | PublicTask/Gold.benchmark_version | Recorded in results, not a gold hint |

The authoring specification holds public material and private annotations for
compilation only. Runtime construction accepts PublicTask, allowed IDs and model
settings; it cannot load the specification/gold through the model interface.
Public rules describe alternative decision criteria, not which observation holds.
Gold expected decisions and required support witnesses are manually authored and
checked against an independent Boolean closure. Optional intermediate supports
are enumerated by a public provenance engine; this shared representation remains
an evaluator-dependence limitation.

## Difficulty (structural, not calibrated LLM accuracy)

- **Easy:** four relevant observations, one or two inference layers, one principal
  integration relationship, three distractors. Four documents support the decision.
- **Medium:** typically six relevant observations (five may suffice for the
  decision), two or three layers or a join/control/independence relation, plus
  optional weak reports. Several partial conclusions must be combined.
- **Hard:** typically seven relevant observations, or competing mandatory vetoes
  / a forked reconciliation with six observations. These require cross-scope
  precedence, causal-role separation, missing preferences, ordered rollback or a
  longer cascade (up to four inference layers). Difficulty is not assigned solely
  from depth; an infeasibility certificate can have depth two and still require
  checking mutually different candidate failures.

`dependency_depth` is the maximum active inference depth from observed facts
(depth zero), excluding the final decision selection. The audit recomputes it.
Cases have three distractors; some add one or two weak reports. Near-duplicate
screening is lexical and cannot validate human-level difficulty. Labels are fixed
before generation outcomes, not recalibrated to favor any condition.

## Partition fairness and non-favoritism

Partition relevant, weak and distractor strata separately, with seeded bounded
search over 128 balanced candidates. Every document belongs to exactly one worker.
Stratum count ranges are at most one. Choose a candidate minimizing concentration
above 2/3 of a minimal decision-support set, then importance imbalance. Relevant
weights normally equal two; selected highly diagnostic records have weight three
and supporting ranking records weight two. Integer sums need not match exactly;
the audit accepts range ≤3 and records actual weights/counts for each assignment.
No worker can independently hold the whole minimal decision-support set.

Relevance/importance routing remains oracle-assisted. This controls workload but
is not representative of learned retrieval. Roles are shuffled independently for
every task/seed, using the same mapping for C2/C4. No partition is chosen using a
model response. All global evidence is identical across C0–C4. Full-context single
agents can solve every task; contradiction/global-cause/planning tasks plausibly
favor having all premises together. There is no benchmark rule requiring evidence
to be hidden or requiring multiple agents as a prerequisite for correctness.
