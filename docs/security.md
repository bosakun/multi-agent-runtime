# Security boundary

## Trusted and untrusted components

Trusted: host process, installed Python extensions, schema/policy registration,
workflow definitions, operator, database. Untrusted: source documents, tool
results, model output and user-provided task content. A provider necessarily sees
the authorized context submitted to it; choose provider contracts appropriately.

An agent cannot request global state or choose memory namespaces through a model
response. Tool lookup is scoped before invocation. The demo AST scanner consumes
only submitted code text, with a size limit, and never executes it or accesses the
filesystem/network. Adding a file or network tool requires resource-level scope
validation inside that trusted handler, not just a tool-name allowlist.

Schemas reject unknown fields, enforce bounds, and validate messages/artifacts.
Malformed output has bounded retries. Request-validation API errors omit input
values. Transport errors retain only safe status codes. Hidden reasoning content
is never requested or copied into domain records. Application authors must not
add output fields that solicit private chain-of-thought.

## What is not guaranteed

Python object isolation is not process isolation. A hostile installed tool or
provider implementation can read process memory or environment variables.
Untrusted-data labels and prompts do not guarantee injection resistance; the
enforced boundary is which data and tool capabilities are available. Schema
validation does not stop false statements or semantic disclosure in allowed text.

The API is intentionally a local operator surface with no tenant authentication.
Results and persisted snapshots may include sensitive data. Before deployment,
add authentication, per-run authorization, TLS, secret-manager injection,
encrypted storage, a retention policy, request limits and reviewed tools. Use
one scheduler process per database workload in v1; CAS is not a work lease.

Model API keys are held only by the provider adapter. `.env` and SQLite files are
gitignored. The repository's example PostgreSQL credentials are local demo
credentials. Do not log raw request/response bodies from HTTP clients or custom
observers. `MockProvider(capture=True)` records contexts in memory only for tests
and evaluation; normal runtime construction disables it.
