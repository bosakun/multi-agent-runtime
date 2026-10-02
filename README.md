# Isolated Agent Runtime

A Python multi-agent runtime centered on explicit information boundaries, typed
publications, durable state, and inspectable execution. Independent implementation;
no proprietary code or prompts and no agent framework.

## What is this?

An extensible asyncio runtime in which agents have separate context, memory
namespaces, knowledge access, tools, schemas, model configuration, execution
budgets, and publication permissions. A central orchestrator runs a validated
DAG and commits typed results into durable state. It includes two applications,
an HTTP API, a CLI, offline evaluation, and adversarial boundary tests.

This repository was designed from general engineering principles. It contains no
code, prompts, documents, or internal architecture from previous projects.

## Why Multi-Agent?

Use multiple agents when separate responsibilities need **different information
and authority**, or when independent analyses should precede evaluation. For
example, an investigator sees one source while a reviewer sees only published
findings. The reviewer cannot fetch the investigator's private memory.

Multiple calls can increase cost, latency and failure opportunities. The included
single-agent baseline is deliberately competitive: all fixture modes can solve
the same task. The benchmark measures the overhead and information exposure of
each arrangement, without assuming that more agents produce better answers.

## Five-minute local run

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). No API key or Docker is
required for the local demos. Run these commands from the repository root:

```bash
uv sync --locked
uv run python -m app.cli run --workflow investigation --input examples/investigation.json
uv run python -m app.cli run --workflow software_review --input examples/software_review.json
```

The CLI prints progress to stderr and a JSON result containing `run_id` to stdout.
SQLite persists runs in `runtime.db` by default. Copy a returned ID:

```bash
uv run python -m app.cli inspect <run_id>
uv run python -m app.cli inspect <run_id> --mermaid
uv run python -m app.cli inspect <run_id> --content
uv run python -m app.cli inspect <run_id> --revision 1
```

`--content` explicitly includes potentially sensitive artifact payloads. Default
inspection shows information categories, artifact/message routes, events, model,
attempts, latency, usage and safe error codes.

Example progress:

```text
[START] investigator_a attempt=1
[START] investigator_b attempt=1
[START] investigator_c attempt=1
[DONE] investigator_a 12.5ms
[DONE] investigator_b 12.7ms
[DONE] investigator_c 12.8ms
[START] reviewer attempt=1
...
```

## Design principles and architecture

```mermaid
flowchart TD
    Entry[CLI / FastAPI] --> O[Orchestrator + validated DAG]
    O --> State[Authoritative WorkflowState]
    State --> Policy[ContextBuilder: allowlists + ACLs]
    Memory[Private / Shared / Long-term memory] --> Policy
    Policy --> A[Detached AgentContext]
    A --> Executor[Bounded Agent executor]
    Executor --> Provider[Mock / OpenAI-compatible provider]
    Executor --> Tools[Permission-checked Tool gateway]
    Provider --> Validation[Schema + evidence-scope validation]
    Validation --> Publications[Versioned artifacts + routed messages]
    Publications --> State
    O --> Storage[Atomic events + snapshots + projections]
    Storage --> Trace[CLI / Mermaid / evaluation]
```

- Information isolation is enforced by code. Agents receive no state or repository
  handle. Projection uses exact allowlists and copies mutable values.
- Communication uses Pydantic outputs, artifact versions, explicit recipients and
  typed references. The model cannot route arbitrary private contexts.
- Workflow state determines execution. Dependencies, branch predicates, joins,
  approval nodes, retries and timeouts are explicit data.
- Uncertainty includes confidence, assumptions, evidence IDs and unknowns.
- The runtime stores public decisions and evidence, never hidden chain-of-thought.
- Provider, repository, memory, schemas and tools have separate extension points.

Agent lifecycle:

```mermaid
stateDiagram-v2
    [*] --> Scheduled
    Scheduled --> ContextBuilt
    ContextBuilt --> Running
    Running --> Validated
    Validated --> Published
    Published --> StateCommitted
    Running --> Retry: transient error / malformed output
    Retry --> Running: budget available
    Running --> Failed: permanent error / exhausted budget
    Running --> Cancelled
```

Parallel execution uses bounded batches and deterministic commits. Event sequence
is commit order; event timestamps preserve actual worker start/completion times.
Independent branches survive agent failure. A join can explicitly accept partial
results. Rejected approval skips the gated branch; run traversal may succeed
without producing a final artifact, which task evaluation treats as unsuccessful.

## Demo applications and information flow

Distributed Investigation splits three conflicting sources across investigators,
then reviews findings, detects conflicts, and synthesizes a report:

```mermaid
flowchart LR
    EA[Evidence A] --> A[Investigator A]
    EB[Evidence B] --> B[Investigator B]
    EC[Evidence C] --> C[Investigator C]
    A -->|findings| R[Reviewer]
    B -->|findings| R
    C -->|findings| R
    R -->|reviewed findings| D[Conflict Detector]
    D -->|findings + conflicts| S[Synthesizer]
```

Reviewer, Conflict Detector and Synthesizer have no raw evidence access. Publishing
a finding intentionally grants its configured readers access to that finding.
It does not grant access to the source context or private memory.

Software Change Review runs four specialists in parallel:

| Agent | Visible inputs | Tools |
|---|---|---|
| Architecture | Architecture description, changed filenames | None |
| Security | Changed code, dependencies, security constraints | `scan_python` |
| Test | Requirements, tests, changed behavior | None |
| Maintainability | Diff, design constraints | None |
| Final Reviewer | Published specialist findings | None |

`scan_python` parses submitted code using Python's AST and never executes it.
The final reviewer receives structured findings without original code or tests.
All schedules, publication rules and context policies live in the applications;
neither demo adds conditional application logic to the orchestrator.

## Human approval and recovery

```bash
uv run python -m app.cli run --workflow investigation --input examples/investigation.json --approval
uv run python -m app.cli resume <run_id> --approve approval
# Alternatively:
uv run python -m app.cli resume <run_id> --reject approval
uv run python -m app.cli cancel <run_id>
```

Approval and definition snapshots survive process restarts. `resume` without a
decision cannot bypass a paused approval. Interrupted runs resume from the last
committed batch. External calls have at-least-once recovery semantics, so tool
handlers must be read-only or idempotent. Live cancellation must target the process
executing the run: use the API cancel endpoint for API runs. CLI cancellation is
appropriate for inactive, paused or interrupted runs.

## API

```bash
uv run uvicorn app.api.main:create_app --factory --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
curl -s http://127.0.0.1:8000/workflows
curl -s http://127.0.0.1:8000/agents
curl -s -X POST http://127.0.0.1:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{"workflow":"investigation","input":{"task":"Investigate a conflict","knowledge":{"evidence_a":{"id":"evidence_a","content":"service.health = healthy"},"evidence_b":{"id":"evidence_b","content":"service.health = degraded"}}}}'
curl -s http://127.0.0.1:8000/runs/<run_id>
curl -s http://127.0.0.1:8000/runs/<run_id>/events
curl -s http://127.0.0.1:8000/runs/<run_id>/graph
```

`POST /runs` returns HTTP 202 while execution proceeds in the background. Control
endpoints are `POST /runs/{id}/approvals/{node}` with `{"approved":true}`,
`POST /runs/{id}/resume`, and `POST /runs/{id}/cancel`. OpenAPI is at `/docs`.
This is an operator API: bind to localhost and add authentication/authorization
before exposing it. The read endpoint includes results, but omits raw source
documents and private contexts. Run one API worker in v1.

## Single vs. Multi comparison

```bash
uv run python -m app.cli evaluate --workflow investigation --input examples/investigation.json --case examples/investigation.case.json
uv run python -m app.cli evaluate --workflow software_review --input examples/software_review.json --case examples/software_review.case.json
```

Each experiment runs A: single agent, B: multiple agents with all raw inputs
explicitly shared, and C: multiple agents with isolated policies. Baseline
selection never modifies the isolated definitions. Use `run --mode single` or
`run --mode shared` to retain those traces in the normal repository.

Metrics include task success, completeness, conflicts, missed conflicts,
unsupported claims, leakage canaries, extra raw context categories, model calls,
tokens, latency, cost estimates and agent failures. Fixture ground truth is
separate from generation. See [evaluation methodology](docs/evaluation.md) and
[sample results](docs/evaluation-results.md).

The mock parses explicit fixture claims and review markers; it does not reason or
verify facts. Its tokens are character-count estimates and its monetary cost is
zero. These results demonstrate runtime behavior, not multi-agent quality gains.

## Storage and Docker

SQLite works without infrastructure. PostgreSQL uses the same Repository
interface, JSON-backed schema and optimistic revision checks. Each checkpoint
atomically stores the run, ordered events, immutable snapshot and projections for
agent runs, artifacts, messages and usage. Agent/workflow definitions and memory
have separate tables. Alembic owns the deployed schema.

```bash
docker compose up -d --build
docker compose ps
# API: http://127.0.0.1:8000/docs
docker compose stop
```

Compose starts PostgreSQL, runs migrations, then starts the API as a non-root
user. Data remains in the named volume after stopping. The Compose password is a
local demo value; set `POSTGRES_PASSWORD` for deployments. Never commit `.env`.

For a fresh local schema explicitly managed by migrations:

```bash
DATABASE_URL=sqlite+aiosqlite:///migrated.db uv run alembic upgrade head
DATABASE_URL=sqlite+aiosqlite:///migrated.db uv run alembic check
```

Runtime initialization can bootstrap an empty database for convenience. Do not
run the initial migration on an already bootstrapped database without an operator
review of its schema and migration version.

## Model providers and configuration

The default is `MockProvider`. `OpenAICompatibleProvider` uses `httpx` against
`chat/completions`, JSON-schema structured outputs, and function tool calls.
Provider-specific types do not enter the runtime domain.

Export `MODEL_PROVIDER=openai`, `MODEL_NAME` for a model supporting this protocol,
`MODEL_BASE_URL` ending in `/v1/`, and `MODEL_API_KEY` from your secret manager.
`.env.example` is a template; the application does not automatically load it.
Credentials never enter AgentDefinition, model context, snapshots or events.
The endpoint must support `temperature`, `max_completion_tokens`, JSON schema and
the selected tools; compatibility across every model/vendor is not assumed.

Model prices are explicit per-agent configuration (`input_cost_per_million` and
`output_cost_per_million`); zero means unconfigured, not free real inference.
Usage for failed network calls may be incomplete because billing data is absent.
Set `RUNTIME_LOG_LEVEL=INFO` to emit content-free event JSON on stderr.

## Tests and development

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -q
```

The default suite is offline and uses MockProvider plus mocked HTTP transport.
Run the same integration/security tests against PostgreSQL:

```bash
docker compose up -d postgres
TEST_POSTGRES_URL=postgresql+asyncpg://runtime:runtime-local-only@127.0.0.1:5432/runtime uv run pytest -q
# With the Docker API running:
TEST_API_URL=http://127.0.0.1:8000 uv run pytest -q tests/e2e/test_live_api.py
```

Tests include secret sentinels, memory namespaces, detached contexts, artifact
ACLs, forged message references, evidence-scope violations, injection-triggered
tool denial, retries, timeouts, concurrency, approval restart, cancellation,
stale writers, migration drift, API contracts and both demos in all three modes.
The GitHub Actions CI template at
[docs/github-actions-ci-template.yml](docs/github-actions-ci-template.yml) covers
Python 3.12/3.13 with SQLite and PostgreSQL. It is not active from `docs/`; enable
it under `.github/workflows/` after granting the GitHub credential workflow scope.

## Extending the runtime

Register Pydantic input/output schemas, construct AgentDefinitions, define a
WorkflowDefinition with nodes/edges/conditions, and submit through Orchestrator.
Graphs can be loaded with `WorkflowDefinition.model_validate_json(...)`; they
are data, not hard-coded scheduler branches. Add a provider by implementing
`ModelProvider.generate`, or a tool with typed inputs, outputs and an async
handler. See [extension guide](docs/extensions.md).

## Limitations

- A single process owns scheduling. Revision checks prevent stale commits, but
  are not distributed leases and cannot prevent duplicate external effects.
- Trusted Python extensions are not sandboxed. Context policy constrains model
  inputs; it cannot prove semantic confidentiality or prevent a model guessing.
- Publishing is explicit declassification. A permitted summary can disclose its
  source; application authors must design schemas and recipients appropriately.
- Untrusted-data markers do not solve prompt injection by themselves. Tool and
  context authority is checked independently of model compliance.
- Snapshots, artifacts and memory can contain sensitive content. Database
  encryption, access controls and retention are deployment responsibilities.
- Replay restores committed snapshots with their event history. It is not a
  deterministic replay of LLM calls or an event-only state rebuild.
- Full snapshots and JSON projections favor auditability over storage efficiency.
  Trace pagination, tenant isolation, automatic retention, rate limiting and
  distributed queueing are not implemented.
- Memory writes are explicit trusted host operations. There is no automatic
  long-term promotion, retrieval ranking, or vector database.
- Live paid-model quality and robustness require separate experiments; the HTTP
  adapter is contract-tested offline, without spending API credits.

## Research / Experiments

[研究の現在地（日本語）](docs/research-status-ja.md) summarizes both completed
model comparisons, their evidence, and the unresolved research questions.

[Research objective, RQs and contributions](docs/research-question-and-contributions.md)
places the runtime as an auditable experimental foundation. The next analysis is
[stage-wise independent human review](experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan.md)
(design only; not yet conducted), before any new confirmatory experiment.

[Role Diversity vs. Epistemic Diversity](experiments/epistemic-diversity/README.md)
is an independent research application of this runtime: five controlled conditions,
30 versioned synthetic tasks across ten structural families, auditable context
separation, paired analysis and reproducible figures. The later Windows / Qwen3
HotpotQA study completed 30 questions across C0-C4, with 150 cases and 510 successful
model calls; see the [completion report](experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md).
Research code lives under `experiments/` and is not part of the runtime core; prior
campaigns and results are retained.

The follow-up study, [Synthesis Evidence Preservation](experiments/synthesis-evidence-preservation/README.md),
completed an 81-call fixed-worker comparison on Windows, including 24 questions
with source-excerpt and input-length controls. See the
[results and limitations](experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md).
Independent human review is pending; the overall research is not yet complete.

## Roadmap

Dynamic agent creation; richer planning and scheduling; distributed execution
with leases and idempotent effects; stronger evaluation datasets; simulation as
a typed workflow stage; UI/trace viewer. World models are intentionally absent
from v1. Future simulation should publish predicted-state artifacts through the
existing boundary rather than introducing a parallel control plane.

## Design documents

[Native Windows / NVIDIA / Ollama host preparation](docs/windows-nvidia-ollama.md)
provides non-generating preflight, hardware fingerprints and mock smoke tests.
It does not introduce a research condition or authorize a new pilot.

[Requirements](docs/requirements.md) · [Architecture](docs/architecture.md) ·
[Agent model](docs/agent-model.md) · [Information flow](docs/information-flow.md) ·
[Security](docs/security.md) · [ADRs](docs/design-decisions.md) ·
[Validation](docs/validation.md)
