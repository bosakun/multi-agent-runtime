"""Public, typed application outputs with explicit uncertainty."""

from typing import Literal

from pydantic import Field

from app.core.models import Model, Uncertainty


class EmptyInput(Model):
    pass


Severity = Literal["info", "warning", "critical"]


class Finding(Model):
    subject: str
    value: str
    evidence_ids: list[str] = Field(default_factory=list)
    severity: Severity = "info"


class Findings(Model):
    findings: list[Finding]
    uncertainty: Uncertainty


class ReviewResult(Findings):
    rejected_count: int = Field(default=0, ge=0)


class Conflict(Model):
    subject: str
    values: list[str]
    evidence_ids: list[str]


class ConflictReport(Findings):
    conflicts: list[Conflict]


class FinalReport(ConflictReport):
    summary: str
    decision: Literal["accept", "needs_review"]


class ArchitectureInput(Model):
    architecture: str
    changed_files: list[str]


class SecurityInput(Model):
    changed_code: str
    dependencies: list[str]
    security_constraints: str


class TestInput(Model):
    requirements: str
    tests: str
    changed_behavior: str


class MaintainabilityInput(Model):
    diff: str
    design_constraints: str


class SoftwareInput(ArchitectureInput, SecurityInput, TestInput, MaintainabilityInput):
    pass
