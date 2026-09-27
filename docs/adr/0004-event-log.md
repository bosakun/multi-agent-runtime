# ADR 0004: Atomic metadata events and content snapshots

Status: accepted.

Persist ordered metadata events together with state snapshots and projections in
one database transaction, using optimistic revision checks. This supports audit,
historical inspection and crash recovery without placing raw prompts or private
memory in logs. Snapshot replay is supported; event-only reconstruction is not.
Sensitive snapshots require operator-controlled storage and retention. External
calls cannot share the database transaction, so recovery is at-least-once.
