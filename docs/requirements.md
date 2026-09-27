# v1 requirements and acceptance plan

This is a new, independent implementation. No previous project code, prompts,
documents, or proprietary architecture are inputs to this repository.

## Scope

Build a reusable Python runtime, two applications, and a controlled comparison.
The runtime owns scheduling, capabilities, state, structured communication,
durability, and traceability. Applications own schemas, policies, and workflows.
No agent framework, vector database, distributed workers, or simulation in v1.

## Acceptance map

| Requirement | Implementation boundary | Verification |
|---|---|---|
| Independent context, knowledge, memory | ContextBuilder with explicit allowlists and artifact ACLs | Sentinel leakage and snapshot mutation tests |
| Tool authority | Bound tool gateway, schema validation, per-call timeout | Unauthorized calls and timeout tests |
| Typed communication | Schema registry, validated results, routed artifact references | Invalid output, recipient and evidence validation |
| DAG scheduling | Validated nodes/edges/conditions, bounded concurrency | Parallel, branch, join, retry, partial failure |
| Human control | Persisted approval node, resume and cancellation | Restart/resume and cancellation tests |
| Replaceable models | ModelProvider protocol, mock and HTTP adapter | Offline E2E and HTTP transport tests |
| Durable execution | Repository protocol, SQLAlchemy SQLite/PostgreSQL | Transaction, version, replay, migration tests |
| Inspection | Safe metadata events, CLI and Mermaid | Flow and privacy assertions |
| Reuse | Investigation and software review apps | Both demos via API/CLI |
| Comparison | Single, shared experimental baseline, isolated | Deterministic fixtures and metric report |
| Quality | Ruff, mypy, pytest, README smoke commands | All checks before handoff |

Shared context is permitted only in the explicitly selected experimental baseline.
It never widens the isolated workflow's policy. Evaluation must not claim that
deterministic mock output demonstrates improved real-world model intelligence.

## Threat model

LLM output and documents are untrusted. Workflow definitions, Python tool
implementations, policy registration, and the operator are trusted. Capability
boundaries constrain information supplied to a provider and tools invoked by it;
they are not an OS sandbox against hostile Python plugins. API is a local operator
surface, not a public multi-tenant service. Persistent content can contain PII;
logs and event metadata must omit content. Deployment needs authentication,
encryption, retention controls, and vetted external providers.
