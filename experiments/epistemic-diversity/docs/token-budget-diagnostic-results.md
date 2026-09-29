# Qwen3 token-budget diagnostic v1 — actual real-model results

Executed 2026-09-29 JST under **「実モデル実行まで」** authorization. This is the
predeclared six-cell synthetic operational diagnostic, not a Protocol 2.4,
research Pilot, retry/resume or C2/C3 performance comparison.

## Operational integrity

- Executed / planned / durable consumed budget: **6 / 6 / 6 calls**.
- Six journals and six metadata sidecars; every record completed with
  schema_valid=true, error=null and finish_reason=stop. Stopped_reason=null.
- No truncation, timeout, transport/schema failure or additional generation.
- All three paired wire hashes match after excluding only max_tokens.
  The exact ceiling order was 4096, 2048, 2048, 4096, 2048, 4096.
- Thinking default, temperature 0, deadlines 600s, concurrency 1, no tools,
  backend seed, retries or continuations remained unchanged.
- Model qwen3:14b; Ollama **0.34.4**; GGUF / Q4_K_M / 14.8B; arm64 macOS.
  Recorded digest: `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
- UTC start `2026-09-28T18:56:20.657506+00:00`, finish
  `2026-09-28T19:00:12.374885+00:00` (JST 03:56:20–04:00:12).
  Wall-clock duration **231.72s / about 3m52s**, including preflight/recording.

## All six cells, no exclusions

| Cell | Synthetic fixture | Limit | Input tokens | Generated tokens | Thinking chars | Final chars | Latency s |
|---|---|---:|---:|---:|---:|---:|---:|
| 01 | diag-direct | 4096 | 365 | 426 | 1279 | 549 | 34.77 |
| 02 | diag-direct | 2048 | 365 | 426 | 1279 | 549 | 32.30 |
| 03 | diag-partial | 2048 | 425 | 422 | 1188 | 560 | 32.80 |
| 04 | diag-partial | 4096 | 425 | 422 | 1188 | 560 | 32.44 |
| 05 | diag-artifacts | 2048 | 768 | 472 | 1628 | 530 | 48.61 |
| 06 | diag-artifacts | 4096 | 768 | 472 | 1628 | 530 | 50.75 |

Both ceilings completed **3/3** schema-valid responses. All generated counts
are far below 2048; the higher ceiling was not binding either. Nonempty Thinking
fields were observed but their reasoning-token counts were not reported and
remain **null**. Character counts are not token counts. Equal lengths/counts
do not prove equal text or answer semantics; no final text or hidden reasoning
was persisted. No correctness or research-metric evaluation was performed.

| Ceiling | Calls | Input tokens | Generated tokens | Total reported tokens | Sum of latency s |
|---|---:|---:|---:|---:|---:|
| 2048 | 3 | 1558 | 1320 | 2878 | 113.71 |
| 4096 | 3 | 1558 | 1320 | 2878 | 117.96 |
| Combined | 6 | 3116 | 2640 | 5756 | 231.67 |

Usage is known for all six calls. No cost estimate is invented without verified
prices or electricity measurements. Minor latency differences cannot be separated
from cache/warm-up/thermal/background variation with this small diagnostic.

## Predeclared interpretation

**The earlier truncation was not reproduced.** Both ceilings completed on all
three inputs, so doubling the budget is not demonstrated to fix the stopped
research campaign. The predeclared criterion requiring a 2048 length failure
and three successful 4096 cells was **not met**. No automatic adoption follows.

Demonstrated: exactly six controlled provider calls, explicit max_tokens,
default Thinking metadata and schema completion, with auditable non-text logs.

Not demonstrated: failed Protocol 2.3 call 0017's cause, reliability on harder
benchmark tasks, a sufficient generation ceiling, exact reasoning/final-token
allocation, answer quality or superiority of either multi-agent condition.
Three observations per ceiling cannot justify significance or reliability claims.

The synthetic inputs were fixed before outputs and not selected from the failed
case. That protects integrity but their low generation demand limits failure
reproduction. No harder input, added repetition, extra ceiling or Pilot was added.
A more demanding independently predeclared diagnostic may be proposed next;
it requires a new plan and approval. No new research protocol or Pilot is launched.

## Preservation and validation

All **228 protected files** retain their pre-execution raw-byte SHA256, including
Protocol 2.1/2.2/2.3 campaigns, benchmark 2.0.0, prompts, scientific source,
bindings and original freezes. Protocol 2.3 freeze still verifies:
`fb661f49dd4b98276ae1594ded53b3aca53ac92b91d01e6b9d26a5913872e361`.
Independent diagnostic seal verifies:
`d1d115063ae1684def31ca8fc3e4475d75980628f8af9f465e8ad2b00a942fec`.
No sealed source/plan/authorization or new binding changed after launch.

Runtime/research suite: **225 passed / 3 optional external-service skips**;
formatter/lint and both strict type checks pass. Fake HTTP tests covered budget,
wire invariants, expected truncation and other fail-stop paths. Original app/
and sealed research src/ were not edited for this diagnostic.

## Preserved artifacts

Under `runs/qwen3-14b-token-budget-diag-v1/`:

- results.json: all six outcomes, timings, usage, git/source/seal identity.
- binding.json: immutable diagnostic binding and authorization.
- backend.json: backend/model/hardware metadata, from non-generation requests.
- budget.sqlite: six durably consumed calls.
- call-journal/cell-01.json through cell-06.json: reservations/outcomes.
- metadata/cell-01/ through cell-06/: observed non-text response metadata.

Independent seal: `diagnostics/token-budget-v1/seal.json`.
Entry point: token_budget.py; original plan/input files remain unchanged.
`token_budget.py verify` is read-only. **Do not repeat prepare/run** on this
consumed campaign; there is no resume. No analysis/figures for failed Protocol 2.3
were executed. Nothing was committed or pushed by this task.
