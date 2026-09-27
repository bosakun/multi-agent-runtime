# Information flow and publication

The entire WorkflowState is private to runtime infrastructure. ContextBuilder
selects task/input keys, assigned knowledge IDs, intersecting artifact producer
and reader policies, recipient messages and namespaced memory keys. A serialized
round-trip severs mutable aliases before the executor receives the context.

Knowledge documents carry the literal `trust="untrusted_data"`. Providers encode
documents within a user-data message, separate from the trusted system instruction.
Structured agent output is also untrusted: schema and provenance checks happen
before publication. No model-provided instruction changes policy or scheduling.

| Stage | Raw knowledge | Structured publications |
|---|---|---|
| Investigator A | evidence_a | None |
| Investigator B | evidence_b | None |
| Investigator C | evidence_c | None |
| Reviewer | None | Investigator findings |
| Conflict Detector | None | Reviewed findings |
| Synthesizer | None | Findings and conflict report |

Each publication is an intentional release to named readers. Before an artifact
can be routed, the sender must own it, each recipient must exist in the run, the
sender must allow that recipient, the artifact ACL must include it, and the
recipient policy must select the sender. Message content consists of references;
it cannot smuggle an extra `raw_context` field through a permissive dictionary.

Secret-canary tests check provider requests and investigator results. They also
verify that explicit publication permits downstream readers to see the released
finding. This distinction matters: isolation does not mean agents can never
share information; it means sharing has an auditable boundary.

`inspect` renders categories and actual artifact consumption. Mermaid adds DAG
dependency edges, context category nodes, versioned artifact nodes and recipient
consumption edges. The event log includes message routes and tool names but not
tool arguments/results, documents, raw contexts, API keys or private memories.

Event sequence is deterministic commit order. Worker timestamps record occurrence
time and may be out of sequence across parallel agents. An interrupted uncommitted
batch can lose its detailed trace; the durable `AGENT_SCHEDULED` checkpoint
identifies nodes requiring recovery. Snapshot revision, not model nondeterminism,
is the unit of historical replay.
