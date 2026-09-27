from app.core.models import AgentDefinition, ContextAccess, ToolAccess
from app.orchestration.workflow import Edge, Node, WorkflowDefinition


def build() -> tuple[WorkflowDefinition, dict[str, AgentDefinition]]:
    responsibilities = {
        "architecture": ["architecture", "changed_files"],
        "security": ["changed_code", "dependencies", "security_constraints"],
        "test": ["requirements", "tests", "changed_behavior"],
        "maintainability": ["diff", "design_constraints"],
    }
    agents = {
        key: AgentDefinition(
            id=key,
            name=key.title(),
            description=f"Review {key} concerns",
            instruction=(
                f"Review the software change for {key} concerns using only supplied inputs. "
                "Report actionable findings and uncertainty."
            ),
            input_schema=f"software.{key}",
            output_schema="findings",
            context=ContextAccess(input_keys=keys),
            publish_to=["final_reviewer"],
        )
        for key, keys in responsibilities.items()
    }
    agents["final_reviewer"] = AgentDefinition(
        id="final_reviewer",
        name="Final Reviewer",
        description="Combine independent review findings",
        instruction=(
            "Combine structured findings. Flag critical risks and conflicting assessments. "
            "Do not claim access to original code."
        ),
        input_schema="empty",
        output_schema="report",
        context=ContextAccess(artifact_producers=list(responsibilities)),
    )
    agents["security"].tools = ToolAccess(allowed=["scan_python"], max_calls=1)
    return WorkflowDefinition(
        id="software_review",
        description="Separated software review responsibilities",
        nodes=[Node(id=key, agent_id=key, final=key == "final_reviewer") for key in agents],
        edges=[Edge(source=key, target="final_reviewer") for key in responsibilities],
    ), agents
