# Architecture decisions

1. [Custom runtime](adr/0001-custom-runtime-instead-of-framework.md): expose the mechanics.
2. [Structured communication](adr/0002-structured-agent-communication.md): explicit publications.
3. [Context isolation](adr/0003-context-isolation.md): code-enforced projection and capabilities.
4. [Event log](adr/0004-event-log.md): content-free metadata with atomic snapshots.
5. [Failure and human control](adr/0005-failure-and-human-control.md): bounded batches and durable approval.

Implementation follows the requirement phases: contracts and policies; DAG and
execution; storage and interfaces; two application compositions; baselines,
evaluation and adversarial tests. Architecture changes discovered during testing
are documented in [validation](validation.md), particularly SQLite connection
serialization and timestamp semantics for parallel events.
