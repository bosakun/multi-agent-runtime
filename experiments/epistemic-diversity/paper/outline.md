# Paper development outline

## Current Methods / Benchmark / Metrics amendment (benchmark 2.0.0 / protocol 2.1)

**Real-model results pending.** No Results or Conclusion claims are added.
Methods should now describe the immutable content seal plus pre-call model binding,
a six-family C2/C3 feasibility pilot (48 calls), operational fail-stop and retained
semantic failures. Benchmark is 30 cases / ten structural families, with three
structural difficulty tiers and separately versioned public/gold files. Include
the taxonomy, shortcut/duplicate/partition audit and shared easy-control structures.
Describe the pre-real candidate-position audit and common seeded public-rule
randomization, preserving the superseded mock cohort. Pilot position balance is
4 first / 2 second, not a perfectly balanced counterbalancing design.
Metrics separate valid facts, relevant evidence and required insights; add collective
coverage gain and clearly labeled fixed-output provenance marginal support loss,
not counterfactual LLM regeneration. V2 paired inference uses family-level units;
model/version cohorts and old v1 results must not be pooled. The old page-allocation
outline below remains a historical writing scaffold, not a source of current counts.

Working title: **Role Diversity vs. Epistemic Diversity in LLM Multi-Agent Systems:
Effects of Information Separation on Collective Intelligence**.

Status: protocol and implementation exist; **no real-model empirical paper draft
is claimed**. The mock-only software validation does not justify a results-driven
6–10 page paper. This outline specifies how to develop one after real execution.
The protocol abstract is [abstract.md](abstract.md).

## 1. Abstract (~0.25 page)

State the causal comparison, same-model controls, benchmark and actual sample
sizes. Report direction, magnitude and uncertainty only for executed real runs.
Do not describe mechanical evidence uniqueness as emergent intelligence.

## 2. Introduction (~0.75 page)

Motivate diversity of accessible evidence separately from role labels and model
heterogeneity. Human meetings are an analogy, not an architectural requirement.
Explain why homogeneous multi-agent and single-agent controls are both necessary.
Proposed contributions: explicit access-controlled manipulation, reproducible
benchmark/metrics, and ultimately an empirical comparison whose direction is open.
Do not claim that existing multi-agent work universally shares identical knowledge.

## 3. Related Work (~0.75 page)

Use the verified primary references in [related-work.md](../docs/related-work.md):
ReConcile (model heterogeneity/consensus), iAgents (information asymmetry), Hegazy
(diverse trained models in debate), DMAD (different reasoning approaches), and
AgentPanel (heterogeneous human–AI exploration). Distinguish all these interventions
from the present role × access factorial. Expand the literature search before
claiming novelty; do not cite unverified philosophical or empirical sources.

## 4. Multi-Agent Runtime (~0.5 page)

Explain the trusted-host boundary, ContextBuilder projection, detached contexts,
typed publications, fixed DAG, parallel workers and common synthesis. Describe
actual request/response auditing and source-canary limitations. No hidden reasoning
logs, unrestricted peer chat or experimental dependencies in the runtime core.
One architecture diagram is sufficient; the paper is not a framework feature list.

## 5. Research Questions (~0.5 page)

RQ1 performance/recovery; RQ2 overlap; RQ3 combined manipulation; RQ4 resources and
leakage; RQ5 single-agent trade-off. State H1–H5 as falsifiable hypotheses. H5 needs
careful wording: authorized shared exposure is not an ACL violation.

## 6. Experimental Setup (~1 page)

Present C0–C4 (Figure 1), controlled parameters, randomized assignments, source
partitions, schema, unchanged synthesizer and explicit stopping/call limits.
Describe public/gold separation, two task families, six templates/four variants,
oracle-balanced routing and co-varying premises. Report actual provider/model
version, source fingerprint, execution dates, repetitions and call accounting.
Separate full dataset, executed subset, pilot, attempted failures and unexecuted
blocks. Name all changes from the pre-execution plan in an amendment table.

## 7. Metrics (~0.75 page)

Give formulas for claim support, evidence coverage, uniqueness, redundancy and
Jaccard. Explain the distinction between fact recovery and higher-level insights.
Describe exact canonical evaluation, no judge, null unknown cost, actual boundary
audit, task-paired inference, multiplicity families and undefined effect sizes.
Disclose missing usage on failed transport and strict-evaluator limitations.

## 8. Results (~1 page; pending real data)

Table: actual task/run counts and failure accounting. Table: P1–P5 paired effects,
95% bootstrap intervals, dz and adjusted p-values for the two primary endpoints.
Figures 2–5: performance, information diversity, resource trade-offs, leakage.
Keep mock plumbing validation in an appendix, never pooled into main results.
Current mock observations are documented in [findings.md](../docs/findings.md).
All real-model cells remain unfilled until measured.

## 9. Analysis (~0.75 page; pending real data)

Search both directional C2/C3 failure cases, retaining unfavorable outcomes.
Trace missing context → published claims → synthesis errors. Separate failures of
retrieval/reporting from failures of integration. If no discordant cases exist,
report that. Inspect role/partition interactions descriptively without promoting
post-hoc comparisons to primary endpoints. Ablations require remaining budget and
a separately recorded plan; none have been run.

## 10. Limitations (~0.5 page)

Small synthetic benchmark; constrained decision rules; no pretrained-knowledge
isolation; single-model dependence; weak roles; oracle partitioning; no human
semantic validation; no naturalistic communication. Distinguish unimplemented
extensions from empirically unsupported claims.

## 11. Threats to Validity (~0.5 page)

Use [limitations.md](../docs/limitations.md): synthetic/template bias, sample size,
model/prompt/role/partition dependence, evaluator bias, absence of same-model judge
(no judge used), limited repetitions, unequal aggregate token budgets, latency
variation, task-template dependence and domain generalization. No p-value can
repair these design limitations. Preregister additional robustness checks.

## 12. Discussion (~0.5 page)

Discuss whether information partitioning distributes useful work or merely shifts
integration to a bottleneck. Relate observed quality to overhead rather than
assuming more agents are desirable. A null or single-agent-favoring result is
legitimate. Avoid extrapolation to intrinsic human-like beliefs or creativity.

## 13. Conclusion (~0.25 page)

Answer only questions supported by real executed data. State what remains unknown.
If no robust difference is established, say so. Future work can vary partition
quality, agent count, raw-source synthesis and role strength under separately
controlled protocols. World models are explicitly outside this study.

## Submission readiness checklist

- Real pilot and main executed within ledger budget; all attempts preserved.
- Gold and context boundary tests pass on the evaluated source version.
- All condition/task pairs accounted for, including errors and missing blocks.
- No benchmark changes selected to favor the hypothesis.
- Independent annotation/design review and broader literature check performed.
- Figures regenerated from the exact released records; captions state provider/n.
- Template dependence and limited power discussed; no mock-derived LLM claims.
