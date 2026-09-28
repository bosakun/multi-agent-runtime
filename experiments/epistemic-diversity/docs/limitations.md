# Limitations and threats to validity

Protocol 2.1 corrects an answer-position hint found after mock validation: author
order put the correct decision first in all files. Provider-facing candidate and
rule order is now independently seeded but common to each condition pair. Pilot
positions remain 4/2 rather than exactly balanced; no seed/task was changed to
tune the distribution. The literal/structural audit alone missed this semantic
shortcut, reinforcing the need for independent human review. The amended protocol
and old source/result archives are disclosed in protocol-2.1-amendment.md.

## Current v2 scope (supersedes v1 counts below)

30 tasks / ten structural families improve over six templates but are still a
small authored symbolic benchmark. Each family contributes three related cases;
v2 inference uses family-level units. The paid pilot has only six families and
C2/C3, so it cannot establish P2–P5, equivalence or broad generalization. Difficulty
is structurally assigned, not calibrated on model success. Some easy cases share
simple conjunction structures; near-zero lexical similarity does not prove
epistemic independence. Rules, candidate vocabulary and statement grammar may make
the benchmark too easy for capable models and underrepresent free-form reasoning.

Gold-relevance/importance routing remains an oracle-assisted confound. Counts and
weights are approximately balanced, not exactly equal. Per-call token caps do not
equalize total input/output exposure or single-versus-multi compute. All conditions
retain a common model's pretrained knowledge and shared public rules. Information
separation does not create different intrinsic beliefs.

Fixed-output marginal support loss is a provenance counterfactual, not a generated
answer change or causal/Shapley attribution. Canonical evaluation may reject true
unannotated claims. Source-qualified fields reduce false contradictions but cannot
fully evaluate semantic conflicts. Literal markers do not detect all leaks; invalid
HTTP bodies may be rejected before typed response audit. No LLM judge is used, so
same-model judge bias is absent but human/semantic validation is still needed.

No real credentials/model choice are available. Content freeze is complete only
when verify-freeze passes; a concrete model/endpoint must additionally be bound
before paid calls. Fake-HTTP contract tests are not live-model experiments. After
any fatal case, remaining cells are unexecuted, with partial pairs disclosed.
No automatic main run or post-hoc conclusion is authorized. Earlier v1 results,
counts and threats below are historical and must not be pooled with v2.

## Historical v1 threats / generally applicable cautions

## No empirical LLM comparison yet

No provider credentials were available. All recorded executions use a public-rule
interpreter through MockProvider. It ignores role instructions and deliberately
performs complete supported extraction. Therefore neither equality of final
scores nor differences in overlap can confirm/refute the scientific hypotheses.
Statistical routines are validated; statistical confidence in an LLM effect is
**not available**. A degenerate mock interval [0, 0] is not an equivalence result.

## Construct validity

- Information separation concerns external source access, not pretrained knowledge,
  intrinsic beliefs, learned values, independent experience or consciousness.
- Disjoint evidence sets mechanically raise evidence uniqueness. This measures
  work distribution, not creativity. Claim/insight metrics partly inherit that bias.
- An isolated worker has fewer premises; reduced local insight coverage can coexist
  with complete final performance if synthesis is effective.
- All conditions share public reasoning/decision rules. They share some knowledge
  even when private documents differ; the intervention is not total epistemic independence.
- Leakage auditing detects IDs/canaries, not all semantic paraphrases or guesses.
  ACL-enforced context isolation does not sandbox trusted Python extension code.

## Benchmark and external validity

- Synthetic benchmark bias: nine short, explicit observations with recognizable
  distractors are easier than ambiguous documents, retrieval or conflicting sources.
- Benchmark size: 24 tasks come from only six templates. Four configurations per
  template are dependent; within each three-fact group truth values co-vary.
- Task family names differ in domain framing, but both use similar symbolic rule
  composition. This is a controlled microbenchmark, not general problem solving.
- Public candidate rules/vocabulary may create ceiling effects and reduce the value
  of analytical, skeptical or systems roles. Roles have no unique tools or expertise.
- Oracle-balanced partitions use gold relevance in trusted host routing. Real-world
  partitioning quality is unknown and may substantially change outcomes.
- No generalization to other domains, long contexts, natural language synthesis,
  adversarial documents, conflicting evidence or dynamic collaboration is shown.

## Internal validity

- Model dependence: no model has yet been evaluated; future one-model results would
  remain model-specific. Model choice and deployment/version changes must be recorded.
- Prompt and role definition dependence: short weak role priorities are one
  operationalization. Temperature, wording and role strength can affect results.
- Partition strategy dependence: balanced random disjoint assignment changes both
  evidence availability and per-worker context length; those mechanisms are not separated.
- Token-budget imbalance: per-call limits match, but C0 has one call and C1–C4 four.
  Shared workers read more aggregate raw input. This is not equal-compute evaluation.
- Synthesizer bottleneck: isolated workers cannot independently check the combined
  premises; synthesis may restore or distort them. It has no raw-source verification.
- Condition order is shuffled, but latency remains affected by load, network and
  checkpoint I/O. Mock has a fixed 10ms sleep per call; its milliseconds do not
  predict provider latency or cost.

## Evaluation and statistical validity

- Canonical exact-match evaluation penalizes useful synonyms or true unannotated
  claims. Complete citation matching is stricter than merely being factually right.
- No LLM-as-a-Judge was used. Same-model judge bias is avoided, but no independent
  semantic judge or human validation supplies complementary quality evidence.
- Two mock repetitions test plumbing, not stochastic robustness. Future main has
  only four tasks under default budget, with limited power and model variability.
  Its fixed IDs cover two templates, with two variants of each, not four
  independent domains; broadening that subset requires a new declared protocol.
- Bootstrap resamples tasks, not template clusters. Template dependence can make
  nominal intervals too narrow. Do not interpret these as population confidence.
- Only pre-specified coverage endpoints are primary. Other metrics and failure
  cases are descriptive. No beneficial-looking result is promoted post hoc.
- No adversarial leakage challenge was in the benchmark. Zero detected violations
  does not establish comparative security or support H5 over authorized shared access.
- Provider usage may be missing on failed transports. Unknown costs stay null.

## Operational limitations

The runner is a local process with a durable per-campaign call budget, not a
distributed experiment service. Existing phase paths are refused instead of
silently resumed or overwritten. An interrupted phase may be incomplete; retain
its records, audit calls and runtime database. Before continuing paid work,
account for its consumed ledger and document recovery rather than starting a new
campaign to circumvent the ceiling. Raw malformed HTTP payloads are not logged.
Optional PostgreSQL/live-API tests require external services; this research-only
change was regression-tested locally with SQLite. No remote push was performed.
