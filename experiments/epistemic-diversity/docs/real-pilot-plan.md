# Real pilot plan — pilot-2.1 / benchmark 2.0.0

Protocol 2.1 preserves all choices below and adds task/seed-dependent common
randomization of public inference-rule and decision-candidate order. See
protocol-2.1-amendment.md for the discovered author-order confound and preservation
of the old seal/results. No paid model outcomes informed this correction.

Frozen selection based on metadata, before v2 named runs or any real response.
This is a feasibility/safety pilot, not the main experiment. Research question:
How does epistemic diversity created by information separation compare with
prompt-level role diversity in LLM multi-agent systems?

## Fixed tasks and reasons

| Task ID | Family | Difficulty | Selection reason |
|---|---|---|---|
| v2-synthesis-easy | synthesis | easy | Distributed corroboration / basic extraction control |
| v2-diagnosis-medium | diagnosis | medium | Intervention and matched-control integration |
| v2-constraints-medium | constraints | medium | Multi-constraint candidate elimination |
| v2-contradiction-hard | contradiction | hard | Time, scope and reliability resolution |
| v2-missing-easy | missing | easy | Correct explicit uncertainty, not forced guessing |
| v2-causal-hard | causal | hard | Four-stage propagation with a failed barrier |

One case from each of six families; two cases per difficulty. No task is replaced
because a mock or real output is poor. Non-pilot families remain in the full
benchmark and all-condition mock check, not in this paid pilot sample.

## Conditions and budget

C2 = three role-diverse shared-context workers + synthesizer.
C3 = three neutral-role partitioned-context workers + the identical synthesizer.
One repetition; experiment seed **20260928**. Shuffled condition order and seeded
role/partition mapping. The seed does not control upstream model sampling.

6 tasks × 2 conditions × 4 calls = **48 planned calls**, 12 runs.
Default `MAX_MODEL_CALLS=60`. No retries, tools, debate rounds, judges or ablations.
All five conditions over these tasks would be 102 calls; C0/C1/C4 are therefore
not part of this budget-constrained pilot. They remain unchanged in the design.
P2–P5 cannot be answered by this pilot. A 47-call remaining budget is refused,
not converted into an outcome-dependent smaller subset. Unused reserve is not
automatically spent. The budget is persisted per campaign; failed calls count.

## Model configuration and pre-call binding

One Chat Completions-compatible provider/endpoint and one explicit model ID for
every worker and synthesizer across conditions. Temperature 0, maximum completion
tokens 2048, timeout 90s, max attempts 1, max model turns 1, no tools. Same worker
output schema, same final schema, same task/global evidence and same synthesizer.
Only the role factor changes role text; only the access factor changes visibility.

No real model ID is selected in the environment today. To avoid pretending this
choice was frozen, readiness has two stages: content freeze now, then an immutable
`bind-model` file with actual model ID and normalized endpoint **before any paid
call**. Generation settings/seed/endpoint must match that binding at launch.
The binding contains no API key. `MODEL_NAME` is a shell convenience, not an
automatically selected provider. Unsupported schema/temperature parameters cause
the pilot to stop; there is no silent fallback to different generation settings.

## Stopping and failure policy

- Missing credentials, missing/changed freeze or mismatched binding: refuse before
  dispatch. Real main/full and legacy real execution are disabled in this phase.
- After the first attempted case with transport, runtime, schema or boundary
  failure: persist the record/trace and stop. Concurrent in-flight worker calls
  may already have been charged; each is reserved and journaled before sending.
- A semantically wrong but schema-valid answer is retained and does NOT stop the
  pilot. Do not replace its task or remove its result.
- Existing phase paths cannot be overwritten. Interrupted/failed attempts retain
  reservations, per-call journal and runtime database. No automatic paid resume.
- Correct a genuine bug through a dated amendment/new freeze and an explicitly
  budgeted subsequent pilot; never silently overwrite the failed cohort.

## Metrics / comparisons / human review

P1 = C3−C2 on final gold-fact coverage and worker relevant-evidence coverage.
Other required quality, useful-diversity, collective gain, fixed-output marginal
support, leakage and resource metrics are descriptive. See metric-audit.md for
formulas and family-level inference; no success threshold is used to cherry-pick
scientific results. Gold required unknowns determine correct uncertainty.

Every attempted record includes version, commit/source hash, settings, roles,
partitions, outputs, usage semantics and errors. `pilot-human-review.md` presents
task, worker outputs/citations, final answer, gold, metrics and tentative failure
tags. Human reviewers should examine both successful and unsuccessful cases,
including all-identical evidence, lost premises, unsupported bridge claims and
source-attribution mistakes. A clean pilot authorizes no automatic main run.
