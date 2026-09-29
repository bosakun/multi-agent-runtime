# Representative Qwen3 generation-budget diagnostic — actual results

Executed 2026-09-29 JST after the user's authorization to improve operational
problems and reach Pilot completion. This is an engineering reproduction, not a
C2/C3 performance comparison. Historical campaigns remain immutable.

The plan/source/input binding was fixed before three real calls. All used
qwen3:14b, Ollama 0.34.4, temperature 0, default thinking, serial execution,
no tools/retries, 1200-second deadline. Original agent-only requests were read
from preserved journals; no gold/global context was reconstructed.

| Cell | Input | Generation limit | Reported generation | Final-content chars | Status | Seconds |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | Exact failed worker request | 2048 | 2048 | 0 | length termination | 164.64 |
| 2 | Same worker request | 4096 | 2430 | 980 | schema-valid / stop | 224.70 |
| 3 | Near-limit synthesizer request | 4096 | 2033 | 553 | schema-valid / stop | 225.04 |

For the paired worker requests the actual HTTP bodies matched except `max_tokens`.
Cell 1 returned 9,788 reasoning characters and zero final-content characters;
only counts, **not reasoning text**, were persisted. Thus in this reproduction,
generation ended before a final JSON answer was emitted. This is stronger
diagnostic evidence than the earlier lightweight synthetic success.

Cell 2 completed with 2430 generated tokens, exceeding the previous 2048 ceiling.
Increasing the generation allowance permitted this input to finish, under the
unchanged thinking/temperature/prompt settings. This does not recover the lost
original response or prove that every benchmark input will fit 4096.
Reasoning-token counts are not reported; character counts must not be interpreted
as exact token allocation. Latency is observational, not a controlled speed benchmark.

Both 4096 candidate cells passed the predeclared gate. A new Protocol 2.4 cohort
was therefore sealed with a common 4096 limit and 1200-second deadline. Its
scientific outcomes remain separate. Diagnostic costs: **3 calls**, retained
including the baseline failure. Shared campaign counter has 48 further planned
Pilot calls, within the hard ceiling 60. No additional model probes were made.

Artifacts:

- `runs/qwen3-14b-recovery-v2/binding.json`
- `runs/qwen3-14b-recovery-v2/diagnostic/results.json`
- `runs/qwen3-14b-recovery-v2/diagnostic/cell-01/response.json`
- `runs/qwen3-14b-recovery-v2/diagnostic/cell-02/response.json`
- `runs/qwen3-14b-recovery-v2/diagnostic/cell-03/response.json`
- `runs/qwen3-14b-recovery-v2/diagnostic/backend.json`

The prefix observer retained explicit final JSON where available; it did not
manufacture content for cell 1. The recorded observation's generic wording
"allocation cause unknown" remains unedited; the direct zero-final-content /
nonzero-reasoning observation above is what was measured in this reproduction.
