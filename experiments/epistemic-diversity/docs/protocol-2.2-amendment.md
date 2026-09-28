# Protocol 2.2 — local Ollama scheduling and timeout recovery

Prepared before any protocol-2.2 real-model call. Motivated by the preserved
qwen3:14b operational failure: 1 run, 3 calls, approximately 90 seconds,
2 agent_timeout failures and 2 CancelledError call records. See
[failure evidence](qwen3-14b-operational-failure.md). No comparative research
conclusion is inferred from this incomplete operational attempt.

## Fixed scientific factors

Benchmark 2.0.0 files and version are unchanged. The six pilot task IDs remain
v2-synthesis-easy, v2-diagnosis-medium, v2-constraints-medium,
v2-contradiction-hard, v2-missing-easy and v2-causal-hard.
C2/C3, roles, evidence visibility/partitions, prompts, schemas, public criteria
ordering, artifact-only synthesis, seed 20260928 and one repetition remain fixed.
Temperature 0 and maximum output 2048 apply to every generation. The budget is
48 planned calls / 12 runs with default ceiling 60; failures count, no automatic
retry or resume. Metrics, hypotheses and primary comparisons remain unchanged.
The historical three calls remain consumed: one future complete recovery pilot
would make 3 + 48 = 51 attempts across the two cohorts. A new ledger does not
refund those calls or authorize repeated recoveries.

## Local-only accommodation

The explicit `local_ollama` execution profile requires the loopback Ollama
endpoint on port 11434 with path /v1. Worker scheduling concurrency is **1**;
the provider also limits in-flight model calls to **1**. Agent and HTTP timeouts
are **300 seconds per invocation**. One attempt and one model turn are retained.
The `standard` profile retains concurrency 3 and timeout 90 for other endpoints.
Loopback Ollama launches must use the local profile; no silent fallback is allowed.

Workers have no dependency edges, message subscriptions or sibling artifact
access. They receive policy projections from the same task state. Running these
independent workers sequentially changes scheduling, not the manipulated role or
evidence-access factor. Synthesis still waits for all workers and receives their
published artifacts only. Role assignment and partitions use task/seed, not
completion order. Tests compare worker contexts and useful outputs across profiles.

Scheduling can still change latency and operational completion probability.
Local inference can depend on cache, load and backend nondeterminism. Therefore
both C2 and C3 use the same local profile, and protocol-2.1/2.2 cohorts must not be
pooled. Claims of unchanged scientific factors do not claim invariant wall time
or identical real-model outputs. The 300-second deadline is not a whole-run SLA.

## Required seals and fresh paths

Current content seal: `freezes/benchmark-2.0.0-protocol-2.2.json`.
All previous freezes are retained. A binding must reference this verified seal,
explicit model/endpoint, local profile and its new campaign root. `bind-model`
refuses an existing local campaign root and writes its binding at the new root.
Launch refuses a different root or a root containing prior artifacts, including
a prior budget database. The old binding fails current seal validation.

Example new root: `runs/qwen3-14b-protocol22` (must not exist before binding).
`runs/qwen3-14b` is historical and cannot be reused. A failed new attempt requires
another explicitly approved recovery decision, new binding and fresh root;
unused budget is not an automatic authorization to rerun. Model ID, endpoint,
execution profile and concurrency are recorded with the new manifest.

## Validation and authorization

Validate schema/settings guards, both concurrency layers, endpoint/binding/root
checks, cancellation journals, unchanged context visibility and mock outputs.
Run a new offline mock pilot and the runtime/research test suites. These tests
may use fake HTTP fixtures; they must not dispatch to Ollama or an external model.
No real-model run is authorized by this amendment implementation. Human approval
to execute a new real pilot is still required.
