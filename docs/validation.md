# v1 validation record

Date: 2026-09-27. Local: macOS ARM64, CPython 3.13.14, locked dependencies.
Container runtime: Python 3.12, PostgreSQL 17, non-root API process.

## Executed checks

| Check | Result |
|---|---|
| `uv sync --locked` | Passed |
| `uv run ruff format --check .` | Passed |
| `uv run ruff check .` | Passed |
| `uv run mypy` | Passed, strict mode, 44 application modules |
| Default offline pytest suite | 67 passed, 3 explicitly optional service tests skipped |
| Full suite with `TEST_POSTGRES_URL` and `TEST_API_URL` | **70 passed**, no skips |
| SQLite Alembic `upgrade head` and `check` | Passed in integration test |
| Docker build, PostgreSQL health, Alembic startup, API startup | Passed |
| Live HTTP execution of both demos, events and graph reads | Passed |
| README CLI run, inspect, Mermaid, content, historical revision | Passed |
| CLI approval, rejection and cancellation across processes | Passed |
| Three-mode evaluation for both applications | Passed |

OpenAI-compatible request/response contracts were tested using `httpx.MockTransport`.
No paid model API calls were made. GitHub Actions CI configuration is retained as
`docs/github-actions-ci-template.yml`; it is inactive because the GitHub OAuth
credential used for the initial push does not have the `workflow` scope. Remote
CI was not triggered from this workspace. Docker production images currently
install bounded dependencies from pyproject; local/CI use uv.lock.

## Definition of done evidence

| Acceptance condition | Evidence |
|---|---|
| 1: At least two parallel agents | Orchestrator test checks simultaneous active calls and overlapping timestamps |
| 2–4: Different contexts, no state handle, isolation tests | Security tests inspect exact provider requests and outputs |
| 5: Tool permissions | Gateway tests and software scanner E2E |
| 6: Structured communication | Closed Pydantic messages, recipient and artifact-owner validation |
| 7: Persisted execution history | Sequential events and atomic checkpoint tests |
| 8–9: DAG, branch/join/retry | Graph validation, conditional branch, partial join, retries |
| 10: Localized failure | Independent branch and partial-result tests |
| 11–12: Replaceable provider, offline E2E | ModelProvider protocol, both adapters, full offline demo matrix |
| 13: PostgreSQL and local storage | Same suite run against PostgreSQL and SQLite |
| 14–15: CLI and API | Subprocess CLI tests, ASGI contract tests, live HTTP tests |
| 16: Information flow | CLI trace and actual consumed-artifact Mermaid rendering |
| 17–18: Both demos | Investigation and software review via CLI and live API |
| 19: Single/shared/isolated comparison | Fixture-grounded evaluation and recorded results |
| 20: Third-party documentation | README, architecture, ADRs, security and extension guide |

## Design refinements discovered through testing

SQLite in-memory engines share a physical connection: overlapping logical
connections could roll back each other's transaction. The repository serializes
SQLite connection scopes; PostgreSQL retains independent transaction connections.
CAS and atomic snapshot/event writes are still applied in both backends.

Parallel traces commit in deterministic node order but record actual occurrence
timestamps. Cancellation retains completed and cancelled worker records with
usage known at the time of cancellation. Retrying does not reset tool authority.
The API rejects a duplicate in-flight submission of the same run, and database
revision checks independently reject stale checkpoint writers.

The full test suite verifies intended v1 semantics, not production readiness for
untrusted tenants or distributed workers. Deployment and replay limitations are
explicit in README and the security/architecture documents.
