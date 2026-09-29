# Protocol 2.3 operational failure and bounded improvement

Recorded 2026-09-29 JST. This is a failure investigation, not a comparison of
C2/C3 answer quality. No performance analysis, figures, retry or resume follows.

## Observed facts

Campaign: `runs/qwen3-14b-protocol23`; experiment ID
`48ba27fa2b4747f7831a8b30fbfcdac4`. Five records were retained and 19 calls were
consumed. The first four records succeeded; record five,
`v2-constraints-medium / C3`, is partial. It contains `provider_output_truncated`
and `RuntimeFault`. Seven planned records were never executed.

The failed node is **worker_0**, not the synthesizer. It attempted once and
failed at 431.352 seconds, below the 600-second deadline. Call journal 0017
records approximately 431.344 seconds and no normalized response. Worker_1 and
worker_2 succeeded in the same attempted run; the synthesizer was not dispatched.
The run took approximately 863.345 seconds. These independent worker executions
are not retries. Recorded context/result/gold leaks are all zero.

The actual request audit records `max_tokens: 2048` and no Thinking override.
The frozen adapter raises `provider_output_truncated` specifically on a
Chat Completions `finish_reason` of `length`. This proves a generation-length
termination was detected, rather than an HTTP/agent timeout or answer-quality
failure. The raw envelope was not retained, so the actual token count and
reasoning/final-output split of that failed call are **unknown**.

Preserved evidence (relative to the experiment root):

- `runs/qwen3-14b-protocol23/pilot/results.json`
- `runs/qwen3-14b-protocol23/pilot/traces/e14b05fe11754953a75d6010dc002060.json`
- `runs/qwen3-14b-protocol23/pilot/call-journal/0017_e14b05fe11754953a75d6010dc002060_worker_0.json`

## Why increasing timeout again would not fix this failure

A time deadline and a generation-token ceiling are different constraints.
The HTTP request returned a length-terminated response before 600 seconds.
Giving that same request more time cannot restore tokens that were not generated
after its ceiling. Treating its incomplete output as success, repairing JSON,
continuing generation or retrying would violate the frozen failure policy.
Fail-stop is correct; the missing operational measurements are the fixable gap.

## Mechanism and hypotheses, not a fabricated root cause

The [versioned Ollama adapter](https://github.com/ollama/ollama/blob/v0.34.4/openai/openai.go)
maps `max_tokens` to `options.num_predict`, reports `completion_tokens` from
`EvalCount`, and exposes thinking separately from final content. This limit is
not a guarantee of 2048 **final JSON** tokens after unrestricted thinking.
Do not equate serialized output characters with provider-generated tokens.

Two successful journals report 2033 and 2025 generated tokens;
both are within 1.2% of the configured limit. This is evidence of
little headroom in some calls, not a recovered measurement of failed call 0017.
Those counts alone cannot establish the size of hidden reasoning.

Possible contributors:

1. Default Qwen3 thinking consumed part of the common generation budget before
   a complete JSON answer was emitted. This is plausible, not directly observed.
2. A long final answer, repetitive generation, or a combination of reasoning and
   final JSON exhausted the budget. Their relative contributions are unknown.
3. Temperature 0 interacts poorly with default thinking for this model.
   The [official Qwen3-14B model card](https://huggingface.co/Qwen/Qwen3-14B)
   warns against greedy decoding in thinking mode because of degradation and
   repetition. This identifies a compatibility risk, not proof of repetition
   in the failed response. Temperature remains frozen at 0.

Input size, MacBook performance, partition-induced uncertainty and model behavior
may contribute, but no individual factor has been causally established. No
research hypothesis about epistemic diversity follows from this stopped cohort.

## Improvement implemented without changing Protocol 2.3

New tooling lives outside the sealed `src/` and `app/` trees:

- `diagnose.py` / `operational_diagnostics/campaign.py`: read-only failure audit;
  it exports node/call errors, latency, request limits, known-usage subtotals and
  explicit unknown usage. It never exports answers/gold or compares conditions.
  Existing output directories and all campaign/freezes/benchmark destinations
  are refused. Original results and journals are not amended.
- `operational_diagnostics/http_metadata.py`: a prospective opt-in HTTP response
  hook that captures allowlisted metadata **before** provider rejection:
  finish reason, reported tokens, optional reported reasoning-token count,
  final/reasoning character counts and syntactic JSON-object availability.
  It does not persist model text, hidden reasoning, headers, URLs or error bodies.
  Unknown counts stay null. JSON syntax is not schema validity or success.
- Fake HTTP tests prove that requests, default/OpenAI token-limit behavior,
  truncation exceptions and lack of retries are unchanged by the observer.

The observer is intentionally **not wired into the frozen runner**. Using it in
a real experiment requires a separately approved amendment, seal and fresh
binding/campaign. There is no Protocol 2.4, new freeze, new binding, real request
or rerun in this change. Benchmark 2.0.0 and all three historical campaigns stay
unchanged. This corrects diagnostic readiness, **not proven model reliability**.

Reproduce the offline report from the repository root (fresh output only):

```bash
uv run python experiments/epistemic-diversity/diagnose.py \
  experiments/epistemic-diversity/runs/qwen3-14b-protocol23/pilot \
  --output experiments/epistemic-diversity/results/protocol23-operational-diagnostics
```

## Next approval boundary

Before another scientific cohort, separately authorize a small operational
capability check using predetermined synthetic non-benchmark inputs and the
metadata observer. It must be a distinct diagnostic cohort with a declared call
budget, not a partial resume, scored-task replacement or hidden retry.

If default-thinking Qwen3 cannot reliably finish with total generation 2048 and
temperature 0, there is no demonstrated adapter fix that guarantees completion
while preserving every frozen factor. Candidate amendments are a larger common
generation budget, explicit non-thinking execution, or a different model suited
to the budget. Each changes scientific controls, must apply equally to C2/C3,
requires prior human approval and a new freeze/binding/campaign, and must not be
pooled with 2.1–2.3. No particular larger budget is established as sufficient;
blindly raising it risks longer runtimes and further timeouts.
