# Research plan — current protocol pilot-2.2 / benchmark 2.0.0

Protocol 2.2 adjusts only local Ollama scheduling (worker/model concurrency 1)
and per-invocation timeout (300s) following the preserved operational failure.
All local conditions share this setting. See protocol-2.2-amendment.md.

The [protocol 2.1 amendment](protocol-2.1-amendment.md) adds common seeded
candidate/rule-order randomization after identifying an author-order shortcut.
This is documented after mock validation, before any real data; no tasks, gold,
seeds, endpoints or comparisons changed. Old seals and results remain separate.

The RQ, hypotheses and five role/access conditions are unchanged. The user requested
benchmark hardening before real execution. The authoritative pre-execution
amendment is [v2-design-amendment.md](v2-design-amendment.md), with
[taxonomy](benchmark-taxonomy.md), [metric audit](metric-audit.md),
[real pilot plan](real-pilot-plan.md) and [content freeze](experiment-freeze.md).

V2 has 30 tasks / ten structural families / three difficulty tiers. Pilot tasks
are six fixed families with two tasks per difficulty, C2/C3 only, one repetition,
seed 20260928, 48 calls under a default 60-call ceiling. Full mock exercises all
five conditions. Paid main/full are disabled; no model is silently selected.
Useful evidence/fact/required-insight diversity is separated; collective gain and
fixed-output marginal support loss are descriptive. Inference resamples family
means to reduce template pseudo-replication. Current primary pilot comparison is
P1 with two co-primary coverage endpoints; P2–P5 remain in the full design but
cannot be estimated from this pilot.

## Historical v1 plan — retained, not current execution authority

The following text preserves the original 24-task / 180-call plan. Its numerical
scope and runtime launch gate are superseded for v2; old results are not relabeled.

Date: 2026-09-27. Base repository commit: a63b676.
Local branch: research/epistemic-diversity. No remote push authorized.

**How does epistemic diversity created by information separation compare with
prompt-level role diversity in LLM multi-agent systems?**

Working title: Role Diversity vs. Epistemic Diversity in LLM Multi-Agent Systems:
Effects of Information Separation on Collective Intelligence.

This is a controlled information-access experiment. It does not manipulate model
weights, intrinsic beliefs, learned experience, or human-like personalities.
The meeting analogy motivates independence, not a meeting application.

## Research questions and falsifiable hypotheses

RQ1: How do collective relevant-evidence recovery and final task performance
change between role diversity and information separation?
RQ2: How do valid evidence/claim contributions, overlap and redundancy change?
RQ3: Does combining the two factors add benefit?
RQ4: What are the token, calls, latency and unauthorized-information tradeoffs?
RQ5: Under what benchmark conditions does single-agent processing match or exceed
multi-agent processing?

H1: C3 increases distinct relevant-evidence coverage relative to C2.
H2: Shared-context role-diverse workers retain substantial evidence overlap.
H3: Isolated workers have higher unique valid contribution rates.
H4: C4 may improve performance but incurs resource tradeoffs.
H5: Isolation may reduce unauthorized information transfer. Shared visibility is
authorized in C1/C2, so zero ACL violations in all conditions would NOT support a
between-condition reduction in actual leakage. Counterfactual raw exposure against
an isolated assignment is a separate, mechanically determined metric.

All hypotheses may be unsupported. No task or failed attempted run will be removed
because its result disagrees with a hypothesis.

## Five conditions

| ID | Workers | Role | Raw evidence | Final stage |
|---|---:|---|---|---|
| C0 | 1 | neutral | full | same final schema, single call |
| C1 | 3 | same neutral prompt | full for all | common synthesizer |
| C2 | 3 | analytical, skeptical, systems | full for all | common synthesizer |
| C3 | 3 | same neutral prompt | balanced disjoint partitions | common synthesizer |
| C4 | 3 | same three roles as C2 | balanced disjoint partitions | common synthesizer |

C1–C4: same base model, parameters, three workers, worker output schema, task,
tools (none), synthesizer prompt/schema, 2048 output-token limit per call, one
attempt, one model turn. Single shares the final-output schema and token limit.
All conditions use the same global evidence. Same task/repetition seed controls
evidence ordering, balanced partition assignment and role permutation. C2 and C4
use the same shuffled role-to-worker mapping; C4 therefore randomizes role-to-
partition association. Repetitions do not claim deterministic provider sampling:
the seed controls the experiment, not the upstream model API.

Workers publish typed claims/insights with evidence references. The synthesizer
sees the common task plus those publications and never raw evidence. A worker
cannot see other worker outputs. All access is enforced by app.ContextBuilder.

## Benchmark fixed before model outcomes

24 authored synthetic tasks: 12 distributed-evidence tasks and 12 multi-perspective
decision tasks. Each has nine evidence documents: six relevant and three
distractors. Each partition has two relevant and one distractor item; relevant
document lengths are comparable. Assignment uses hidden relevance strata, which
is an oracle-balanced best case and a declared limitation.

Public task files contain question, domain context, output vocabulary, alternative
decision rules and evidence documents. Rules enumerate candidate hypotheses and
decision criteria, not which candidate is true. Private gold files contain valid
claims/insights, complete supporting evidence sets, relevant IDs, expected
conclusion, constraints/failure-factor labels, and hidden canaries. A deterministic
mock solves public data and rules without loading gold. Natural-language claims
are mapped through a public canonical subject/value vocabulary; strict matching
limits generalization to free-form reasoning.

Pilot: first task from each family (2 tasks). Main: next two per family (4 tasks),
two repetitions if the budget allows. Full: all 24 tasks. Subsets are fixed by ID,
never selected from outcomes. Task family/template ancestry will be recorded;
related templates are not independent real-world samples.

## Metrics fixed in advance

Co-primary endpoints: final valid gold-claim coverage and worker-union relevant
evidence coverage (C0 uses its sole output). Task success is binary: a successful
runtime, all required gold claims and insights with valid complete citations,
correct conclusion, and no unsupported claims or final contradictions.

Valid claim/insight: exact normalized subject/value match to hidden annotation,
with at least one complete gold supporting set and no invented/extraneous IDs.
Relevant evidence coverage counts IDs used in these valid statements, not arbitrary
citations. Report final and worker-union coverage separately.

Unique contribution: fraction of valid union items owned by exactly one worker,
for evidence and claims separately. Redundancy: (sum of worker set sizes - union
size) / sum of sizes. Pairwise Jaccard: mean pairwise intersection/union; empty
pairs are excluded and reported null if no meaningful pair exists. C0 diversity
metrics are null (no peer comparison), never assigned an artificial perfect score.
Distinct valid worker insights are reported separately. Disjoint source partitions
can force evidence uniqueness even with no cognitive improvement.

Contradictions: number of subjects assigned conflicting normalized values, for
worker union and final output separately. Unsupported claims: statements with no
gold match or invalid/incomplete citation support. Leakage: unauthorized evidence
IDs or source canaries in actual provider requests and raw model responses,
including responses subsequently rejected by runtime validation. Gold canaries and
annotation-key leakage are checked independently. Published provenance is an
authorized release to the synthesizer; it is not a leak.

Input/output/total tokens and attempted model calls are recorded. Mock token usage
is explicitly an estimate. Wall latency includes scheduling and checkpoint I/O.
Cost is null unless provider-supplied pricing provenance is configured; unknown
pricing must not silently become $0.

## Primary paired comparisons and analysis

P1 C3 minus C2; P2 C2 minus C1; P3 C3 minus C1; P4 C4 minus C3;
P5 C3 minus C0. Positive coverage difference favors the first named condition.

Average repetitions within task before inference. Report per-condition mean,
median, SD and IQR; paired mean differences, task-resampled 95% percentile
bootstrap intervals (5000 draws, fixed seed), standardized paired effect dz when
the SD of differences is nonzero, and exact sign-flip paired permutation tests
for <=16 tasks (otherwise 20,000 seeded sign flips). Ten tests (five contrasts by
two co-primary endpoints) form one Holm-adjusted family. Other metrics are
descriptive; no opportunistic significance tests. Paired binary task success uses
exact McNemar on repetition zero, with counts of discordant task pairs. Its five
comparisons form a separate Holm-adjusted secondary family.

Each attempted failure stays in the denominator: semantic scores zero, observed
usage/errors retained. A task/repetition block not started due to budget is
planned-but-unexecuted and is not a result. Incomplete blocks are prominently
reported, and only complete task/repetition pairs enter paired differences.
Bootstrap precision is conditional on these authored tasks, not population-wide
LLM performance; same-template dependence and mock determinism invalidate broad
empirical interpretation.

## API budget and execution gates

Default real-call ceiling is MAX_MODEL_CALLS=180 across pilot + main. One complete
five-condition task/repetition block costs at most 17 calls (1+4*4), because
retries/tool loops are disabled. Pilot 2x5x1 = 10 runs/34 calls; disjoint main
4x5x2 = 40 runs/136 calls; total 50 runs/170 calls. Before running, print and save
the plan. A persisted call ledger reserves each call before dispatch and counts
transport failures too. Refuse dispatch above the ceiling. Fit a smaller complete
paired subset if the requested selection exceeds remaining calls.

Real main requires a completed valid pilot from the same protocol/model/settings,
zero boundary violations and no runtime/schema errors. Failed task answers alone
are not a reason to discard or redesign tasks. If credentials are absent, only
mock pilot/full validation is performed. Mock role prompts have no modeled
behavioral effect; mock differences cannot test the scientific hypotheses.

## Failure analysis and artifacts

Search all paired records for C2-success/C3-failure and the reverse. For each
actual case, preserve assignments, missing valid claims/evidence, raw publications,
unsupported claims and synthesis inputs. If there are none, say so. Do not invent
qualitative examples as observed failures. Ablations are optional and must not
consume primary budget; none are preplanned for this first run.

Figures: conditions diagram; observed performance; coverage/contribution/
redundancy; tokens/latency; actual leakage plus separate raw exposure. Every plot
must carry provider type and sample sizes, and mock plots must visibly say MOCK
VALIDATION — NOT LLM RESULTS. No real-model result plots without real executions.

Save experiment ID, parent git commit and source fingerprint/dirty state,
timestamps, task/condition/repetition, seeds, exact policies and prompts, role and
partition assignments, model parameters, output, metrics, usage, latency, errors,
and artifact/event trace. Raw synthetic audit files stay in the experiment tree.

## Threats to validity

Synthetic and template bias; 24-task size; same-model dependence; prompt wording;
role choice/strength; oracle-balanced partitions and missing local context;
strict canonical evaluator bias; no independent semantic judge; limited
repetitions; unequal aggregate context/token budgets (controlled per call, measured
in aggregate); latency variation and batch scheduling; source-level rather than
pretrained-knowledge isolation; mechanical diversity metrics; no evidence of
generalization to unstructured text or other domains. No world model or simulation.

## Amendments

Changes after this plan must be dated in docs/experiment-log.md and distinguish
bug fixes from changed research questions or post-hoc analyses.
