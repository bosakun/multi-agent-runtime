# Related work: verified primary sources

Checked 2026-09-28 JST using primary publication/author-hosted arXiv pages. This is
a focused related-work pass, not a systematic review or a claim of exhaustive
novelty. Findings below describe the authors' studies, not replications here.

## Model heterogeneity and debate

Justin Chih-Yao Chen, Swarnadeep Saha and Mohit Bansal.
*ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse
LLMs*. ACL 2024; arXiv:2309.13007v3.
[Primary text](https://arxiv.org/html/2309.13007v3).
ReConcile combines different model families, multiple discussion rounds and
confidence-weighted consensus. Its diversity source is primarily model
heterogeneity, whereas this experiment holds the model fixed and varies evidence
access separately from role prompts. Its reported benefits do not establish that
disjoint external context improves a same-model system.

Mahmood Hegazy. *Diversity of Thought Elicits Stronger Reasoning Capabilities in
Multi-Agent Debate Frameworks*. arXiv:2410.12853v2 (2025 revision of 2024 work).
[Primary abstract and paper](https://arxiv.org/abs/2410.12853).
The author compares diverse trained models with repeated instances of a model on
mathematical reasoning. This motivates examining sources of diversity, but does
not by itself identify the causal effect of runtime-enforced information separation.

## Information asymmetry

Wei Liu et al. *Autonomous Agents for Collaborative Task under Information
Asymmetry*. NeurIPS 2024; arXiv:2406.14928v2.
[Primary text](https://arxiv.org/html/2406.14928v2).
iAgents addresses agents serving different users with private information. Its
InfoNav mechanism guides exchange and InformativeBench evaluates collaboration
under asymmetry. This is directly relevant to private context and communication.
Our small fixed worker-to-synthesizer DAG differs from its proactive communication
and memory retrieval; we do not reproduce its benchmark or claim better performance.

## Diversity of reasoning approaches

Yexiang Liu, Jie Cao, Zekun Li, Ran He and Tieniu Tan.
*Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate*.
ICLR 2025.
[Official proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3de667dab3b3d812583abc0a786139a0-Abstract-Conference.html).
DMAD distinguishes different reasoning approaches from merely assigning personas.
It is relevant to the difference between role labels and substantive diversity.
Its approach diversity is not the same intervention as the document ACLs studied
here; our weak perspective prompts should not be equated with its method.

## Human–AI scientific exploration

Zhiyao Cui et al. *AgentPanel: Toward a New Paradigm for Human–AI Collaboration
in Exploring Scientific Questions*. arXiv:2608.03283v1, 4 August 2026.
[Primary abstract and paper](https://arxiv.org/abs/2608.03283).
AgentPanel describes asynchronous heterogeneous agents in a research forum and
evaluates exploration with offline experiments and a human study. We treat this
as recent adjacent work, not evidence that role prompts and evidence separation
have been causally disentangled. Our experiment does not reproduce a forum or
measure human-perceived novelty.

## Positioning and remaining work

These sources establish relevant prior work in heterogeneity, debate, reasoning
strategies and information asymmetry. They do not justify a general assertion
that existing multi-agent systems all have identical beliefs or knowledge.
The proposed contribution is a transparent same-model factorial experiment using
auditable information policies, with a single-agent baseline. Whether that yields
a publishable empirical contribution remains unknown until real runs and stronger
benchmark validation exist. Broader philosophical epistemic-diversity literature
and further same-model information-partition studies remain to be surveyed.
