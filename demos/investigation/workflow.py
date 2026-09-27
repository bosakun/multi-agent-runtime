from app.core.models import AgentDefinition, ContextAccess
from app.orchestration.workflow import Edge, Node, WorkflowDefinition


def build() -> tuple[WorkflowDefinition, dict[str, AgentDefinition]]:
    agents: dict[str, AgentDefinition] = {}
    investigators = [f"investigator_{letter}" for letter in "abc"]
    for letter, agent_id in zip("abc", investigators, strict=True):
        agents[agent_id] = AgentDefinition(
            id=agent_id,
            name=f"Investigator {letter.upper()}",
            description="Analyze assigned evidence only",
            instruction=(
                "Extract supported claims from assigned documents. Preserve conflicts and unknowns."
            ),
            input_schema="empty",
            output_schema="findings",
            context=ContextAccess(knowledge_ids=[f"evidence_{letter}"]),
            publish_to=["reviewer"],
        )
    for agent_id, schema, sources, recipients, instruction in [
        (
            "reviewer",
            "review",
            investigators,
            ["conflict_detector"],
            "Review structured findings for support. Preserve cited claims and competing accounts.",
        ),
        (
            "conflict_detector",
            "conflicts",
            ["reviewer"],
            ["synthesizer"],
            "Detect conflicting values for the same subject in reviewed findings.",
        ),
        (
            "synthesizer",
            "report",
            ["conflict_detector"],
            [],
            "Synthesize the findings and unresolved conflicts into a cautious report.",
        ),
    ]:
        agents[agent_id] = AgentDefinition(
            id=agent_id,
            name=agent_id.replace("_", " ").title(),
            description=instruction,
            instruction=instruction,
            input_schema="empty",
            output_schema=schema,
            context=ContextAccess(artifact_producers=sources),
            publish_to=recipients,
        )
    nodes = [Node(id=key, agent_id=key, final=key == "synthesizer") for key in agents]
    edges = [Edge(source=key, target="reviewer") for key in investigators]
    edges.extend(
        [
            Edge(source="reviewer", target="conflict_detector"),
            Edge(source="conflict_detector", target="synthesizer"),
        ]
    )
    return WorkflowDefinition(
        id="investigation",
        description="Partitioned evidence investigation",
        nodes=nodes,
        edges=edges,
    ), agents
