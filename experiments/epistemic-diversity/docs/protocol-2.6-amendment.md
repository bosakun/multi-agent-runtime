# Prospective Protocol 2.6 — native no-thinking Windows Pilot

Written before any Protocol 2.6 model generation. The user authorized operational
improvement, execution, and autonomous recovery on 2026-09-29. No historical
Protocol 2.1–2.5 result, source, freeze, or budget will be edited or reused.

## Failure and predeclared change

Protocol 2.5 stopped with 39 calls: missing-easy/C3 worker_1 exhausted its
4096 generated-token cap on reasoning, with no final content. Diagnosis here
does not imply that the evidence-enum contract failed. Change both C2 and C3
uniformly to native Ollama POST /api/chat, think:false, stream:false, format
equal to the strict context-scoped JSON schema, options temperature:0,
num_predict:4096, num_ctx:8192. Do not add /no_think to prompts. The exact system
instruction suffix and serialized authorized context remain unchanged.

Ollama native thinking API: https://docs.ollama.com/capabilities/thinking
Native chat contract: https://docs.ollama.com/api/chat

## Fixed design and budgets

Same qwen3:14b manifest digest bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8,
six Pilot tasks, seed 20260928, C2/C3, one repetition, 12 runs, 48 calls,
benchmark/metrics 2.0.0, worker/model concurrency 1, deadline 1200 seconds.
No tools, retries, repaired outputs, or continuation of incomplete cohorts.
Same evidence scope and recursive citation validation; no gold in model input.

One separate engineering diagnostic, hard budget 1, uses exactly the failed
2.5 worker request from journal 0038_6b87dcb146b44eae9562128790d86ebb_worker_1.json.
It is explicitly selected on the failure and cannot be pooled into research
results. Its source/request digest and execution controls are sealed before
dispatch. Diagnostic must return stop, complete schema-valid WorkerOutput,
no unknown citations, no thinking output, and measured usage within bounds.
Only then create the formal Pilot freeze and backend binding. Pilot has a
separate hard budget 48: total permitted real generations for 2.6 is 49.
Failed attempts count; diagnostic or Pilot reuse is forbidden.

Before dispatch verify all historical seals, current source hashes, backend
version/model digest, and full 48-call Mock gate. Journal effective requests
and exact native controls before HTTP dispatch. Save stop reason, usage,
duration and character counts before rejecting failures, never reasoning text.
Reject prompt usage above 4096 or output usage above 4096 (8192 total bound).

Fail-stop after a failed run, schema/transport fault or boundary leak. Keep
partial results and human review; do not analyze incomplete cohorts. A further
recoverable fault requires another prospective protocol and fresh bounded
cohort, never retrospective edits to this protocol.

After all 12 successful runs/48 calls and zero boundary leaks, use the unchanged
paired Pilot analysis, figures and review. No Main experiment or superiority
claim is authorized by this small engineering Pilot. GPU residence/context are
observed independently; full offload is not the same as 100% GPU utilization.
