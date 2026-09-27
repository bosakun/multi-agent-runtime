"""Shared value objects and explicit execution state."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue


def new_id() -> str:
    return uuid4().hex


def now() -> datetime:
    return datetime.now(UTC)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Status(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class Usage(Model):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    model_calls: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0, ge=0)

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.model_calls += other.model_calls
        self.cost_usd += other.cost_usd


class Uncertainty(Model):
    confidence: float | None = Field(default=None, ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class ContextAccess(Model):
    include_task: bool = True
    input_keys: list[str] = Field(default_factory=list)
    knowledge_ids: list[str] = Field(default_factory=list)
    artifact_producers: list[str] = Field(default_factory=list)
    shared_memory_keys: list[str] = Field(default_factory=list)
    private_memory_keys: list[str] = Field(default_factory=list)
    long_term_memory_keys: list[str] = Field(default_factory=list)
    receive_messages: bool = True
    max_context_chars: int = Field(default=100_000, ge=100, le=2_000_000)


class ToolAccess(Model):
    allowed: list[str] = Field(default_factory=list)
    max_calls: int = Field(default=4, ge=0, le=100)
    timeout_seconds: float = Field(default=10, gt=0, le=300)


class ModelConfig(Model):
    provider: str = "mock"
    model: str = "deterministic-v1"
    temperature: float = Field(default=0, ge=0, le=2)
    max_output_tokens: int = Field(default=2048, gt=0)
    input_cost_per_million: float = Field(default=0, ge=0)
    output_cost_per_million: float = Field(default=0, ge=0)


class ExecutionPolicy(Model):
    timeout_seconds: float = Field(default=60, gt=0, le=3600)
    max_attempts: int = Field(default=2, ge=1, le=10)
    retry_delay_seconds: float = Field(default=0.05, ge=0, le=60)
    max_model_turns: int = Field(default=5, ge=1, le=50)


class AgentDefinition(Model):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    name: str
    description: str
    instruction: str
    input_schema: str
    output_schema: str
    context: ContextAccess = Field(default_factory=ContextAccess)
    tools: ToolAccess = Field(default_factory=ToolAccess)
    model: ModelConfig = Field(default_factory=ModelConfig)
    execution: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    publish_to: list[str] = Field(default_factory=list)


class Knowledge(Model):
    id: str
    content: str
    trust: Literal["untrusted_data"] = "untrusted_data"


class Artifact(Model):
    id: str = Field(default_factory=new_id)
    name: str
    version: int = Field(ge=1)
    producer: str
    node_id: str
    schema_id: str
    payload: dict[str, JsonValue]
    readers: list[str]
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now)


class ArtifactRef(Model):
    id: str
    version: int = Field(ge=1)


class MessageEnvelope(Model):
    id: str = Field(default_factory=new_id)
    sender: str
    recipients: list[str] = Field(min_length=1)
    message_type: Literal["artifact.published"] = "artifact.published"
    artifacts: list[ArtifactRef] = Field(min_length=1)
    created_at: datetime = Field(default_factory=now)


class AgentContext(Model):
    agent_id: str
    run_id: str
    task: str | None = None
    inputs: dict[str, JsonValue] = Field(default_factory=dict)
    knowledge: list[Knowledge] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    messages: list[MessageEnvelope] = Field(default_factory=list)
    private_memory: dict[str, JsonValue] = Field(default_factory=dict)
    shared_memory: dict[str, JsonValue] = Field(default_factory=dict)
    long_term_memory: dict[str, JsonValue] = Field(default_factory=dict)

    def evidence_scope(self) -> set[str]:
        scope = {item.id for item in self.knowledge}
        for artifact in self.artifacts:
            scope.update(artifact.evidence_ids)
        return scope


class SafeError(Model):
    code: str
    retryable: bool = False


class AgentResult(Model):
    status: Status
    output: dict[str, JsonValue] | None = None
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    usage: Usage = Field(default_factory=Usage)
    error: SafeError | None = None


class AgentRun(Model):
    id: str = Field(default_factory=new_id)
    node_id: str
    agent_id: str
    status: Status = Status.PENDING
    attempts: int = 0
    model: str
    context_categories: list[str] = Field(default_factory=list)
    context_artifact_ids: list[str] = Field(default_factory=list)
    latency_ms: float = 0
    result: AgentResult | None = None


class Event(Model):
    id: str = Field(default_factory=new_id)
    run_id: str
    sequence: int = Field(ge=1)
    kind: str
    node_id: str | None = None
    data: dict[str, JsonValue] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now)


class WorkflowInput(Model):
    task: str = Field(min_length=1, max_length=20_000)
    inputs: dict[str, JsonValue] = Field(default_factory=dict)
    knowledge: dict[str, Knowledge] = Field(default_factory=dict)


class WorkflowState(Model):
    task: WorkflowInput
    nodes: dict[str, Status]
    artifacts: list[Artifact] = Field(default_factory=list)
    messages: list[MessageEnvelope] = Field(default_factory=list)
    agent_runs: list[AgentRun] = Field(default_factory=list)
    approvals: dict[str, bool] = Field(default_factory=dict)
    final_artifact_ids: list[str] = Field(default_factory=list)


class Run(Model):
    id: str = Field(default_factory=new_id)
    workflow_id: str
    workflow: dict[str, JsonValue]
    agents: dict[str, AgentDefinition]
    state: WorkflowState
    status: Status = Status.PENDING
    revision: int = 0
    event_count: int = 0
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)

    def usage(self) -> Usage:
        total = Usage()
        for attempt in self.state.agent_runs:
            if attempt.result:
                total.add(attempt.result.usage)
        return total
