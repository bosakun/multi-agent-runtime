# Evaluation methodology

The mock generator extracts fixture statements (`subject = value`) or review
markers. Ground truth is independently stored in `examples/*.case.json`.
Generation and evaluation share output schemas but no expected-answer object.

| Metric | Definition |
|---|---|
| Task success | Final report, full expected-claim coverage, no unsupported claims, no missed expected conflicts, no agent failure |
| Completeness | Fraction of expected `(subject,value)` pairs present in the report |
| Contradictions | Number of subjects explicitly reported as conflicting |
| Missed conflicts | Expected conflict subjects absent from the conflict report |
| Unsupported claims | Unexpected pairs, out-of-ground-truth citations, or missing required citations |
| Information leakage | Forbidden fixture markers found in an agent's context or publications, relative to the isolated assignment |
| Extra raw categories | Input/knowledge categories beyond that agent's isolated definition |
| Tokens | Provider-reported usage; mock uses characters divided by four |
| Latency | Monotonic elapsed time for creation and execution including checkpoints |
| Model calls | All attempted provider invocations, including retries and tool continuation |
| Cost estimate | Input/output usage multiplied by explicitly configured per-million prices |
| Agent failures | Failed AgentRun records |

Canary counts are exposure measurements, not a universal confidentiality detector.
The shared baseline intentionally broadens policy, so its exposure relative to
the isolated assignment is expected rather than a violation of its configured
ACL. A single-agent baseline intentionally has all inputs and no peer privacy
boundary. Semantic success and information exposure are reported separately.

Two software single-agent calls still mean one agent: the first invokes its
authorized scanner and the second consumes the result. This is why agent count
and model-call count must not be conflated.

For real-model research, use the same task fixtures and `score` interface with a
separate evaluation observer, record provider/model/version and configured prices,
repeat trials, report distributions, audit supporting evidence, and expand the
ground truth beyond the two deterministic examples. Do not interpret zero-dollar
mock cost, fixed confidence or equal fixture success as an empirical LLM result.
