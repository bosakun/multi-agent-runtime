# Protocol 2.3 — operational compatibility amendment

Prepared 2026-09-29 JST, before any protocol-2.3 model generation. This is not
an attempt to favor C3. Neither condition's future quality is known.

## Preserved protocol-2.2 failure

`runs/qwen3-14b-protocol22/pilot/results.json` records four attempted runs and
16 calls. The first three runs succeeded. On `v2-diagnosis-medium / C3`, all
three workers succeeded on their only attempt; the synthesizer exceeded its
300-second deadline (300010.480 ms). The run is partial, with `agent_timeout`
and a `CancelledError` call journal. All recorded context/result/gold leaks are
zero. Eight planned runs were unexecuted. This is an **operational failure**,
not a conclusion about model answer quality or epistemic diversity.

The same task's successful C2 synthesizer had 5729 serialized context characters
and approximately 170.10 seconds latency. The C3 synthesizer had 5105 characters
and approximately 300.01 seconds latency. These are context serialization lengths,
not complete HTTP payload sizes or token counts. Input size alone cannot explain
the failure. No response or token usage was saved for the cancelled call; its
internal inference phase and root cause remain unknown.

Both earlier campaigns, their bindings, results, traces, journals, SQLite budgets,
human reviews and existing hardware/model notes remain byte-for-byte preserved.
Protocol 2.1's one-run/three-call failure is described separately in
[qwen3-14b-operational-failure.md](qwen3-14b-operational-failure.md).

## Exactly two operational corrections

1. Only `local_ollama` agent and HTTP deadlines change from **300 to 600 seconds**.
   This is an upper deadline per invocation, not a fixed wait, a whole-run SLA,
   a retry, or a guarantee of completion. Both conditions receive the same deadline.
   Independent worker scheduling and model dispatch remain serial (1 / 1).
   Standard profile remains three workers and 90-second deadlines.
2. Only `local_ollama` selects the explicit Chat Completions token-limit parameter
   **`max_tokens: 2048`**, instead of `max_completion_tokens: 2048`. There is no
   parameter negotiation, silent fallback, dual-parameter request or extra probe call.
   Standard provider behavior remains `max_completion_tokens`.

The semantic configured generation ceiling remains **2048**. This correction
translates that ceiling to the backend's supported field; it does not add tokens.
Ollama 0.34.4's request type exposes `max_tokens`, and its converter maps that
field to `options.num_predict`. The inspected implementation does not expose
`max_completion_tokens`; therefore the earlier configured limit was not evidence
of backend enforcement. See the [versioned official implementation](https://github.com/ollama/ollama/blob/v0.34.4/openai/openai.go)
and [official compatibility specification](https://docs.ollama.com/api/openai-compatibility).
Fake HTTP verifies what we send, not an arbitrary server's actual enforcement.
Server upgrades, customized builds and default inference behavior remain risks.

The small runtime change is a generic, explicit provider-constructor choice of
token-limit field. Runtime has no experiment/profile/model-specific branch and
imports no experiment code. Its default remains unchanged. The research runner
alone chooses the local strategy. Actual serialized HTTP token-limit key/value
is checked before transmission and recorded in call journals, including attempts
whose response later fails. Secrets, HTTP headers and hidden reasoning are not logged.

## Unchanged scientific factors

Benchmark **2.0.0**, all public/gold bytes, six task IDs, C2/C3, role definitions,
partitions and seeded assignment, ContextPolicy, prompts, schemas, synthesizer,
public-rule and condition ordering, artifact-only visibility and information
boundaries are unchanged. Seed **20260928**, repetitions **1**, temperature **0**,
2048 semantic output limit, no tools, one attempt/turn, no retries, stopping rules,
metrics, evaluation and analysis definitions are unchanged.

Thinking stays at the model/backend default. No `think`, `reasoning_effort`,
`reasoning` budget or new prompt instruction is added. The existing system suffix
is unchanged. Qwen3 thinking variability remains a possible latency factor.

Workers have no sibling dependencies or publications in their input. Sequential
execution changes scheduling, not the role/access manipulation; synthesis still
waits for all three published artifacts. Serial scheduling is retained from 2.2,
not introduced by 2.3. Operational changes can affect completion probability,
outputs and resource measurements, so **2.1, 2.2 and 2.3 cohorts must not be pooled**.

## Prospective execution and preservation

New seal: `freezes/benchmark-2.0.0-protocol-2.3.json`. Old seals remain archival;
they are not valid authorizations for current execution. A new immutable binding
must identify protocol, freeze, model, endpoint, profile, 600-second deadline,
temperature, semantic limit, actual backend strategy, seed, selection and calls.

Required fresh campaign: `runs/qwen3-14b-protocol23`; binding:
`runs/qwen3-14b-protocol23/binding.json`. Neither historical campaign nor a child
of it can be used. Binding creation refuses existing roots; launch permits only
its binding and no prior artifacts. Existing phases/results cannot be overwritten.
There is no retry or partial resume. Forty-eight calls / twelve runs are planned;
default ceiling is 60. Historical 3 + 16 calls are not refunded: a complete future
2.3 pilot would bring historical plus prospective attempts to 67 across cohorts.

Real generation remains **not authorized by this implementation**. Only Mock
and fake HTTP transports are used for validation. A human must explicitly approve
the separate launch. Main/full real experiments remain disabled. Performance
analysis and figures require all 12 operationally successful records, 48 calls,
empty errors and zero context/result/gold leaks; incorrect schema-valid answers
are retained and are not grounds for exclusion or rerun.
