# Agent model

An AgentDefinition is a serializable policy bundle, not a conversational persona.
It has its own registered input/output schemas, model selection and pricing,
context allowlists, tool authority, maximum attempts, timeout, model-turn budget
and publication recipients. A run pins copies of these definitions and its DAG.

| Value | Owner | Purpose |
|---|---|---|
| WorkflowInput / WorkflowState | Orchestrator | Input, scheduling and committed results |
| AgentDefinition | Application author | Authority and execution configuration |
| AgentContext | ContextBuilder → executor | Detached projection of authorized information |
| AgentResult | Executor | Validated output, uncertainty, safe error and total usage |
| AgentRun | Orchestrator | Node execution record spanning bounded retries |
| Artifact | Publisher / router | Immutable version of a named structured output |
| MessageEnvelope | Router | Explicit sender, recipients and artifact-version references |
| Run | Repository | Definition snapshot, state and concurrency revision |
| Event | Orchestrator | Metadata-only audit record |

The executor validates the agent-specific input dictionary, builds a ModelRequest
from the authorized context, runs a bounded model/tool loop, validates the output
schema, and checks every nested `evidence_ids` field against visible provenance.
Evidence scope verification does not establish factual truth; the evaluator uses
independent fixture ground truth. Software findings can cite input-based concerns
without evidence-document IDs and explicitly include uncertainty.

Retries apply to transient transport failures, timeouts and malformed structured
outputs. Policy denials, invalid tool arguments, unsupported evidence references
and tool failures are permanent. Tool-call budget spans retries to prevent retry
loops from silently multiplying authority. External tool effects must be
idempotent; handlers that block the Python event loop cannot be forcibly preempted.

AgentRun stores aggregate usage across attempts and events record individual
attempts. Cancellation retains attempted-call counts; providers cannot report
tokens billed after a connection is lost. Model costs use configured rates.

Private memory namespace is `run_id:agent_id`; shared memory namespace is run ID
and reads use explicit key allowlists; long-term namespace is agent ID. Across
runs only long-term memory persists semantically. The database also retains old
private memory for audit until an operator's retention policy removes it.
