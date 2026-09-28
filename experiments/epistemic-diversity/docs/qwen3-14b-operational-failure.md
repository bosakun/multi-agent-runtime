# Preserved qwen3:14b pilot — operational failure

Source: `runs/qwen3-14b/pilot/results.json`, its manifest, record, trace and
call journals; model binding is `runs/qwen3-14b/binding.json`.
These files, hardware/model/version notes and budget database are preserved
byte-for-byte. No retry, repair, deletion or relabeling is performed in this path.

Observed protocol: pilot-2.1 / benchmark 2.0.0, local Ollama at
`http://127.0.0.1:11434/v1/`, model `qwen3:14b`, temperature 0, output limit 2048,
worker concurrency 3, agent/client timeout 90 seconds.

| Item | Recorded value |
|---|---|
| Executed runs | 1 |
| Attempted model calls | 3 |
| Task / condition | v2-synthesis-easy / C2 |
| Runtime status | partial |
| Run latency | 90036.417 ms (approximately 90 seconds) |
| Agent failures | 2 × agent_timeout |
| Call journal errors | 2 × CancelledError |
| Final answer | None; no synthesizer call |

The provider records `CancelledError` when the runtime deadline cancels an
in-flight generation. Cancellation is an operational symptom, not a finding
about role or epistemic diversity. Concurrency/resource contention is a plausible
explanation, but the stored observations alone do not establish the cause.

Classify this cohort as **operational failure**, not a research outcome comparing
C2 and C3. The attempted record and calls remain visible; other planned cells
were unexecuted, and no paired condition comparison exists. The one failed record
is not converted to a successful sample or silently removed. Cost and missing
token usage must not be invented.

Protocol 2.2 is a prospective local execution adjustment, documented in
[protocol-2.2-amendment.md](protocol-2.2-amendment.md). Re-execution requires a new
content seal, new model binding and new campaign root. The protocol-2.1 source
can be recovered from commit `0b683cc`; its original content seal remains intact.
