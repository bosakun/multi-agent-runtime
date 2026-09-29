# Status

## Latest: Protocol 2.4 real Pilot stopped at an evidence boundary

The three-call diagnostic passed its predeclared gate. Protocol 2.4 then stopped
after **4 runs / 15 Pilot calls** (18 total including the diagnostic) at
`v2-diagnosis-medium / C3 / worker_1`: `unknown_evidence_reference`, caused by
the returned citation ID `none` not being in that worker's context. The runtime
rejected the unsupported citation. Leakage counts were 0; this is not an evidence
leak. Eight planned runs remain unexecuted; no performance analysis or figures
were generated. Details: docs/qwen3-14b-protocol24-operational-failure.md.

The consumed binding/campaign remain preserved and cannot be resumed. Any future
attempt needs a new protocol and campaign.

User authorized improvement through Pilot completion. Recovery-v2 is a separate
three-call engineering diagnostic, followed only on a passing gate by a fresh
12-run / 48-call cohort. Shared hard budget 60. C2/C3 both receive 4096 tokens and
1200s in that new cohort; temperature/thinking/benchmark/prompts remain unchanged.
No historical campaign is resumed or pooled. No source covered by an old seal
was edited. See docs/recovery-v2-plan.md and docs/protocol-2.4-amendment.md.

Validation before launch: 252 passed / 3 skipped; formatter, lint, strict types
and both historical seals pass. New Mock Pilot completed 12/12 runs / 48 calls,
zero errors/leaks, under results/protocol24-mock-validation. This is software
validation only; real Pilot completion is not yet established.

## Latest: failure recording and representative-input regression improved (offline)

The pilot is **not fixed or complete**. The 6-call synthetic diagnostic did not
reproduce its failure. An offline workload audit now exposes that gap: the failed
worker had 4 inference rules / 2 decision rules / 14 premise occurrences; the
synthetic fixtures had at most 1 / 1 / 4. These are structural descriptors, not
causal or token estimates.

New `operational_recovery/` uses the exact saved worker request with fake HTTP to
test pre-exception capture of partial final-answer JSON and reported usage.
Hidden reasoning and arbitrary response/error bodies are withheld. Truncation
remains failure; no repair, retry, old-file overwrite or real transport is allowed.
This hook is **not retrofitted into frozen research/diagnostic runners**.
No real calls or new Protocol were added. See
[causes, changes and remaining limits](docs/operational-recovery.md).

Validation: **244 passed / 3 skipped**, formatter/lint/strict types passed;
both seals valid. All 2,805 protected files retain their path/content hash sets.
Evidence: `results/operational-recovery-validation.json`.

## Current: synthetic diagnostic completed; scientific Pilot remains stopped

The separately authorized diagnostic executed **6/6 real calls**, three synthetic
inputs at 2048/4096. All schema-valid / finish_reason stop; no truncation, timeout
or other errors. Thinking stayed model-default. Input/generated/total tokens:
**3116 / 2640 / 5756**; wall time about 3m52s. Both ceilings used the same generated
counts per fixture, far below 2048. **Failure not reproduced; 4096 is not established
as a fix.** See [actual diagnostic results](docs/token-budget-diagnostic-results.md).
Both seals verify and all 228 protected hashes match. No scientific Pilot,
Protocol 2.4, added calls, retry or resume followed.

### Historical: planning and stopped research campaign

Planning approved: a [separate generation-budget diagnostic proposal](docs/token-budget-diagnostic-plan.md)
fixes three synthetic inputs × 2048/4096, one repetition, **6 calls maximum**.
Thinking default, temperature 0, 600s deadlines and concurrency 1 remain fixed.
The plan/inputs were authored without any new model output. Implementation,
independent seal/binding and real launch were subsequently authorized by
「実モデル実行まで」 and completed only for this six-call diagnostic.
No scientific Protocol 2.4 or new research Pilot is authorized.

The authorized real pilot attempted **5 runs / 19 calls**, then stopped on
`v2-constraints-medium / C3`: worker_0 returned `provider_output_truncated`
at 431.35s, with a RuntimeFault journal. This was not a 600s timeout. First
four records succeeded; seven planned records remain unexecuted. Recorded
context/result/gold leakage is zero. No performance analysis or figures followed.

[Failure investigation](docs/qwen3-14b-protocol23-operational-failure.md) separates
observed length termination from unproven thinking/budget hypotheses. New offline
diagnostics and a fake-HTTP-tested response-metadata observer fix the measurement
gap without modifying sealed source or activating the observer in a real run.
This is diagnostic readiness, not a claim that Qwen3 reliability is fixed.
That earlier investigation created no Protocol 2.4, new binding, freeze or real call.
All three campaigns, benchmark and the current freeze remain preserved.

Validation: **207 passed / 3 skipped**, including 17 new offline/fake HTTP tests;
formatter, lint, strict typing and current freeze verification pass. All 228
protected file hashes match. The offline operational report was generated at
`results/protocol23-operational-diagnostics/`; no performance analysis was run.
See [diagnostic validation](docs/protocol23-diagnostic-validation.md).

## Historical: protocol 2.3 operational compatibility preparation

Local Ollama deadline is **600s**, worker/model concurrency **1/1**, temperature
**0**, semantic generation limit **2048**, sent explicitly as `max_tokens`.
Thinking is model-default with no override. Standard remains 90s / three workers
and `max_completion_tokens`. Benchmark, selection, roles, boundaries, prompts,
metrics and analysis definitions are unchanged.

Protocol 2.2 actually executed four runs / 16 calls, then stopped at
v2-diagnosis-medium / C3: three workers succeeded, synthesizer timed out at
300.01s, `agent_timeout` / `CancelledError`, zero recorded leaks. No performance
comparison or figures followed. See docs/qwen3-14b-protocol22-operational-failure.md.

New seal: `freezes/benchmark-2.0.0-protocol-2.3.json`.
Required fresh local binding/campaign: `runs/qwen3-14b-protocol23/binding.json` /
`runs/qwen3-14b-protocol23`. Actual wire fields are verified and journaled before
transport. Old seals/bindings/campaign paths and existing artifacts are refused.
No Protocol 2.3 real model generation, retry, partial resume or main/full run is
authorized by this implementation. See READY_FOR_REAL_PILOT.md.

Preservation evidence: `results/protocol23-preservation.json`; it contains SHA256
baselines for both failed campaigns, benchmark 2.0.0, prompts, configs and archives.
Validation details are in docs/protocol-2.3-validation.md. Mock/fake HTTP results
are software checks, not model quality evidence. Historical sections below retain
the state at their original preparation time, not current execution instructions.

Validation complete: **190 passed / 3 skipped** (68 runtime, 122 research passed).
Formatter, lint, both strict typing checks and freeze verification pass.
New local binding is created and matches the seal; the real campaign contains
only binding.json. A named 2.3 local Mock pilot completed **12 runs / 48 calls**;
outputs, all worker payloads, assignments, condition order and non-resource
metrics match the pre-edit 2.2 baseline and the archived Mock reference.
No real calls or scientific comparison were added. Both historical campaigns,
all benchmark/prompts/configs and all existing archives retain their hashes.

**READY FOR REAL PILOT — software/binding ready, human launch approval pending.**

## Historical: protocol 2.2 local recovery preparation

Benchmark 2.0.0, six pilot task IDs, C2/C3, temperature 0 and output limit 2048
are unchanged. Local Ollama worker/model dispatch concurrency is 1 and timeout
300 seconds. Standard non-Ollama scheduling retains 3 workers and timeout 90.
New content seal: `freezes/benchmark-2.0.0-protocol-2.2.json`, hash
`64123f9c62f55a6c26dff30a582472fffbc8b02ede9a42a3c607fd8896a12154`.

The failed qwen3:14b protocol-2.1 campaign remains byte-for-byte intact: one
attempted run, three calls, 90036.417 ms, two agent_timeout failures and two
CancelledError journal records. It is an operational failure with no paired
research outcome. See docs/qwen3-14b-operational-failure.md and the 2.2 amendment.

Current mock regression: standard and local profiles each executed 12 runs /
48 calls (24 runs / 96 mock calls total). All succeeded; paired final outputs,
assignments, quality and boundary metrics match. No observed literal leaks.
These are offline checks, not additional real-model attempts. Results live in
results/mock-v2p22-standard and results/mock-v2p22-local.

Validation: **161 passed / 3 skipped** (94 research + 67 runtime).
Formatter, lint, strict typing and new freeze verification pass. Existing app/
is unchanged. All 14 failed-campaign files and all 63 benchmark-v2 files retain
their prior SHA256 hashes. Existing .DS_Store files were left untouched.

No protocol-2.2 real run or real binding was created here. Local real launch
requires a new binding referencing this seal and a fresh campaign root;
old bindings, mismatched roots and existing artifacts are refused before dispatch.
See READY_FOR_REAL_PILOT.md for commands, which require approval before generation.

## Historical protocol 2.1 preparation and mock validation

Benchmark **2.0.0 / protocol 2.1**: **30 tasks / ten structural families**, ten each easy/medium/hard.
Fixed six-family C2/C3 pilot: **12 runs / 48 calls**, default ceiling **60**.
Paid main/full are disabled. No real-model calls or paper conclusions were added.

The content freeze was sealed before named protocol-2.1 execution and verifies successfully:
`06e2b3ebac936e8cee2e8f506a74d46664342c9a2d1da2d5c698262a909dd041`.
Model/endpoint selection must be sealed separately before the first paid call.
See [READY_FOR_REAL_PILOT.md](READY_FOR_REAL_PILOT.md) for exact setup/commands.

Executed protocol-2.1 mock pilot: **12 runs / 48 calls**. Then full mock: **150 runs / 510
calls**. All 162 runtime runs succeeded, with zero literal context/output/gold hits.
All final mock tasks passed. These are deterministic pipeline checks, not LLM findings.
Seven figures and per-run human-review reports were generated. Old v1 records,
dataset and app/ source were checked against prior saved hashes and are unchanged.

Validation: **145 passed / 3 skipped** (78 research + 67 runtime passed).
Formatter, lint and both strict typing checks pass. Fake HTTP tests verify the
real adapter's 48-call path, fail-stop, budget refusal and secret-free metadata;
they are not real-model experiments. No remote push; existing local changes retained.

## Superseded protocol-2 validation (preserved)

The initial v2 seal `66653c194ab214816d03d823c07a0ecaf3e58fb40d4eb478ffb5ed651f163121`
and its 12 pilot + 150 full mock runs are retained unchanged. A later pre-real
audit found that authoring placed every correct candidate first. Protocol 2.1
randomizes public inference/candidate order without gold access, identically
across conditions; no task or seed was reselected. See the dated amendment.
All 139 old sealed files match the archived source. Old and new mock cohorts
are separate, not pooled or silently relabeled.

## Historical v1 preparation

Real-model experiment pending because no provider credentials were available.

2026-09-27: environment presence checks found neither MODEL_API_KEY nor
OPENAI_API_KEY. No credential value was read into logs. Research plan fixed before
benchmark/experiment implementation. No real-model results exist at this stage.

2026-09-28 JST: implemented C0–C4, 24 annotated tasks, audited runtime runner,
durable call budget, deterministic metrics, paired analysis and five SVG figures.
Executed mock pilot (10 runs / 34 calls), then full validation
(240 runs / 816 calls). All final mock scores were perfect, with zero detected
boundary/gold leaks. This validates software, not any hypothesis about LLM quality.

Research tests: 26 passed. Existing runtime tests: 67 passed, 3 skipped
(optional external PostgreSQL/live API checks). Detailed final commands are in
docs/validation.md. No changes to app/ and no remote push.

Next: securely configure a compatible provider, select a model and run the
pre-specified real pilot/main (170 planned calls, 180 default ceiling).
Paper outline and protocol abstract are provided instead of fabricated results.
