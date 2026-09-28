# Protocol abstract — not a completed empirical paper

Role prompts and information access are distinct interventions in LLM multi-agent
systems, yet a comparison that changes both can obscure their respective effects.
We specify a same-model study separating prompt-level role diversity from
epistemic diversity induced by runtime-enforced evidence partitions. A single-agent
baseline accompanies a two-by-two factorial design over worker role and evidence
visibility. Three workers communicate through typed artifacts to a common
synthesizer that cannot inspect their raw private context. A 24-task controlled
synthetic benchmark separates public inputs from private gold annotations.
Pre-specified outcomes include supported claim coverage, relevant-evidence
recovery, contribution overlap, contradictions, boundary violations and resource
use, with task-paired analysis and bounded model-call accounting. We implemented
the protocol on an existing policy-driven runtime and validated 250 offline mock
runs, including pilot and full-benchmark phases. These executions establish
software-path functionality, not an empirical advantage of any LLM condition.
Real-model experiments remain pending because credentials were unavailable.
The proposed study tests whether information separation changes useful collective
reasoning rather than merely producing mechanically distinct evidence assignments.

Replace this protocol abstract only after real results have been analyzed without
outcome-dependent changes to the primary endpoints.
