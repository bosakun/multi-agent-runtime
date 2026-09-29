# Preserved qwen3:14b protocol-2.2 pilot — operational failure

Observed 2026-09-29 JST (UTC timestamps 2026-09-28 15:29:36–16:00:22).
Source: `runs/qwen3-14b-protocol22/pilot/results.json`, four traces/records,
16 call journals, immutable binding and campaign budget. These files remain
unaltered; this separate document does not rewrite any failure artifact.

| Item | Recorded value |
|---|---|
| Protocol / benchmark | pilot-2.2 / 2.0.0 |
| Model / endpoint | qwen3:14b / http://127.0.0.1:11434/v1/ |
| Local workers / model calls in flight | 1 / 1 |
| Deadline / temperature / configured limit | 300 seconds / 0 / 2048 |
| Executed runs / attempted calls | 4 / 16 |
| Unexecuted runs | 8 |
| Stopped reason | runtime/schema/transport/boundary failure; retain all attempted records |
| Literal context / result / gold leaks | 0 in all four records |

Runs in observed order:

1. v2-synthesis-easy / C2: succeeded, four calls, no errors.
2. v2-synthesis-easy / C3: succeeded, four calls, no errors.
3. v2-diagnosis-medium / C2: succeeded, four calls, no errors.
4. v2-diagnosis-medium / C3: partial, four calls, `agent_timeout`, `CancelledError`.

Failed run ID: `cfa36772e6b64dd88edfcb568c5fb3b1`. The three workers succeeded
on one attempt each (approximately 111.21, 133.66 and 114.90 seconds). Synthesizer
failed on its only attempt at 300010.480 ms. Journal 0016 records `CancelledError`,
300005.001 ms and no response. Missing token usage is **unknown**, not zero.
No retry was made even though the generic timeout error is marked retryable.

For the same task, the C2 synthesizer's serialized AgentContext is 5729 characters
and latency approximately 170.10 seconds; C3 is 5105 characters and times out
at approximately 300.01 seconds. This does not establish a context-size cause.
No partial response or inference-phase timings were preserved, so server waiting,
prefill, thinking, generation and hardware effects cannot be distinguished here.

The adapter sent `max_completion_tokens` rather than Ollama's documented
`max_tokens`; the earlier configured 2048 ceiling therefore does not establish
backend enforcement. This mismatch is not proven to have caused the timeout.
Saved model metadata lists default thinking enabled. No explicit thinking control
was sent; long reasoning is a possibility, not an established explanation.

The 12/12 operational gate failed. **No performance analysis, paired scientific
comparison or figures were generated.** The runner's automatically saved human
review is an artifact of persistence, not an authorization to interpret performance.
All attempted data remain visible, without quality-based exclusion.

See [protocol-2.3-amendment.md](protocol-2.3-amendment.md) for the prospective
600-second deadline and explicit token-limit compatibility translation. Neither
this record nor the amendment authorizes a new real-model execution.
