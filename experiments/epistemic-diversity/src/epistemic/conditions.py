"""A 2x2 role/access factorial plus a single-agent baseline."""

import random

from app.core.models import (
    AgentDefinition,
    ContextAccess,
    ExecutionPolicy,
    ModelConfig,
    WorkflowInput,
)
from app.core.schemas import SchemaRegistry
from app.orchestration.workflow import Edge, Node, WorkflowDefinition
from epistemic.models import (
    Assignment,
    ConditionConfig,
    FinalOutput,
    ModelSettings,
    PublicTask,
    Role,
    TaskInstructions,
    WorkerOutput,
)
from epistemic.paths import ROOT, digest, read_json


def configurations() -> list[ConditionConfig]:
    return sorted(
        (
            ConditionConfig.model_validate(read_json(path))
            for path in (ROOT / "configs").glob("*.json")
            if path.name
            in {
                "single_full.json",
                "multi_shared_homogeneous.json",
                "role_diversity.json",
                "epistemic_diversity.json",
                "role_plus_epistemic.json",
            }
        ),
        key=lambda c: c.id,
    )


def schemas() -> SchemaRegistry:
    registry = SchemaRegistry()
    registry.register("instructions.v1", TaskInstructions)
    registry.register("worker.v1", WorkerOutput)
    registry.register("final.v1", FinalOutput)
    return registry


def build_condition(
    task: PublicTask,
    config: ConditionConfig,
    partitions: dict[str, list[str]],
    seed: int,
    settings: ModelSettings,
) -> tuple[WorkflowDefinition, dict[str, AgentDefinition], WorkflowInput, Assignment]:
    """This function cannot load gold; all available input is public or policy IDs."""
    role_texts: dict[str, str] = read_json(ROOT / "prompts/roles_v1.json")
    varied: list[Role] = ["analytical", "skeptical", "systems"]
    random.Random(digest([task.id, seed, "roles"])).shuffle(varied)
    roles: dict[str, Role] = {
        f"worker_{i}": varied[i] if config.diverse_roles else "neutral"
        for i in range(config.worker_count)
    }
    evidence = [item.model_copy(deep=True) for item in task.evidence]
    random.Random(digest([task.id, seed, "evidence-order"])).shuffle(evidence)
    agents: dict[str, AgentDefinition] = {}
    single = config.id == "C0"
    prompt_version = "v2" if task.benchmark_version == "2.0.0" else "v1"
    worker_prompt = (
        ROOT
        / "prompts"
        / (f"single_{prompt_version}.txt" if single else f"worker_{prompt_version}.txt")
    ).read_text()
    model = ModelConfig(
        provider=settings.provider,
        model=settings.model,
        temperature=settings.temperature,
        max_output_tokens=settings.max_output_tokens,
    )
    execution = ExecutionPolicy(
        max_attempts=1, max_model_turns=1, timeout_seconds=settings.timeout_seconds
    )
    for worker, role in roles.items():
        agents[worker] = AgentDefinition(
            id=worker,
            name=worker,
            description="Research worker",
            instruction=worker_prompt + "\n" + role_texts[role],
            input_schema="instructions.v1",
            output_schema="final.v1" if single else "worker.v1",
            context=ContextAccess(
                input_keys=list(TaskInstructions.model_fields),
                knowledge_ids=partitions[worker]
                if config.separated_evidence
                else [item.id for item in evidence],
            ),
            model=model.model_copy(deep=True),
            execution=execution.model_copy(deep=True),
            publish_to=[] if single else ["synthesizer"],
        )
    if not single:
        agents["synthesizer"] = AgentDefinition(
            id="synthesizer",
            name="Synthesizer",
            description="Common synthesis stage",
            instruction=(ROOT / f"prompts/synthesizer_{prompt_version}.txt").read_text(),
            input_schema="instructions.v1",
            output_schema="final.v1",
            context=ContextAccess(
                input_keys=list(TaskInstructions.model_fields), artifact_producers=list(roles)
            ),
            model=model.model_copy(deep=True),
            execution=execution.model_copy(deep=True),
        )
    workflow = WorkflowDefinition(
        id="epistemic-study-v1",
        description="Controlled role/access comparison",
        max_parallel=3,
        mode="single" if single else "isolated" if config.separated_evidence else "shared",
        nodes=[Node(id=key, agent_id=key, final=single or key == "synthesizer") for key in agents],
        edges=[] if single else [Edge(source=key, target="synthesizer") for key in roles],
    )
    instructions = task.instructions.model_copy(deep=True)
    if task.benchmark_version == "2.0.0":
        # Criteria order is a nuisance variable, identical for every condition in a pair.
        # Shuffle without consulting gold; do not let authoring order signal the answer.
        criteria_rng = random.Random(digest([task.id, seed, "public-criteria-order"]))
        criteria_rng.shuffle(instructions.inference_rules)
        criteria_rng.shuffle(instructions.decision_rules)
    inputs = WorkflowInput(
        task=task.question,
        inputs=instructions.model_dump(mode="json"),
        knowledge={item.id: item for item in evidence},
    )
    return workflow, agents, inputs, Assignment(roles=roles, partitions=partitions, seed=seed)
