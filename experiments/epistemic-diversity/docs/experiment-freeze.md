# Experiment freeze — content protocol pilot-2.1 / benchmark 2.0.0

Prepared 2026-09-28 JST. Protocol 2.1 adds a pre-real candidate-order correction,
documented in protocol-2.1-amendment.md. The old mock cohort/seal remain archived.
The current seal precedes named protocol-2.1 runs and all real execution.
The machine-readable seal is `freezes/benchmark-2.0.0-protocol-2.1.json`; `verify-freeze` checks
its own digest and all listed current file contents before v2 execution. Existing
seals cannot be overwritten. Any post-freeze scientific change requires a new
dated protocol/benchmark version and disclosure, not a favorable-outcome edit.

## Fixed scientific design

RQ: **How does epistemic diversity created by information separation compare with
prompt-level role diversity in LLM multi-agent systems?**
RQ1 useful recovery/performance; RQ2 overlap; RQ3 combined factors; RQ4 resources
and leakage; RQ5 single-agent trade-offs remain unchanged. H1 more distinct
relevant coverage with isolation; H2 substantial shared-context overlap despite
roles; H3 more unique valid contributions with separation; H4 possible combined
benefit with overhead; H5 possible fewer unauthorized transfers. All may fail.
Authorized shared exposure is not evidence for H5.

C0 single/full/neutral; C1 three identical/full; C2 three roles/full;
C3 three identical/disjoint; C4 three roles/disjoint. Same base model and settings,
schemas, no tools, bounded DAG and artifact-only common synthesis for C1–C4.
No world model, additional runtime features or unrestricted discussion.

Benchmark version **2.0.0**: 30 IDs generated as the Cartesian product
`v2-{family}-{difficulty}`, with family in
`synthesis, diagnosis, constraints, contradiction, missing, causal, decision,
failure, planning, ranking` and difficulty in `easy, medium, hard`.
Each is an authored configuration, not three substitutions of one truth template.
All 30 exact entries and files are enumerated and hashed in the manifest/seal.
Relevant/weak/distractor balance and integer importance tolerance are fixed in
benchmark-taxonomy.md. No task requires isolation to be solvable by full context.

## Fixed paid pilot scope

IDs, in plan order:

1. v2-synthesis-easy
2. v2-diagnosis-medium
3. v2-constraints-medium
4. v2-contradiction-hard
5. v2-missing-easy
6. v2-causal-hard

C2 and C3 only; one repetition; seed **20260928**; 48 calls, default ceiling 60.
No automatic main experiment or extra ablation. All-condition mock validation is
separate and cannot answer the LLM question. Model ID/endpoint remain unbound
until explicitly chosen, then must be sealed with `bind-model` before paid calls.
Temperature 0, completion limit 2048, timeout 90s, one attempt/turn and zero tools
are already fixed. Model binding and content hash are saved with each campaign.

## Fixed endpoints / comparisons / analysis

Co-primary: final valid gold-fact coverage, worker-union relevant-evidence coverage.
Task success, required insights, uncertainty, useful uniqueness, redundancy,
collective gain, fixed-output marginal support loss, contradictions, unsupported
claims, literal leakage, calls/tokens/latency are secondary/descriptive.
No unknown-price estimates; no judge. Exact definitions are in metric-audit.md.

Full-design P1 C3−C2; P2 C2−C1; P3 C3−C1; P4 C4−C3; P5 C3−C0.
Only P1 is estimated in the paid pilot. Average repetitions per task, then paired
differences within family; 5000 percentile-bootstrap draws, exact sign flips up
to 16 families (else 20,000 sampled), fixed analysis seed 20260927, paired dz
undefined at zero variance. Holm across the pilot's two co-primary tests (ten
for an explicitly planned future all-condition design). Task descriptives and
per-task differences retained. Binary McNemar on repetition zero only when one
task per family; otherwise counts without an independence-assuming p-value.

## Exclusions and stopping

No attempted run is excluded for low semantic quality. Runtime/schema/transport
or boundary errors stop further real cases, but remain in outputs/denominators.
Wrong answers alone do not stop execution. Unexecuted planned cells are listed
as missing, not generated or silently treated as successful. Paired analysis
requires an observed matching pair; missing pairs and all single-condition error
records remain visible. No task replacement or cherry-picked case deletion.

## Known limitations fixed before outcomes

Symbolic canonical language, oracle relevance/importance routing, no true model
belief independence, per-call rather than total-token matching, only six pilot
families, subjective difficulty labels, closed-world exact evaluation, no live
provider validation yet, literal rather than semantic leakage checks. Shared
simple-rule controls and family ancestry remain disclosed. A post-hoc analysis
must be explicitly labeled exploratory and cannot replace these endpoints.
