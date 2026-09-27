# ADR 0005: Bounded scheduling and explicit human checkpoints

Status: accepted.

Use bounded parallel batches with deterministic commits. Failures propagate only
through dependent nodes; joins may explicitly accept partial inputs. Approval is
a persistent node state with explicit approve/reject decisions, not an in-memory
callback. Resume pins workflow definitions. Batch scheduling favors reproducible
traces over maximum throughput. Exactly-once external effects are not claimed.
