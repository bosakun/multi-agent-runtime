# Extension guide

## New application

1. Define Pydantic input/output classes with `extra="forbid"`. Include uncertainty
   and evidence IDs where relevant.
2. Register schemas under stable names using SchemaRegistry.
3. Define each AgentDefinition with exact input/knowledge/memory selections,
   tool names, model settings, retries and publication recipients.
4. Construct WorkflowDefinition with Node/Edge/Condition data, or load JSON with
   `WorkflowDefinition.model_validate_json`. Unknown endpoints and cycles fail
   before execution. Predicates are field equality, never evaluated Python text.
5. Inject Repository, ContextBuilder, AgentExecutor and ToolRegistry into
   Orchestrator; call `create` followed by `execute`.
6. Add application fixture ground truth and information-flow tests before adding
   the workflow to the service catalog.

`join="all"` waits for all incoming dependencies to become terminal and requires
active branches to succeed. Inactive conditional branches are ignored.
`join="any"` also waits for all predecessors to become terminal, then runs if at
least one succeeds. `allow_failed_dependencies=True` explicitly permits a partial
all-join. It does not authorize extra context. No successful input means skip.

## Tool

Register a ToolDefinition with a description, Pydantic input/output types and an
async handler. Add its name only to authorized agents. The gateway checks the
name, argument schema, total call count and timeout and validates the returned
value. The provider sees descriptions only for allowed tools. Resource-specific
permissions belong in a scoped handler; do not expose unrestricted shell access.

## Provider and storage

Implement `ModelProvider.generate(ModelRequest) -> ModelResponse` without storing
hidden reasoning. ModelRequest includes only agent-local data. Failures should
raise RuntimeFault with a content-free stable code and an explicit retryable flag.
The HTTP adapter follows the official [structured output](https://developers.openai.com/api/docs/guides/structured-outputs)
and [function calling](https://developers.openai.com/api/docs/guides/function-calling)
contracts and still validates output locally. It supports Pydantic object schemas;
provider-specific strict-schema restrictions may require an alternative adapter.

Repository defines checkpoint/save/get/events/replay; MemoryStore defines scoped
read/write. SQLRepository implements both without exposing either to agents.
New stores must preserve atomic checkpoint semantics and stale-writer rejection.
Memory writes are trusted host operations, e.g. `write("long_term", agent_id,
"preference", value)`; reading still requires that agent's key allowlist.

## Simulation later

A future simulator can consume typed proposal artifacts and publish predicted
state artifacts for a reevaluation node. The runtime does not need a World Model
class until an application exercises this boundary. Distributed scheduling will
need leases and effect idempotency beyond the current optimistic revisions.
