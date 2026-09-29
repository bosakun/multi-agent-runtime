# Token-budget diagnostic v1 — implementation and launch authorization

Prepared 2026-09-29 JST **before diagnostic generation**. The user explicitly
approved implementation through real execution: **「実モデル実行まで」**.
That approval covers only the previously declared six synthetic cells, not a
scientific pilot, Protocol 2.4, additional ceiling, repetition, retry or resume.

The earlier plan.json and diagnostic-plan document retain their original
planning-time status and exact inputs/order. This document records the subsequent
authorization without rewriting that prospective plan. All generation controls,
budgets, interpretation criteria and stopping rules remain as predeclared.

## Implemented isolation and safety

`token_budget.py` and `operational_diagnostics/budget_experiment.py` implement
an independent provider-level diagnostic, not an end-to-end Runtime performance
test. The original app/ and sealed research src/ are unchanged. There is no
relaxation of local-Pilot ModelSettings and no use of old research bindings.

The independent seal includes the original research's sealed files for integrity
checking, the new harness/entry point, metadata observer, this authorization,
and the predeclared plan and fixtures. Benchmark bytes are only hashed for
preservation; benchmark/gold tasks are not loaded into diagnostic requests.
The fixture contexts, neutral/synthesizer prompts and schemas are unchanged.
Fixed context run IDs/timestamps ensure paired wire bodies differ only in
max_tokens; actual wire hashes are checked before transport. Cell identity and
authorization remain out of band.

Serial calls use 600s outer/HTTP deadlines. A durable SQLite reservation precedes
each dispatch. The immutable six-call cap cannot be expanded via environment
variables; lower budgets refuse before generation. No retry/resume CLI exists.
Existing phases, historical roots/children, seals and bindings cannot be reused.

Response metadata is saved before provider rejection. The observer's syntactic
JSON-object check is metadata only: a length-terminated response is never used
as an agent output, schema-validated, repaired or salvaged. A length outcome
continues the preplanned grid; all other operational failures stop. Unknown
failed usage remains null. Request/response bodies, hidden reasoning, secret
headers and exception messages are not written to journals or printed.

Before generation, three non-generation metadata requests retrieve backend
version, model digest/details and capabilities. They do not consume model-call
budget or warm up generation. Preflight failure produces a retained zero-call
report with all six cells unexecuted; there is no automatic launch retry.

## Validation completed before launch

Runtime + research suite: **225 passed / 3 optional external-service skips**,
including 13 new fake-HTTP runner tests. Formatter/lint and both strict type
checks pass. The original Protocol 2.3 freeze is still valid. Fake transport
tests cover six serial cells, byte-identical paired requests except max_tokens,
metadata-only persistence, expected length outcomes, other faults stopping,
budget refusal, seal/binding mismatch and campaign reuse rejection.
These are software tests, not results from Qwen3.

## Authorized commands

From repository root, using the already installed locked environment:

```bash
.venv/bin/python experiments/epistemic-diversity/token_budget.py prepare
.venv/bin/python experiments/epistemic-diversity/token_budget.py verify
OPENAI_API_KEY=ollama MODEL_NAME=qwen3:14b \
  MODEL_BASE_URL=http://127.0.0.1:11434/v1/ MAX_MODEL_CALLS=6 \
  .venv/bin/python experiments/epistemic-diversity/token_budget.py run --approve-real
```

`prepare` is single-use and must never be repeated on existing artifacts.
`verify` is read-only and remains usable after execution. The `run` command is
single-launch and refuses a consumed campaign, regardless of success/failure.

Independent seal: `diagnostics/token-budget-v1/seal.json`.
Campaign/binding: `runs/qwen3-14b-token-budget-diag-v1/binding.json`.
Outputs at that same fresh root: `results.json`, `backend.json`, `budget.sqlite`,
`call-journal/`, `metadata/`. Original research campaigns remain untouched.
Known usage totals must identify missing measurements; costs are not fabricated.

## After execution

Report every planned cell, including unexecuted ones; finish reason, reported
tokens, reasoning/final character counts, schema validity, latency and stop reason.
Apply only the predeclared descriptive decision rules. A six-cell success does
not prove benchmark completion or authorize another research Pilot. No analysis
of C2/C3, old cohort pooling, extra calls, new protocol, main/full or push follows.
