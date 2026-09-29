# Qwen3 local Ollama generation-budget diagnostic plan v1

Prepared 2026-09-29 JST after approval to prepare a plan. **Planning only**:
no implementation of a real launcher, binding, new executable freeze, campaign
or model generation is authorized by this document. This is not Protocol 2.4.
The stopped Protocol 2.3 and its scientific design remain immutable.

Machine-readable proposal: `diagnostics/token-budget-v1/plan.json`.
Predetermined inputs: `diagnostics/token-budget-v1/inputs.json`.

## Question and prior evidence

Does doubling the total generation ceiling from 2048 to 4096 allow schema-valid
completion on predetermined synthetic inputs, with model-default Thinking,
temperature 0 and a 600s per-call deadline unchanged?

Protocol 2.3 stopped after five runs / 19 calls on worker_0 length termination,
not a timeout. The failed call's token count and reasoning split were not saved.
See [the investigation](qwen3-14b-protocol23-operational-failure.md).
Thinking budget exhaustion is a hypothesis, not the established root cause.
4096 is a prospective doubling for a minimal diagnostic contrast, **not a
proven sufficient limit** and not a new final-answer-only allocation.

## Separate diagnostic cohort

This is a generation-compatibility check, not C2/C3 performance research. Do not
read benchmark public/gold inputs, replay failed tasks, select scored tasks,
calculate research metrics, invoke judges or pool records with Protocol 2.1–2.3.
Authored artifacts in the inputs file are synthetic fixtures, not actual agent
outputs or alleged real experiment results. There are no hidden gold answers.

Three fixtures are fixed before any new generation:

| ID | Input shape | Existing output schema | Purpose |
|---|---|---|---|
| diag-direct | Two direct inspection observations, no rules | WorkerOutput | Short extraction / plumbing control |
| diag-partial | Two observations and one rule requiring an unobserved third field | WorkerOutput | Partial information and uncertainty handling |
| diag-artifacts | Three authored structured notes, no raw records | FinalOutput | Artifact-only synthesis / completion |

Both ceilings get exactly the same serialized context for each fixture, including
fixed IDs/timestamps. Reuse the unchanged neutral worker/synthesizer prompt files,
existing schemas and provider system suffix. No concise-answer hint, /no_think,
rule simplification or schema repair is introduced. There are no dynamically
generated worker predecessors in this diagnostic: **one fixture cell is one call**.

The fixture run_id is a fixed input identifier, not the campaign execution ID.
Each cell has its own durable call ID, journal and budget reservation. Prompt,
schema and context bytes must match across paired ceilings. Only `max_tokens`
differs in the wire body; experiment/cell identity is logged out of band.

## Fixed controls and explicit manipulation

- Model `qwen3:14b`; endpoint `http://127.0.0.1:11434/v1/`.
- Total generated-token ceilings: **2048 control / 4096 candidate** via `max_tokens`.
- Temperature **0**; Thinking **model default**, no explicit `think`, reasoning
  effort/budget or prompt-based suppression. All other provider fields unchanged.
- Per-call and HTTP deadlines **600 seconds**; one dispatch at a time; no tools.
- One repetition per fixture/ceiling; **no retries, continuations or resume**.
- Order seed **20260928**, stored for reproducibility. It seeds scheduling only;
  no backend `seed` is added, matching the existing provider's request behavior.
  Temperature 0 is not a guarantee of determinism. Default-thinking/greedy-decoding
  risks remain deliberately unaddressed in this one-factor diagnostic.

This proposal must NOT relax the frozen `ModelSettings` local invariant or route
4096 through the current real-pilot CLI. Any future harness belongs outside sealed
scientific source, with an explicit diagnostic-only binding and independent seal.

## Fixed ordering and budget

Use `random.Random(20260928)`: shuffle IDs in the authored order
`[diag-direct, diag-partial, diag-artifacts]`, then shuffle first-ceiling slots
`[2048, 4096, 2048]` using the same generator. Run each pair in its assigned order.
The six exact cells are stored in plan.json:

1. diag-direct / 4096
2. diag-direct / 2048
3. diag-partial / 2048
4. diag-partial / 4096
5. diag-artifacts / 2048
6. diag-artifacts / 4096

Two pairs start with 2048; one starts with 4096. This partly balances warm-up/order
effects; three pairs cannot balance perfectly. Thermal throttling, cache state,
model loading and background activity still limit interpretation. No warm-up
generation or extra model probe is included. Record hardware/backend/model details
using non-generation metadata checks only after explicit execution approval.

**Budget: 3 fixtures × 2 ceilings × 1 repetition = 6 calls**, hard maximum 6.
A future launcher must enforce the lower of the immutable binding limit 6 and
`MAX_MODEL_CALLS` (expected 6); a higher environment value cannot expand the grid.
If the effective remaining budget is below six, refuse before any dispatch;
do not reduce fixtures or ceilings to fit a smaller budget.
Reserve durably before dispatch; failed/cancelled attempts are not refunded.
Require a fresh, unused campaign/budget; never share budgets with historical runs.

If backend limits are enforced, planned worst-case generated tokens are
`3 × (2048 + 4096) = 18432`; this includes any thinking, not just final JSON.
Input tokens and financial cost are unknown before execution and are not invented.
Per-call deadline upper bounds sum to **3600s / 60 minutes** of generation waits,
plus preflight and persistence overhead. This is not a promise of elapsed time or
a fixed wait. The larger ceiling may hit the unchanged 600s deadline.

## Measurements and persistence

Before dispatch verify explicit token key/value and absence of Thinking overrides.
Attach the existing metadata-only HTTP observer before provider parsing. Seal the
observer, adapter, new harness, fixtures, prompts, schemas, locked dependencies
and plan before generation. Record git commit AND dirty state/file hashes.

Persist each reservation and outcome, including failures and unexecuted cells:

- Cell/fixture ID, ceiling, fixed order, source/plan seal and binding hashes.
- Exact nonsecret generation settings, model/backend version and hardware notes.
- HTTP status / finish_reason, reported input/generated/total tokens.
- Optional reported reasoning-token count, reasoning/final-content character
  counts and JSON-object presence; **no text or hidden reasoning** is persisted.
- Pydantic schema validation outcome and safe error code; no response salvage.
- Latency, attempts, consumed budget and stop reason.

Unknown measurements stay null, including timeouts with no completed HTTP
response. Character counts are not token counts. Envelope metadata cannot prove
the exact hidden-reasoning/final-token split when the backend omits that split.
Primary endpoints are schema-valid terminal completion, length termination and
deadline/transport/schema failure—not correctness, insight coverage or C2/C3 rank.

## Diagnostic stop policy — distinct from the research Pilot

`finish_reason=length` is an expected **failed diagnostic outcome**, persisted
without parsing/repairing/salvaging final content. Continue only to the next
already specified independent grid cell. This is not a retry, automatic cap
escalation or permission to continue the failed research pilot.

Stop the diagnostic campaign immediately after persisting any timeout, transport,
HTTP/refusal error, non-length schema/envelope failure, unexpected finish reason,
missing required input/generated usage counts in a completed response, observer/
persistence/boundary error, or binding/budget mismatch. Record all unexecuted
cells. No restart, completion of missing cells, replacement input or added ceiling
is authorized by this plan. Human cancellation also consumes reserved calls.

## Prospective interpretation / decision rules

Always show all six planned cells, including failed and unexecuted cells. Do not
select based on answer quality or characterize missing cells as successes.

- If 2048 has at least one length failure and all three 4096 cells have valid
  terminal completions with required metadata, that supports budget sensitivity
  **on these fixtures only**. 4096 may be proposed for a reviewed new pilot;
  it is not automatically adopted or evidence about epistemic diversity.
- If both ceilings complete all three fixtures, these probes did not reproduce
  the operational issue. Do not claim 2048 is reliable for the full benchmark,
  or that doubling helps, merely because higher-budget outputs were valid.
- If either ceiling has other operational failures or the grid stops early,
  report incompleteness and exact failure; no reliability claim follows.
- If 4096 still truncates, do not automatically try 8192. A new predeclared
  diagnostic plan would be required. Larger budgets can make timeouts more likely.
- With three observations per ceiling, show counts/descriptive paired outcomes
  only; no significance claim or general reliability guarantee is justified.

## Implementation / execution approval gates

Planned fresh root: `runs/qwen3-14b-token-budget-diag-v1`; planned binding at its
root; planned independent seal: `diagnostics/token-budget-v1/seal.json`.
**None exists or is created by plan preparation.** These names are not permission
to reuse a failed path. The current Protocol 2.3 seal remains valid and unchanged.

Next step requires approval to implement the diagnostic-only harness, validate it
with fake HTTP/Mock, seal the reviewed plan and create its fresh binding. After
that, real execution needs **separate explicit approval of these six calls**.
No executable real command is provided because a launcher does not yet exist.
The old `run.py run --provider real` command is not suitable for this diagnostic.

Even a favorable diagnostic does not authorize a new scientific pilot. That
requires a reviewed amendment with common controls for C2/C3, a new freeze,
binding/campaign and launch approval. Benchmark 2.0.0, six research task IDs,
roles/partitions, metrics and all historical records remain intact. No main/full,
other model, added repetitions, push or research conclusion is part of this plan.

## Plan preparation validation actually executed

Using the existing Python 3.13.14 environment, the five new offline plan tests
validate the six-cell budget/order, synthetic contexts/artifact schemas, prompt
references, stop scope, and unchanged 2048 local-Pilot invariant. Combined runtime
and research tests: **212 passed / 3 existing external-service skips**. Formatter,
lint, both strict typing checks, git diff whitespace checks and current freeze
verification pass. The 228 protected files retain their pre-plan raw-byte hashes,
including all three campaigns, bindings, benchmark and freezes. Proposed future
campaign/binding/seal paths remain nonexistent. **Zero new real calls** were made.
The explicit JSON schedule is authoritative for future execution, not a new
random draw on another interpreter or after inspecting model results.
