# Findings: offline validation only

Historical v1 report below (24 tasks). Current benchmark 2.0.0 / protocol 2.1
validation is documented in [STATUS](../STATUS.md) and the
[current mock summary](../results/mock-v2p21-full/summary.md).
No old measurement below has been rescored or pooled with the new cohort.

No real-model results exist. The following measurements come from executed mock
campaigns; they are not generated example scores or estimates of LLM performance.
Execution date: 2026-09-28 JST (2026-09-27 UTC in machine-readable timestamps).

## Executed scope

| Phase | Tasks | Conditions | Repetitions | Runs | Provider calls |
|---|---:|---:|---:|---:|---:|
| Mock pilot | 2 | 5 | 1 | 10 | 34 |
| Mock full | 24 | 5 | 2 | 240 | 816 |
| Real pilot/main | 0 | 0 | 0 | 0 | 0 |

Pilot boundary/schema/runtime checks passed before full execution. Total named
campaign validation was 250 runs / 850 mock calls, using an explicit offline
ceiling of 1000. Test-suite executions are separate fixtures, not additional
research observations. Pilot and full overlap and are not pooled in inference.
There were no excluded failures, omitted full blocks or incomplete full pairs.

## Full validation outcomes

| Condition | Final success | Gold facts | Worker evidence coverage | Unique evidence | Evidence redundancy |
|---|---:|---:|---:|---:|---:|
| C0 Single | 1.000 | 1.000 | 1.000 | N/A | N/A |
| C1 Shared homogeneous | 1.000 | 1.000 | 1.000 | 0.000 | 0.667 |
| C2 Shared roles | 1.000 | 1.000 | 1.000 | 0.000 | 0.667 |
| C3 Isolated homogeneous | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| C4 Isolated roles | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

All final required insights were recovered. All unauthorized context/output hits,
gold annotation hits, contradictions, unsupported statements and agent failures
were zero. Shared conditions intentionally expose 18 additional worker-document
pairs relative to isolated assignments; that exposure is authorized, not leakage.

The overlap differences are expected consequences of a complete-extraction
interpreter with disjoint partitions. It ignores roles, so C1/C2 and C3/C4 are
behaviorally equal by construction. **These observations do not confirm H1–H5.**

## Where integration occurs

C0/C1/C2 worker outputs collectively contained both valid required insights.
C3/C4 workers contained zero: each insight requires three documents, while each
worker has only two relevant documents. Nevertheless the final synthesizer
recovered both from their published individual facts.

This is a useful implementation check: the system actually creates different
knowledge states rather than passing a hidden shared context. It also exposes a
trade-off to investigate with LLMs: partitioning can reduce local reasoning
capability and move the burden of cross-source integration to the synthesizer.
An increase in evidence uniqueness is not automatically an increase in insight.

## Resource observations

| Condition | Calls/run | Estimated tokens/run | Wall latency/run (ms) |
|---|---:|---:|---:|
| C0 | 1 | 1736.1 | 21.9 |
| C1 | 4 | 7351.0 | 52.2 |
| C2 | 4 | 7355.1 | 53.0 |
| C3 | 4 | 5522.0 | 51.3 |
| C4 | 4 | 5526.4 | 51.9 |

Means are over task averages of two repetitions. Token counts are mock
character-quarter estimates; latency includes an artificial 10ms provider sleep
and local SQL/checkpoint overhead. These are neither real token billing nor API
latency estimates. Cost is unknown/null. Within this mock, single-agent processing
achieves the same score with fewer calls and lower total resource estimates.

## Statistical confidence

All five paired contrasts on both co-primary coverage endpoints have mean
difference 0, task-bootstrap 95% interval [0, 0], permutation p=1 and Holm p=1.
Paired effect dz is undefined/null because the differences have zero variance.
Binary success has no discordant pairs, with McNemar p=1. Each contrast has 24
paired task averages, not 48 independent repetitions.

These numbers validate analysis output for a degenerate deterministic case.
They do **not** establish statistical equivalence of LLM conditions, demonstrate
adequate power, or provide confidence that an LLM effect is absent. The six
template families also invalidate an interpretation as 24 independent real-world
scenarios. Real-model effect size and uncertainty remain unknown.

## Failure-case search

Across all 48 full task/repetition pairs, neither C2-success/C3-failure nor
C3-success/C2-failure occurred. There is no observed directional failure case to
explain. The analysis pipeline stores such cases if encountered; it does not
manufacture illustrative failures. The worker insight bottleneck above is an
observed intermediate difference, **not a final-answer failure**.

## RQ status

- RQ1 (performance/recovery): pipeline measured both; LLM comparison pending.
- RQ2 (overlap/diversity): structural overlap metrics work; cognitive effect unknown.
- RQ3 (combination): no role-sensitive model evaluated; unanswered.
- RQ4 (resources/leakage): call accounting and audits work; real trade-offs unknown.
- RQ5 (single-agent advantage): mock single matches quality with lower overhead;
  no general claim about LLM tasks follows.

Reanalyze [records](../results/mock-full/records.json) with the CLI, consult the
[complete statistical output](../results/mock-full/analysis.json), and see
[limitations](limitations.md) before citing these validation numbers.
