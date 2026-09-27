"""Composition of applications and explicit experimental baselines."""

from typing import Literal

from pydantic import BaseModel

from app.core.models import AgentDefinition, ContextAccess, ToolAccess, WorkflowInput
from app.core.schemas import SchemaRegistry
from app.orchestration.workflow import Node, WorkflowDefinition
from demos import schemas
from demos.investigation.workflow import build as investigation
from demos.software_review.workflow import build as software_review

Mode = Literal["isolated", "shared", "single"]


def schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    registered: dict[str, type[BaseModel]] = {
        "empty": schemas.EmptyInput,
        "findings": schemas.Findings,
        "review": schemas.ReviewResult,
        "conflicts": schemas.ConflictReport,
        "report": schemas.FinalReport,
        "software.architecture": schemas.ArchitectureInput,
        "software.security": schemas.SecurityInput,
        "software.test": schemas.TestInput,
        "software.maintainability": schemas.MaintainabilityInput,
        "software.all": schemas.SoftwareInput,
    }
    for name, schema in registered.items():
        registry.register(name, schema)
    return registry


def catalog() -> dict[str, tuple[WorkflowDefinition, dict[str, AgentDefinition]]]:
    return {"investigation": investigation(), "software_review": software_review()}


def configure(
    name: str, task: WorkflowInput, mode: Mode = "isolated", *, approval: bool = False
) -> tuple[WorkflowDefinition, dict[str, AgentDefinition]]:
    workflow, agents = catalog()[name]
    workflow.mode = mode
    if mode == "single":
        agent = AgentDefinition(
            id="single",
            name="Single Agent Baseline",
            description="All task inputs in one call",
            instruction=(
                "Analyze all supplied information and produce a supported report "
                "with conflicts and uncertainty."
            ),
            input_schema="software.all" if name == "software_review" else "empty",
            output_schema="report",
            context=ContextAccess(input_keys=list(task.inputs), knowledge_ids=list(task.knowledge)),
            tools=ToolAccess(
                allowed=["scan_python"] if name == "software_review" else [], max_calls=1
            ),
        )
        workflow = workflow.model_copy(
            update={
                "nodes": [Node(id="single", agent_id="single", final=True)],
                "edges": [],
            }
        )
        agents = {"single": agent}
    elif mode == "shared":
        for agent in agents.values():
            agent.context.input_keys = list(task.inputs)
            agent.context.knowledge_ids = list(task.knowledge)
            agent.input_schema = "software.all" if name == "software_review" else "empty"
    if approval:
        from app.orchestration.workflow import Edge

        final_id = next(n.id for n in workflow.nodes if n.final)
        # Gate the final publication, keeping existing upstream dependencies intact.
        for edge in workflow.edges:
            if edge.target == final_id:
                edge.target = "approval"
        workflow.nodes.insert(len(workflow.nodes) - 1, Node(id="approval", kind="approval"))
        workflow.edges.append(Edge(source="approval", target=final_id))
    return WorkflowDefinition.model_validate(workflow.model_dump()), agents
