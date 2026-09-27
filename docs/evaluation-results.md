# Offline sample results

Recorded on 2026-09-27 with Python 3.13.14, SQLite in-memory checkpoints and
`MockProvider` (`deterministic-v1`, 10ms artificial delay). These are single fixture
executions, not statistical benchmarks. Latency depends on the host and checkpoint
overhead. Tokens are mock character-count estimates; all costs are $0.

## Investigation

| Mode | Task success | Completeness | Conflicts | Unsupported | Leakage canaries | Calls | Input tokens | Output tokens | Latency ms |
|---|---|---|---|---|---|---|---|---|---|
| Single | true | 1.0 | 1 | 0 | 0 | 1 | 680 | 275 | 23.49 |
| Shared multi | true | 1.0 | 1 | 0 | 15 | 6 | 5202 | 1408 | 111.56 |
| Isolated multi | true | 1.0 | 1 | 0 | 0 | 6 | 4314 | 1051 | 107.78 |

## Software change review

| Mode | Task success | Completeness | Conflicts | Unsupported | Leakage canaries | Calls | Input tokens | Output tokens | Latency ms |
|---|---|---|---|---|---|---|---|---|---|
| Single | true | 1.0 | 0 | 0 | 0 | 2 | 1675 | 225 | 33.18 |
| Shared multi | true | 1.0 | 0 | 0 | 4 | 6 | 5094 | 893 | 70.18 |
| Isolated multi | true | 1.0 | 0 | 0 | 0 | 6 | 3911 | 526 | 67.63 |

All six runs had zero failed agents and zero missed expected conflicts. The
software single baseline uses one agent with a tool call and continuation. Shared
context exposes additional raw categories relative to isolated assignment: 15 in
investigation and 47 in software review, counted across model requests.

These measurements show the explicit information boundary and the cost of
additional orchestration. They do not demonstrate superior reasoning by a
multi-agent model. In these small fixtures the single baseline is cheaper and
faster. Choose isolation when role-specific information or authority is a
requirement, and measure real-model task quality separately.

Reproduce with the two `evaluate` commands in README. Expected claims and canaries
are versioned in `examples/*.case.json`; metric definitions are in
[evaluation.md](evaluation.md).
