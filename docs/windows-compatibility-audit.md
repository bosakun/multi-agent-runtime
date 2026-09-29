# Windows execution support — compatibility and preservation audit

## Scope and invariants

Baseline HEAD: `0200e027e09fd36bd5db659ceb6bd233b678cb1a`, branch
`research/epistemic-diversity`. Original untracked `.DS_Store`,
`experiments/.DS_Store`, and `results/protocol24-mock-validation/budget.sqlite` retained.
No scientific code, prompts, config, task/gold, policy, schema, metric or Protocol edits.
No real model generation. Initial implementation stopped before commit/push;
publication of these host-only changes was subsequently authorized separately.
Host preparation is not a new scientific condition.

## Cross-platform review

| Area | Observation / action |
|---|---|
| OS / commands | New host uses platform, shutil.which, argv-only subprocess, 10s command deadline; no shell=True or bash. Windows CIM via fixed PowerShell script, UTF-8 output. No uname/which shell commands. |
| GPU | Parse nvidia-smi XML; all adapters, missing/malformed/unknown observations tested. No nvcc/runtime claims based on driver-supported CUDA. |
| API | Reuse frozen diagnostic preflight, observe its responses, add nongenerating models/residency endpoints. No model load, pull, warmup, generation or option changes. |
| Server process | Query process names/PIDs and bind-test loopback sockets; fail closed if unknown. Never kill. Foreground child inherits parallel=1/max_loaded=1. Bind race remains possible and is not retried. |
| Paths / names | pathlib; tempfile instead of /tmp; timestamp filenames omit colon. Existing run IDs are hex, not timestamp-with-colon filenames. SQLite URL for smoke uses forward-slash absolute path, including Windows drive. |
| Line endings | New .gitattributes preserves LF for byte-sealed text. Existing files are not renormalized. Fresh Windows checkout must verify seals. |
| Encoding | Frozen read_text/write_text often omit encoding. New PowerShell commands use python -X utf8 / PYTHONUTF8=1; no frozen source edits. New native commands/reports explicitly use UTF-8. |
| Signals / chmod | No platform-specific signal/kill/chmod needed in runtime production path. Startup does not manage termination; original terminal owner controls server shutdown. |
| results / trace / journal | Existing research write_json closes sibling .tmp before replace. Windows replace can still fail if another process holds a non-sharing handle. No retries or weakening of refusal rules added. |
| HTTP observations / bindings / freezes | Existing exclusive UTF-8 writes retained; diagnostics use UUID sibling temporary files closed before replace. No historical re-publication. |
| New fingerprint reports | Dedicated reports/windows-host; UTF-8 + fsync + close before atomic no-clobber hard link. Existing destinations and scientific paths refused. Unsupported FS/locked publication stops; no silent fallback. |
| SQLite Runtime | SQLRepository owns engine, serializes updates, explicitly disposes on close. Mock smoke tests workflow completion then closed-handle DB rename/removal. |
| SQLite research budget | Frozen CallBudget uses sqlite3 connection context managers, which commit/rollback but do not explicitly close. GC/process lifetime may hold handles, especially after errors. No change to this sealed module; old DBs never opened by host commands. Before future formal Windows campaigns, validate lifecycle on native Windows / consider a separately authorized generic explicit-close correction with new source sealing. Current host smoke does not claim to certify this research budget lifecycle. |
| File watchers / network FS | NTFS local checkout recommended. Antivirus/indexers/readers may block rename. Existing scientific writer is not claimed immune. No output regeneration to work around locks. |

No app/ changes were necessary for host-only execution support. Adding host files outside the sealed
source inventory avoids invalidating old protocols. Existing metadata collection is reused, not forked.
NVIDIA parsing is an extension for the previously unobserved Windows host, not a second research runner.

## Research boundary TODO (not implemented)

Protocol 2.4 correctly rejected `evidence_id="none"` as `unknown_evidence_reference`.
Future design may project allowed AgentContext evidence IDs into an output-schema enum.
That requires separate design and authorization; no dynamic enum, fuzzy match, ID deletion,
repair, retry, or prompt alteration is present in this host addition.

## Preservation procedure

Before implementation, SHA256 was captured for **3,084 existing protected files**:
all existing experiment files (including Protocol 2.1–2.4 campaigns, diagnostics, freezes,
benchmark/public/gold/audits, historical prompts/configs), app/, demos/, pyproject.toml,
uv.lock and original local .DS_Store files. Generated Python/tool caches excluded.

Baseline: `reports/windows-support-preservation-before.json`.
Final comparison: `reports/windows-support-preservation-after.json`.
New files are explicitly outside the comparison. Reports are local ignored artifacts.

```powershell
uv run python -X utf8 scripts/audit_preservation.py verify --baseline reports/windows-support-preservation-before.json --output reports/windows-support-preservation-after.json
uv run python -X utf8 experiments/epistemic-diversity/run.py verify-freeze
uv run python -X utf8 experiments/epistemic-diversity/token_budget.py verify
uv run python -X utf8 experiments/epistemic-diversity/recovery_live.py verify
uv run python -X utf8 experiments/epistemic-diversity/pilot24.py verify
```

Do not overwrite an existing audit result; use a new report filename for another comparison.
On a different PC, copy the original baseline for comparison or take a separately labelled host
baseline before changes; do not pretend a later snapshot is the implementation baseline.

## Validation commands

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy
$env:MYPYPATH = 'experiments/epistemic-diversity;experiments/epistemic-diversity/src'
uv run mypy experiments/epistemic-diversity/host_support experiments/epistemic-diversity/host.py scripts/audit_preservation.py
uv run mypy experiments/epistemic-diversity/src experiments/epistemic-diversity/run.py experiments/epistemic-diversity/operational_diagnostics
uv run python -X utf8 -m pytest -q tests experiments/epistemic-diversity/tests
```

PowerShell startup script contracts are statically tested here. Native PowerShell execution and
actual Windows file sharing semantics still need the above host smoke on the target PC.
No Windows performance numbers or real hardware values are fabricated.

### Executed validation (2026-09-29, macOS host)

| Check | Result |
|---|---|
| Existing Runtime tests (excluding new Windows tests) | 68 passed, 3 skipped |
| Existing research tests | 184 passed |
| New Windows mocked/unit tests | 66 passed |
| Combined regression | 318 passed, 3 skipped |
| Ruff formatter | 192 Python files already formatted |
| Ruff lint | Passed |
| Runtime mypy | 44 source files passed |
| Research / diagnostic / host / preservation-script mypy | 33 source files passed |
| Mock host smoke | succeeded, 6 mock calls, 0 real generation calls; SQLite close/rename/remove passed |
| SHA256 preservation | 3,084 / 3,084 original files unchanged; no missing files |
| Native Windows / PowerShell / RTX hardware | Not executed; target-machine validation pending |

Verification outputs (existing seals were not regenerated):

```text
run.py verify-freeze
fb661f49dd4b98276ae1594ded53b3aca53ac92b91d01e6b9d26a5913872e361
token_budget.py verify
d1d115063ae1684def31ca8fc3e4475d75980628f8af9f465e8ad2b00a942fec
recovery_live.py verify
065a6fae3b94f87810a6e96017f70a4be9fd6fa5c6634a080a1c5b184e2f47a7
pilot24.py verify
14e0d06d889a315bc8f3509b1c26d4a9a46f63159c76ff40243c51b2b4671a52
```

The three existing Runtime skips are environment-gated tests, not failed Windows checks.
All protocol cohorts, diagnostic records and Benchmark 2.0.0 are preserved by per-file comparison;
historical protocol seals are retained, not promoted to the current protocol.
