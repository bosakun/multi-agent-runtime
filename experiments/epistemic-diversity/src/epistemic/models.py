"""Public inputs and private evaluation annotations are separate types."""

from typing import Literal

from pydantic import Field, model_validator

from app.core.models import Knowledge, Model, Uncertainty
from app.llm.openai_provider import TokenLimitParameter

ConditionID = Literal["C0", "C1", "C2", "C3", "C4"]
Family = Literal[
    "distributed_evidence",
    "multi_perspective",
    "synthesis",
    "diagnosis",
    "constraints",
    "contradiction",
    "missing",
    "causal",
    "decision",
    "failure",
    "planning",
    "ranking",
]
Role = Literal["neutral", "analytical", "skeptical", "systems"]


class Pair(Model):
    subject: str
    value: str

    def key(self) -> str:
        return f"{self.subject.strip().lower()}={self.value.strip().lower()}"


class Claim(Pair):
    evidence_ids: list[str]


class InferenceRule(Model):
    premises: list[Pair]
    conclusion: Pair


class DecisionRule(Model):
    premises: list[Pair]
    choice: str


class TaskInstructions(Model):
    reporting_fields: list[str]
    inference_rules: list[InferenceRule]
    decision_rules: list[DecisionRule]


class PublicTask(Model):
    id: str
    family: Family
    template: str
    question: str
    instructions: TaskInstructions
    evidence: list[Knowledge]
    benchmark_version: str = "1.0.0"
    difficulty: Literal["easy", "medium", "hard"] = "easy"
    dependency_depth: int = Field(default=1, ge=1)
    evidence_interaction_type: str = "conjunctive"


class GoldClaim(Pair):
    supporting_sets: list[list[str]]


class Gold(Model):
    task_id: str
    relevant_evidence_ids: list[str]
    distractor_ids: list[str]
    claims: list[GoldClaim]
    required_insights: list[GoldClaim]
    optional_insights: list[GoldClaim] = Field(default_factory=list)
    expected_conclusion: str
    constraints: list[str]
    failure_factors: list[str]
    hidden_annotation: str
    benchmark_version: str = "1.0.0"
    optional_claims: list[GoldClaim] = Field(default_factory=list)
    weak_evidence_ids: list[str] = Field(default_factory=list)
    evidence_importance: dict[str, int] = Field(default_factory=dict)
    decision_supporting_sets: list[list[str]] = Field(default_factory=list)
    allowed_uncertainty: list[str] = Field(default_factory=list)
    required_unknowns: list[str] = Field(default_factory=list)
    partition_note: str = "Oracle-balanced relevance strata."


class WorkerOutput(Model):
    claims: list[Claim]
    insights: list[Claim]
    uncertainty: Uncertainty


class FinalOutput(WorkerOutput):
    conclusion: str
    decision_summary: str


class ConditionConfig(Model):
    id: ConditionID
    label: str
    worker_count: int
    diverse_roles: bool
    separated_evidence: bool

    @model_validator(mode="after")
    def protocol_invariants(self) -> "ConditionConfig":
        expected = {
            "C0": (1, False, False),
            "C1": (3, False, False),
            "C2": (3, True, False),
            "C3": (3, False, True),
            "C4": (3, True, True),
        }
        if (self.worker_count, self.diverse_roles, self.separated_evidence) != expected[self.id]:
            raise ValueError("Condition violates the frozen five-condition protocol")
        return self


class ModelSettings(Model):
    provider: Literal["mock", "real"] = "mock"
    model: str = "public-rule-mock-v2"
    temperature: float = Field(default=0, ge=0, le=2)
    max_output_tokens: int = Field(default=2048, ge=256)
    timeout_seconds: float = Field(default=90, gt=0)
    execution_profile: Literal["standard", "local_ollama"] = "standard"

    @model_validator(mode="after")
    def local_execution_invariants(self) -> "ModelSettings":
        if self.execution_profile == "local_ollama" and (
            self.timeout_seconds != 600 or self.temperature != 0 or self.max_output_tokens != 2048
        ):
            raise ValueError("Local Ollama requires timeout 600, temperature 0, output limit 2048")
        return self

    @property
    def backend_token_limit_parameter(self) -> TokenLimitParameter:
        """Profile selection is explicit, not inferred from a model name or HTTP failure."""
        return "max_tokens" if self.execution_profile == "local_ollama" else "max_completion_tokens"


class Assignment(Model):
    roles: dict[str, Role]
    partitions: dict[str, list[str]]
    seed: int


class CallRecord(Model):
    run_id: str
    agent_id: str
    request: dict[str, object]
    response: dict[str, object] | None = None
    error: str | None = None
    latency_ms: float = 0
    backend_request: dict[str, object] | None = None
