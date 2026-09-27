"""Serializable workflow graph and deterministic dependency decisions."""

from typing import Literal, Self

from pydantic import Field, JsonValue, model_validator

from app.core.models import Model, Status, WorkflowState


class Condition(Model):
    field: str
    equals: JsonValue

    def matches(self, payload: dict[str, JsonValue]) -> bool:
        value: JsonValue = payload
        for part in self.field.split("."):
            if not isinstance(value, dict) or part not in value:
                return False
            value = value[part]
        return value == self.equals


class Node(Model):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    agent_id: str | None = None
    kind: Literal["agent", "approval"] = "agent"
    join: Literal["all", "any"] = "all"
    allow_failed_dependencies: bool = False
    final: bool = False

    @model_validator(mode="after")
    def valid_kind(self) -> Self:
        if (self.kind == "agent") != (self.agent_id is not None):
            raise ValueError("Only agent nodes require an agent_id")
        return self


class Edge(Model):
    source: str
    target: str
    condition: Condition | None = None


class WorkflowDefinition(Model):
    id: str
    description: str
    nodes: list[Node] = Field(min_length=1)
    edges: list[Edge] = Field(default_factory=list)
    max_parallel: int = Field(default=4, ge=1, le=32)
    mode: Literal["isolated", "shared", "single"] = "isolated"

    @model_validator(mode="after")
    def valid_dag(self) -> Self:
        ids = {node.id for node in self.nodes}
        if len(ids) != len(self.nodes):
            raise ValueError("Duplicate node id")
        seen_edges: set[tuple[str, str]] = set()
        for edge in self.edges:
            if edge.source not in ids or edge.target not in ids:
                raise ValueError("Unknown edge endpoint")
            pair = (edge.source, edge.target)
            if pair in seen_edges:
                raise ValueError("Duplicate edge")
            seen_edges.add(pair)
        remaining = set(ids)
        while remaining:
            roots = {
                node
                for node in remaining
                if not any(e.target == node and e.source in remaining for e in self.edges)
            }
            if not roots:
                raise ValueError("Workflow must be acyclic")
            remaining -= roots
        return self

    def decision(self, node: Node, state: WorkflowState) -> Literal["ready", "wait", "skip"]:
        incoming = [edge for edge in self.edges if edge.target == node.id]
        if not incoming:
            return "ready"
        if any(
            state.nodes[e.source] in {Status.PENDING, Status.RUNNING, Status.PAUSED}
            for e in incoming
        ):
            return "wait"
        active = 0
        unavailable = 0
        for edge in incoming:
            status = state.nodes[edge.source]
            if status == Status.SKIPPED:
                continue
            if status in {Status.FAILED, Status.CANCELLED}:
                unavailable += 1
                continue
            if edge.condition is not None:
                artifacts = [a for a in state.artifacts if a.node_id == edge.source]
                if not artifacts or not edge.condition.matches(artifacts[-1].payload):
                    continue
            active += 1
        if not active:
            return "skip"
        if unavailable and node.join == "all" and not node.allow_failed_dependencies:
            return "skip"
        return "ready"
