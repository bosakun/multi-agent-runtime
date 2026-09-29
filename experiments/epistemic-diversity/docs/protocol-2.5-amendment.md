# Protocol 2.5: prospective context-scoped evidence-ID contract on Windows

Authorized 2026-09-29 JST before new generation: the user requested real experiments
and selected option 1, improving evidence-ID output constraints before a fresh Pilot.
This plan and its source seal precede all Protocol 2.5 real model calls.

## Declared change and scope

Protocol 2.4 stopped after 4 attempted runs / 15 Pilot calls when C3 worker_1
cited `none`, outside its context. That failure remains a failure. No old
campaign, binding, freeze, prompt, schema, task or result is rewritten or resumed.

In this new cohort, every nested `evidence_ids` output-array item is constrained
to the sorted IDs from that exact request's `AgentContext.evidence_scope()`.
Workers receive only their visible knowledge IDs. The artifact-only synthesizer
receives only evidence IDs already released through authorized worker artifacts.
No global evidence inventory, hidden gold, withheld partition, or new evidence
is provided. When the scope is empty, `maxItems=0` permits only an empty array;
no invented placeholder such as `none` is allowed. Empty citations remain allowed
for uncertain/unsupported statements, as in the original schema.

The same projection applies to C2 and C3, including workers and synthesizers.
It changes the structured-output contract and therefore is a new research protocol,
not a retrospective repair or a claim of equivalent historical measurements.
The runtime's original recursive citation validation remains active. Backend
noncompliance still stops execution; outputs are never repaired, trimmed, retried,
or replaced. Correct citation membership does not establish evidential support,
answer correctness, or superiority of either condition.

## Fixed controls and separate host

- Benchmark / metrics 2.0.0, original six Pilot task IDs, seed 20260928,
  C2/C3 only, one repetition, fixed condition ordering: 12 runs / 48 calls.
- Model `qwen3:14b`, Ollama 0.34.4, manifest digest
  `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
- Original Protocol 2.4 controls: temperature 0, `max_tokens=4096`, 1200s per-agent
  / HTTP deadline, default thinking with no override, no tools, worker/model
  concurrency 1/1. Prompts, roles, evidence partitions, task order and metrics unchanged.
- Native Windows / RTX 4070 SUPER is the host for this separately labelled cohort.
  Host/backend observations are bound before launch and observed again before dispatch.
  Server is launched with parallel=1 and max_loaded_models=1; no implicit tray-server
  substitution is accepted as evidence of those settings.

## Fresh storage, seal and gates

Campaign: `runs/qwen3-14b-protocol25-windows`. Freeze:
`freezes/benchmark-2.0.0-protocol-2.5.json`. Independent hard budget 60, fresh zero
starting count, 48 planned real calls, no added diagnostics or automatic repeats.
The consumed recovery-v2 budget and its unavailable local records are not reused.
Committed historical incident/gate summaries provide background, not a new gate.

Before new generation: verify original sealed content, execute new contract unit/
fake-HTTP regressions including fail-stop and wire/journal matching, complete the
full 48-call Mock grid, verify preservation, and pass native non-generating host
preflight. The new seal binds historical source, extension source, tests, this plan,
and the successful Mock result hash. The model binding records backend version,
full model digest, Windows host and fixed controls. Any drift blocks launch.

The historical verifier uses platform-dependent `str(relative_path)` keys. The
new verification layer normalizes path separators solely for comparison, while
retaining original file hashes and validating the original signature. It neither
edits nor regenerates an old freeze. Content or inventory differences still fail.
New SQLite budget connections are explicitly closed; reservation semantics and
failures-count-as-used policy remain unchanged. This host resource correction is
included in the new source seal and does not retrofit historical budget modules.

## Failure and analysis rules

Stop at the first case with runtime/schema/transport/boundary failure. Preserve
attempts, reserved calls, guarded HTTP observations and partial records. No resume,
extra cohort, task replacement, relaxed validation, JSON repair or hidden reasoning
capture. Incorrect but valid answers are retained research outcomes.

Only after exactly 12 successful records / 48 calls, no errors and zero recorded
context/result/gold leaks: analyze this cohort alone, generate human review and
figures in new Protocol 2.5-specific directories. A single six-task Pilot is not
evidence of general superiority. Main/full and extra repetitions are not enabled.

## Windows commands (dedicated research PowerShell)

Configure PATH for the existing Ollama installation and `.venv/Scripts`, then
dot-source `scripts/windows/env-research.ps1` only in the research process.
Do not use its local compatibility key for Codex authentication.

```powershell
uv run --frozen python -X utf8 experiments/epistemic-diversity/pilot25.py historical
uv run --frozen python -X utf8 -m pytest -q experiments/epistemic-diversity/tests/test_pilot25.py
uv run --frozen python -X utf8 experiments/epistemic-diversity/pilot25.py mock
uv run --frozen python -X utf8 experiments/epistemic-diversity/pilot25.py prepare
uv run --frozen python -X utf8 experiments/epistemic-diversity/pilot25.py verify
uv run --frozen python -X utf8 experiments/epistemic-diversity/pilot25.py run --approve-real
```

This file records the prospective plan, not a claim that any real call succeeded.
