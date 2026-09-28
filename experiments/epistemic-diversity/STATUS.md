# Status

## Current: protocol 2.2 local recovery prepared; new binding and run authorization pending

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
