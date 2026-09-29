# Prospective Protocol 2.7 — evidence-array cardinality bound

Written before any 2.7 generation, under the user's 2026-09-29 authorization
for improvement, execution and autonomous recoverable-error handling.
All 2.1–2.6 sources, budgets, freezes and partial results remain unchanged.

## Observed failure and minimal prospective change

Protocol 2.6 stopped after 11 calls, two successful runs and one partial run.
The v2-diagnosis-medium/C2 worker_2 generated 4096 tokens, thinking_chars=0,
but exhausted the output cap. A separate one-call engineering reproduction
preserved only visible message.content. It demonstrated an unbounded repeated
sequence of already authorized IDs in uncertainty.evidence_ids. No inference
about research quality is made from this selected-failure diagnostic.

For every evidence_ids array, retain the authorized-context enum and add
maxItems = len(AgentContext.evidence_scope()). Empty scope remains maxItems=0.
Apply to all nested claims, insights and uncertainty, including $defs, before
journaling/transmission. This bound uses no global evidence inventory or gold.
A set of distinct authorized citations can fit in this many entries; duplicated
IDs add no new evidence. Do not require uniqueItems (no new grammar assumption).
Also reject overlong citation arrays at the receiver, never trim or deduplicate
model outputs. Preserve the original recursive unknown-ID rejection.

Do not add limits to claims/insights, change prompts, add repeat penalties,
or increase token/deadline budgets. Native /api/chat, think:false, stream:false,
temperature:0, num_predict:4096, num_ctx:8192, deadline1200 remain as in 2.6.
The legacy frozen runner emits a max_tokens label in compact records; correct
that descriptive field to options.num_predict in new 2.7 records only. The
2.6 native call journals, not that legacy label, describe its actual wire.

## Fixed design, validation and authorization bounds

Same qwen3:14b manifest digest bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8,
Ollama version binding, six Pilot tasks, C2/C3, seed20260928, one repetition,
12 runs/48 calls, benchmark/metrics2.0.0, worker/model concurrency1.
No tools, prompt /no_think, retries, output repairs, or resume.

Require source-current 48-call Mock gate before the new engineering diagnostic.
One separate real diagnostic, hard limit1, reuses exactly the failed worker_2
request from journal 0011_54ccbae7d1e54dd88ec643dab90909b7_worker_2.json, except
for the predeclared evidence-array bounds. Bind sources, request/journal hash,
backend identity and controls before dispatch. Require complete schema-valid
WorkerOutput, stop, zero thinking, valid measured usage, authorized citations
and arrays within the bound. Only then bind and launch fresh full Pilot.
New Pilot budget48 plus separate diagnostic budget1 = maximum49 real calls.
No old residual budgets, diagnostic-result pooling, or incomplete-cohort analysis.

Stop a cohort on runtime/schema/transport failure or boundary leak. Further
recovery requires another prospective amendment/fresh bounded cohort, not edits
to a consumed one. Only 12 successful runs/48 calls and zero leaks permit the
unchanged paired analysis, figures and review. Main/full is not launched here.
