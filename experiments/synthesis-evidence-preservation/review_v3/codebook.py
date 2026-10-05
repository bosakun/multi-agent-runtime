"""Version/provenance validation only. Never classifies natural-language facts."""

import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from review_v3.schema import Decision, Record
from review_v3.storage import digest, file_hash

CANDIDATE_VERSION = "0.2.0"
DOCUMENTS = ("CODEBOOK.md", "ADJUDICATION-RULES.md", "PILOT-PROTOCOL.md")


class CodebookRule(Record):
    rule_id: str = Field(pattern=r"^[A-Z][A-Z0-9]*-[A-Z][A-Z0-9]*-[0-9]{3}$")
    document: Literal["CODEBOOK.md", "ADJUDICATION-RULES.md", "PILOT-PROTOCOL.md"]


class CodebookDefinition(Record):
    version: str = Field(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
    status: Literal["candidate", "freeze_candidate"]
    document_hashes: dict[str, str]
    rules: list[CodebookRule]
    example_hashes: dict[str, str] = Field(default_factory=dict)
    language_policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def consistency(self):
        major = int(self.version.split(".")[0])
        if (major == 0) != (self.status == "candidate"):
            raise ValueError("Pilot 0.x candidate and main >=1 freeze_candidate are separate")
        ids = [r.rule_id for r in self.rules]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("Nonempty unique stable rule IDs required")
        if set(self.document_hashes) != set(DOCUMENTS):
            raise ValueError("All three codebook/protocol document hashes required")
        if any(not re.fullmatch(r"[a-f0-9]{64}", h) for h in self.document_hashes.values()):
            raise ValueError("Byte SHA256 document hashes required")
        if set(self.example_hashes) != {"examples/semantic-boundaries.md"} or any(
            not re.fullmatch(r"[a-f0-9]{64}", h) for h in self.example_hashes.values()
        ):
            raise ValueError("Adopted artificial boundary examples require byte SHA256")
        return self


class CodebookRevision(Record):
    change_id: str
    old_definition_hash: str
    new_definition_hash: str
    old_version: str
    new_version: str
    reason: str = Field(min_length=1)
    affected_fields: list[str]
    affected_rule_ids: list[str]
    affected_pilot_units: list[str]
    impact_and_reannotation: str = Field(min_length=1)
    semantic_rules_changed: bool
    timestamp: datetime

    @model_validator(mode="after")
    def forward_only(self):
        pattern = r"\d+\.\d+\.\d+"
        if not all(re.fullmatch(pattern, v) for v in (self.old_version, self.new_version)):
            raise ValueError("Explicit semantic versions required")
        if tuple(map(int, self.new_version.split("."))) <= tuple(
            map(int, self.old_version.split("."))
        ):
            raise ValueError("Revision must increase version; preserve old artifacts")
        if self.old_definition_hash == self.new_definition_hash:
            raise ValueError("Distinct definition hashes required")
        return self


class Ambiguity(Record):
    ambiguity_id: str
    batch_id: str
    unit_id: str
    codebook_version: str
    affected_fields: list[str]
    competing_labels: list[str]
    rule_ids: list[str]
    evidence_pointer: list[str]
    issue: str = Field(min_length=1)
    disposition: Literal["existing_rule", "revision_needed", "remain_unclear"]
    resolution: str = Field(min_length=1)
    blocks_freeze: bool
    timestamp: datetime


class PathAdmission(Record):
    """Validate consistency of HUMAN supplied prerequisites, not factual validity."""

    path_id: str
    candidate_before_system_output: bool
    all_factual_premises_registered: Decision
    reference_support_sufficient: Decision
    answers_question_sufficiently: Decision
    requires_external_factual_premise: Decision
    compositional_relation_explained: Decision
    validity: Decision
    rationale: str = Field(min_length=1)
    evidence_pointer: list[str]

    @model_validator(mode="after")
    def primary_admission(self):
        if self.validity == "yes" and not (
            self.candidate_before_system_output
            and self.all_factual_premises_registered == "yes"
            and self.reference_support_sufficient == "yes"
            and self.answers_question_sufficiently == "yes"
            and self.requires_external_factual_premise == "no"
            and self.compositional_relation_explained == "yes"
            and self.evidence_pointer
        ):
            raise ValueError("Primary valid path lacks explicitly judged prerequisites")
        return self


class RequirednessCheck(Record):
    path_id: str
    fact_id: str
    removal_breaks_this_path: Decision
    required_within_path: Decision
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def path_conditional(self):
        if self.removal_breaks_this_path != self.required_within_path:
            raise ValueError("Requiredness follows removal within THIS path only")
        return self


def candidate_definition():
    """Hash authored design documents; no registry or semantic annotation produced."""
    root = Path(__file__).parent
    rules = []
    for name in DOCUMENTS:
        text = (root / name).read_text(encoding="utf-8")
        ids = re.findall(r"<!-- rule: ([A-Z0-9-]+) -->", text)
        # Table IDs are definitions; inline references are NOT duplicate rules.
        ids += re.findall(r"^\| ([A-Z0-9]+-[A-Z0-9]+-\d{3}) \|", text, re.MULTILINE)
        rules.extend(CodebookRule(rule_id=i, document=name) for i in ids)
    return CodebookDefinition(
        version=CANDIDATE_VERSION,
        status="candidate",
        document_hashes={name: file_hash(root / name) for name in DOCUMENTS},
        rules=rules,
        example_hashes={
            "examples/semantic-boundaries.md": file_hash(root / "examples/semantic-boundaries.md")
        },
        language_policy_hash=file_hash(root / "BILINGUAL-REVIEW-POLICY.md"),
    )


def definition_hash(definition):
    return digest(definition.model_dump(mode="json"))


def validate_revision_history(definitions, revisions):
    """Check explicit immutable ancestry; cannot assess human change reasons."""
    by_hash = {definition_hash(d): d for d in definitions}
    for revision in revisions:
        old, new = (
            by_hash.get(revision.old_definition_hash),
            by_hash.get(revision.new_definition_hash),
        )
        if (
            not old
            or not new
            or (old.version, new.version) != (revision.old_version, revision.new_version)
        ):
            raise ValueError("Revision ancestry missing/mismatched")
    if len(revisions) != max(len(definitions) - 1, 0):
        raise ValueError("Every version transition needs a preserved change log")
    for old, new, revision in zip(definitions, definitions[1:], revisions, strict=False):
        if (definition_hash(old), definition_hash(new)) != (
            revision.old_definition_hash,
            revision.new_definition_hash,
        ):
            raise ValueError("Disconnected revision history")
    return True
