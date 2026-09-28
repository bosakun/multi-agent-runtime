# Status

## Current: READY FOR REAL PILOT (content/software); model binding and credentials pending

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
