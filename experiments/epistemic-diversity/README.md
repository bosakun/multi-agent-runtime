# Role Diversity vs. Epistemic Diversity

**Benchmark 2.0.0 / protocol 2.3: 30 tasks / 10 structural families.**

**Current operational status:** the authorized Protocol 2.3 Qwen3 pilot stopped
after **5 runs / 19 calls** with worker output truncation, not a timeout.
No C2/C3 performance comparison follows. See the
[failure investigation and bounded diagnostic improvement](docs/qwen3-14b-protocol23-operational-failure.md).
Do not rerun its binding/campaign. Real-model reliability remains unestablished;
all prospective model/settings changes require a separately approved protocol.

The separate [six-call synthetic diagnostic](docs/token-budget-diagnostic-results.md)
has now actually completed: both 2048/4096 had 3/3 schema-valid completions, with
Thinking unchanged. Truncation was not reproduced, so doubling the limit is not
established as a fix. This is not a replacement research Pilot or permission to
launch one. [Predeclared plan](docs/token-budget-diagnostic-plan.md).

The qwen3:14b local protocol-2.1 pilot ended in an operational failure: one run,
three calls, approximately 90s, two agent timeouts and CancelledError journals.
[The preserved failure](docs/qwen3-14b-operational-failure.md) has no paired research
outcome. The subsequent [protocol-2.2 failure](docs/qwen3-14b-protocol22-operational-failure.md)
stopped at run 4 / call 16 with a synthesizer deadline failure.
[Protocol 2.3](docs/protocol-2.3-amendment.md) makes exactly two local operational
corrections: 600s deadline and explicit `max_tokens=2048` compatibility translation.
Concurrency stays 1/1, thinking stays model-default, and scientific factors stay fixed.
That preparation preceded the preserved failed launch; it is not permission to rerun it.

How does epistemic diversity created by information separation compare with
prompt-level role diversity in LLM multi-agent systems?

This research application imports the existing runtime. Protocol 2.3 adds one
generic optional token-limit field to its HTTP adapter; the default behavior is unchanged.
V1's 24-task benchmark and 250 mock runs are retained unchanged under their old
paths. Do not pool those records with v2. The [v1 README](docs/archive/README-v1.md)
is historical; its real-main commands are no longer enabled.

## Conditions and scope

| Condition | Workers | Roles | Evidence |
|---|---:|---|---|
| C0 | 1 | neutral | full |
| C1 | 3 | identical neutral | full |
| C2 | 3 | analytical / skeptical / systems | full |
| C3 | 3 | identical neutral | disjoint balanced partitions |
| C4 | 3 | three roles, shuffled per task/seed | disjoint balanced partitions |

C1–C4 use the same artifact-only synthesizer, model/settings, output schemas,
tool permissions (none), per-call token limit and stopping rules. ContextBuilder
enforces evidence visibility; worker output is not unrestricted chat. Public task
rules are shared, but raw documents are projected according to explicit policies.

The paid pilot tests **C2 vs C3 only** over six fixed tasks: 12 runs / **48 calls**.
All five conditions would need 102 calls for six tasks, above the default 60-call
pilot ceiling. C0/C1/C4 remain implemented and exercised in full mock validation.
This is a feasibility pilot, not a replacement for all five-condition research.
Real main/full execution is disabled; a successful pilot does not start it.

## Stronger controlled benchmark

Ten families cover synthesis, root-cause diagnosis, constraint satisfaction,
contradiction resolution, missing information, sequential causality,
multi-perspective decisions, failure analysis, constrained planning and evidence
ranking. Each has easy/medium/hard cases based on dependency/interaction structure,
not just word count. Three cases per family are related and not treated as three
independent families.

[Taxonomy](docs/benchmark-taxonomy.md) explains information patterns, failure modes,
schema, difficulty and residual partition imbalance.
[Audit](docs/benchmark-audit.md) checks duplicates, gold leakage, solvability,
shortcuts, canonical conflicts, dependency depths and 180 seeded assignments.
[Metric audit](docs/metric-audit.md) defines useful uniqueness, overlap, collective
coverage gain and **fixed-output provenance marginal support loss**. The latter is
not an LLM regeneration ablation. [Limitations](docs/limitations.md) remain explicit.

Public inputs and gold are separate files under `benchmarks/v2/public/` and
`benchmarks/v2/gold/`. A host-only compiler reads authored specifications; models
never receive gold, difficulty or routing labels. Oracle relevance/importance
routing remains a declared limitation. Full-context C0 can solve every task.

## Offline verification and reproduction

From the repository root, Python 3.12+; no extra dependency or paid API is needed:

```bash
uv sync --group dev
uv run python experiments/epistemic-diversity/run.py verify-freeze
uv run python experiments/epistemic-diversity/run.py plan --phase pilot
uv run python experiments/epistemic-diversity/run.py run \
  --provider mock --phase pilot \
  --campaign experiments/epistemic-diversity/runs/my-v2 --max-model-calls 600
uv run python experiments/epistemic-diversity/run.py run \
  --provider mock --phase full \
  --campaign experiments/epistemic-diversity/runs/my-v2 --max-model-calls 600
uv run python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/my-v2/full/results.json \
  --output experiments/epistemic-diversity/results/my-v2
uv run python experiments/epistemic-diversity/run.py figures \
  experiments/epistemic-diversity/results/my-v2/analysis.json \
  --output experiments/epistemic-diversity/figures/my-v2
```

Pilot mock: 48 calls. Full mock: 30 × 17 = 510 calls. Combined 558 offline calls
fit the explicit 600-call override; it is **not** the paid default. One repetition
is enough for deterministic plumbing validation. Use a fresh campaign name:
existing phases and freezes are never overwritten. `.venv/bin/python` can replace
`uv run python` in an already-installed environment.

`benchmark` and `audit` deterministically regenerate v2 files; `verify-freeze`
must still pass afterward. To change authored tasks, declare a new version and
freeze instead of reusing 2.0.0. Legacy generation requires
`benchmark --benchmark-version 1.0.0`; old results are never regenerated implicitly.

## Freeze and safe real-provider execution

The [experiment freeze](docs/experiment-freeze.md) fixes the question, hypotheses,
conditions, benchmark/tasks, metrics, comparisons, analysis, settings and exclusions.
The [pilot plan](docs/real-pilot-plan.md) fixes six task IDs, seed and stopping rules.
`freezes/benchmark-2.0.0-protocol-2.3.json` hashes public/gold files, audit, source, prompts,
protocol documents, runtime source and dependency lock. Any change blocks launch.
The [protocol 2.1 amendment](docs/protocol-2.1-amendment.md) documents a discovered
answer-position shortcut and common seeded criteria-order randomization. The old
protocol-2 seal, archived source and mock results remain intact; do not pool cohorts.

Model ID and endpoint are deliberately **not silently chosen**. Before a paid
call, `bind-model` records them together with fixed temperature 0, 2048 completion
tokens, 90s standard / 600s local timeout, one attempt/turn, no tools and seed 20260928.
Local Ollama additionally binds a fresh campaign root and serial worker/model dispatch.
The binding names `max_tokens`; journals verify and record the actual serialized
parameter before dispatch. Standard endpoints retain `max_completion_tokens`.
Neither profile adds thinking/reasoning overrides or parameter fallback.
Launch must match
the sealed binding. See [READY_FOR_REAL_PILOT.md](READY_FOR_REAL_PILOT.md) for exact
environment variables and commands. No credentials are stored; no `.env` is
automatically loaded. API usage is separate from ChatGPT/Codex subscription usage.

Both failed local cohorts are preserved, never pooled. No protocol-2.3 real run
has been executed. Adapter regressions use fake HTTP;
those fixtures do not contact Ollama or an external provider.

## Outputs and human inspection

Each phase saves `results.json`, per-run records, runtime SQLite snapshots/events,
raw synthetic traces, a reservation ledger and per-call pre/post-dispatch journals.
Records contain benchmark/metrics versions, commit/source hash, roles/partitions,
model settings, outputs, errors, token semantics and metrics. Unknown cost is null.
The manifest records the content seal and real model binding.

`pilot-human-review.md` is generated automatically beside phase results and by
`analyze`. It contains task, condition, agent outputs, evidence IDs, final output,
gold and metrics. To regenerate it independently:

```bash
uv run python experiments/epistemic-diversity/run.py human-review \
  experiments/epistemic-diversity/runs/my-v2/pilot/results.json \
  --output experiments/epistemic-diversity/results/my-v2/pilot-human-review.md
```

Use the [qualitative template](docs/qualitative-analysis-template.md) to inspect
both successes and failures. Automatic tags suggest patterns; they do not establish
role bias, partition causality or a dominant agent's causal effect.

Seven SVGs cover conditions, performance, valid overlap, resource use, literal
leakage, collective gain/marginal support and required-insight diversity. Mock
figures are visibly labeled **MOCK VALIDATION — NOT LLM RESULTS**.

Executed protocol-2.1 validation: pilot **12 runs / 48 calls**, full **150 runs / 510 calls**.
All runtime cases succeeded with zero detected literal boundary/gold hits. These
deterministic outputs do not establish any real-model effect. Inspect the
[pilot human review](results/mock-v2p21-pilot/pilot-human-review.md),
[full mock summary](results/mock-v2p21-full/summary.md) and
[collective-gain figure](figures/mock-v2p21-full/figure6_collective.svg).

## Validation

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
MYPYPATH=experiments/epistemic-diversity/src uv run mypy --strict \
  experiments/epistemic-diversity/src experiments/epistemic-diversity/run.py
uv run pytest -q tests experiments/epistemic-diversity/tests
```

See [status](STATUS.md) and [validation](docs/validation.md) for actual executed
counts, not planned claims. [Research plan](docs/research-plan.md),
[methodology](docs/methodology.md), [related work](docs/related-work.md) and
[paper outline](paper/outline.md) distinguish protocol, software validation and
still-pending empirical research. No main experiment or paper conclusion is added.

## Operational recovery status

The latest representative recovery diagnostic succeeded, but the new real pilot
stopped after four runs when a worker cited an evidence ID outside its context.
The runtime rejected it; no performance comparison is valid. See the
[Protocol 2.4 incident](docs/qwen3-14b-protocol24-operational-failure.md) and
[failure investigation](docs/operational-recovery.md).
