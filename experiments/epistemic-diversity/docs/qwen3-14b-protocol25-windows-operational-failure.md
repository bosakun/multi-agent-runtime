# Protocol 2.5 Windows real Pilot: citation contract applied, generation truncated

Recorded 2026-09-29 JST. The new real Pilot actually ran from 18:05:04 to
18:22:48 JST (about 17m44s) and stopped according to its prospective fail-stop
rule. This is an incomplete feasibility cohort, not a C2/C3 performance result.

## Execution and outcome

- Protocol `pilot-2.5`, benchmark/metrics 2.0.0, original six fixed tasks,
  C2/C3, seed 20260928, one repetition, `qwen3:14b` / Ollama 0.34.4.
- Temperature 0, default thinking, `max_tokens=4096`, 1200s deadline,
  worker/model concurrency 1/1, no tools, retry, repair or resume.
- Every request's nested evidence-ID arrays used only its AgentContext scope,
  with the effective schema captured in its journal and checked before HTTP dispatch.
- Nine runs succeeded. The tenth attempted run, `v2-missing-easy / C3`, was
  partial after `worker_1` failed with `provider_output_truncated` / `RuntimeFault`.
  Its other two workers succeeded; the synthesizer was not dispatched.
- 39 real calls were consumed from the fresh independent ceiling of 60.
  Both `v2-causal-hard` conditions remain unexecuted. The expected full grid was
  12 runs / 48 calls; operational integrity is false. The remaining budget is not
  permission to resume or start another cohort.
- Recorded context/result/gold leakage counts are all zero in all ten attempted
  run records. No `unknown_evidence_reference` occurred in this cohort. These
  observations do not establish universal citation reliability or causal attribution.

The former Protocol 2.4 failing `v2-diagnosis-medium / C3` case succeeded here.
The host and structured-output contract differ from that historical cohort;
do not infer a single causal fix or pool the cohorts.

## Direct evidence for the new failure

Failed run ID: `6b87dcb146b44eae9562128790d86ebb`.

| Agent | HTTP finish | Input tokens | Generated tokens | Call latency |
|---|---|---:|---:|---:|
| worker_0 | stop | 589 | 1303 | 28.20s |
| worker_1 | length | 591 | 4096 | 88.84s |
| worker_2 | stop | 648 | 1233 | 26.59s |

The failed HTTP response reported 4687 total tokens and no final-answer content
(`final_content_characters=0`, `answer_capture=no_content`). A separated reasoning
field had 20,805 characters; only its length was retained, never its text. The
backend did not report a reasoning token count, so that count remains null.
Do not convert characters to tokens or subtract different units to infer allocation.
The direct failure is generation-length termination, not a 1200s timeout.
Its exact allocation and cause are not established by these observations.

All 39 HTTP observations are preserved: 38 `stop`, one `length`. Provider-reported
operational totals including the failed call: 45,606 input + 45,116 generated =
90,722 total tokens. Run-level successful-response usage may omit failed-call usage;
the HTTP totals above must be labelled separately.

## Host observation

Windows 11 / i7-14700F / approximately 32 GiB RAM / RTX 4070 SUPER / driver
591.86 / VRAM 12282 MiB. Ollama recognized CUDA compute capability 8.9.
During execution, `ollama ps` reported `100% GPU`, and `/api/ps` reported
`size=size_vram=9646353939`, active context length 4096. These are offload/memory
observations, not 100% compute utilization or a throughput benchmark.

Dedicated report:
`reports/windows-host/inspect-20260929T090603Z-e96d215c3f614222a66a01bb6f688dab.json`.

## Validation and immutable provenance

- New contract/fake HTTP tests passed; full selected Runtime/Windows/new-protocol
  regression: 144 passed, 2 skipped. Live API tests were explicitly excluded.
  Skips: external PostgreSQL and undistributed implementation-local preservation baseline.
- Ruff formatting/lint and mypy passed for all six new source files.
- Full new Mock Pilot: 12 runs / 48 calls, all succeeded with zero recorded leaks.
- Original Protocol 2.3 signature/content verified with portable path normalization;
  the old verifier/source/freeze were not rewritten.
- Before launch, all 416 existing protected checkout files retained their SHA256.
  Baseline and prelaunch reports are under `reports/protocol25-preservation-*.json`.
- No commit, stage or push was performed. New additive source files remain local.

New freeze: `freezes/benchmark-2.0.0-protocol-2.5.json`, signed content hash
`729943054b541e9a398354f60d7d02847a3609cc901b6ab44fc60b6d8973a8f6`.
Binding signature:
`4a1ae07bd09e9021a76bf7401ff7568c2e6ec7c6e9db44cf5a651018c2b8daf1`.
Model manifest digest:
`bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.

Campaign (Git-ignored): `runs/qwen3-14b-protocol25-windows/` contains binding,
budget.sqlite, Pilot results, runtime SQLite, records, traces, call journals,
HTTP observations and partial human review. Results file SHA256:
`f8babe745d711e3cce00be9d38d3fffda738d5f951b320c1d1be8b7034adf776`.

No performance analysis or figures were generated. Do not repair the failed
response, edit the sealed plan/source, reuse this binding, resume the remaining
cases or silently change thinking/token/context controls. A subsequent engineering
reproduction needs its own prospective scope/budget and fresh artifacts; another
research attempt needs a new reviewed protocol, freeze, binding and campaign.
