"""Strict, separate registry/observation/provenance objects. None means missing."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Decision = Literal["yes", "no", "unclear"]
Semantic = Literal["correct", "partial", "distorted", "absent", "unclear", "NA"]
Transition = Literal["separate_records", "identity_alias", "unknown"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Question(Record):
    question_id: str
    question_text: str
    source_hash: str
    registry_version: str


class Sentence(Record):
    sentence_id: str
    title: str
    sentence_index: int = Field(ge=0)
    text: str
    text_hash: str


class Fact(Record):
    fact_id: str
    fact_text: str
    fact_type: Literal["atomic_fact", "relation_step", "answer_claim"]
    reference_basis: Literal["raw_discovery", "gold_anchor", "both"]


class SupportSet(Record):
    support_set_id: str
    fact_id: str
    evidence_sentence_ids: list[str]
    support_set_sufficient: Decision | None = None


class ReasoningPath(Record):
    path_id: str
    path_basis: Literal["gold_anchored", "raw_discovered_alternative"]
    target_answer: str
    validity: Decision | None = None


class Membership(Record):
    question_id: str
    path_id: str
    fact_id: str
    required_within_path: Decision | None = None
    support_set_ids: list[str]


class RegistryJudgment(Record):
    reviewer_id: str
    registry_phase: Literal["R1", "R2", "FINAL", "post_freeze_candidate"]
    registry_version: str
    judgment_status: Literal["independent", "adjudicated", "candidate"]
    rationale: str
    timestamp: datetime
    source_hashes: dict[str, str]


class Registry(Record):
    question: Question
    sentences: list[Sentence] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    support_sets: list[SupportSet] = Field(default_factory=list)
    paths: list[ReasoningPath] = Field(default_factory=list)
    memberships: list[Membership] = Field(default_factory=list)
    judgments: list[RegistryJudgment] = Field(default_factory=list)
    frozen_hash: str | None = None

    @model_validator(mode="after")
    def references(self):
        indexes = {}
        for name, key in [
            ("sentences", "sentence_id"),
            ("facts", "fact_id"),
            ("support_sets", "support_set_id"),
            ("paths", "path_id"),
        ]:
            values = [getattr(item, key) for item in getattr(self, name)]
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate {name} ID")
            indexes[name] = set(values)
        sets = {s.support_set_id: s for s in self.support_sets}
        for support in self.support_sets:
            if support.fact_id not in indexes["facts"] or not support.evidence_sentence_ids:
                raise ValueError("Support set needs a registered fact and nonempty sentences")
            if not set(support.evidence_sentence_ids) <= indexes["sentences"]:
                raise ValueError("Unknown support sentence")
        seen = set()
        for member in self.memberships:
            key = (member.path_id, member.fact_id)
            if key in seen:
                raise ValueError("Duplicate path-fact membership")
            seen.add(key)
            if (
                member.question_id != self.question.question_id
                or member.path_id not in indexes["paths"]
                or member.fact_id not in indexes["facts"]
            ):
                raise ValueError("Invalid membership reference")
            if not member.support_set_ids:
                raise ValueError("Membership needs candidate support sets")
            for sid in member.support_set_ids:
                if sid not in sets or sets[sid].fact_id != member.fact_id:
                    raise ValueError("Support-set/fact mismatch")
        if self.frozen_hash:
            from review_v3.storage import digest

            if digest(self.model_dump(mode="json", exclude={"frozen_hash"})) != self.frozen_hash:
                raise ValueError("Frozen registry hash mismatch")
        return self


class Common(Record):
    question_id: str
    path_id: str | None = None
    fact_id: str | None = None
    worker_id: str | None = None
    arm: str | None = None
    route: str | None = None
    reviewer_id: str | None = None
    codebook_version: str | None = None
    applicability: Literal["applicable", "not_applicable", "unclear"] | None = None
    applicability_reason: str | None = None
    evidence_pointer: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] | None = None
    rationale: str | None = None
    translation_issue: Literal["none", "ambiguous", "mismatch", "unclear"] | None = None
    translation_unit_pointers: list[str] = Field(default_factory=list)
    translation_visible_pairs_hash: str | None = None
    record_availability: (
        Literal["available", "missing", "unreadable", "mapping_unresolved"] | None
    ) = None

    @model_validator(mode="after")
    def na_is_structural(self):
        state = getattr(self, "state", None)
        if state == "NA" and self.applicability != "not_applicable":
            raise ValueError("NA requires explicit structural non-applicability")
        if self.applicability == "not_applicable" and state not in (None, "NA"):
            raise ValueError("Non-applicable cannot carry a semantic state")
        return self


class S0(Common):
    state: Literal["complete", "partial", "absent", "unclear"] | None = None


class S1(Common):
    state: Literal["complete", "partial", "none", "unclear"] | None = None
    intended_sentence_ids: list[str] | None = None
    actual_sentence_ids: list[str] | None = None
    intended_partition_pointer: str | None = None
    actual_serialized_input_pointer: str | None = None


class S2(Common):
    state: Semantic | None = None


class S3(Common):
    publication_transition_type: Transition | None = None
    state: Literal["retained", "partial_loss", "distorted", "lost", "unclear", "NA"] | None = None
    artifact_fact_state: Semantic | None = None
    before_pointer: str | None = None
    after_pointer: str | None = None

    @model_validator(mode="after")
    def alias(self):
        if self.publication_transition_type == "identity_alias" and self.state is not None:
            if (
                self.state != "NA"
                or self.applicability_reason != "no_separate_transition"
                or self.applicability != "not_applicable"
            ):
                raise ValueError("identity_alias requires S3=NA / no_separate_transition")
        return self


class S4(Common):
    state: Semantic | None = None
    artifact_state: Semantic | None = None
    supplementary_state: Semantic | None = None
    machine_payload_match: Literal["match", "mismatch", "unclear", "NA"] | None = None
    mismatch_fact_related: bool | None = None
    received_via: (
        Literal["artifact", "supplementary_evidence", "both", "neither", "unclear"] | None
    ) = None
    expected_hash: str | None = None
    actual_hash: str | None = None
    normalization_rule: str | None = None


class S5a(Common):
    state: Literal["reflected", "contradicted", "not_asserted", "unclear", "NA"] | None = None


class S5b(Common):
    state: (
        Literal["fully_supported", "partially_supported", "unsupported", "unclear", "NA"] | None
    ) = None


class SharedLineage(Record):
    fact_id: str
    worker_id: str
    s0: S0
    s1: S1
    s2: S2
    s3: S3


class ArmLabels(Record):
    # Keys of s4: fact_id|worker_id; s5a: fact_id; s5b: registered path_id.
    s4: dict[str, S4] = Field(default_factory=dict)
    s5a: dict[str, S5a] = Field(default_factory=dict)
    s5b: dict[str, S5b] = Field(default_factory=dict)


class QuestionLabels(Record):
    registry: Registry
    shared: list[SharedLineage] = Field(default_factory=list)
    arms: dict[str, ArmLabels] = Field(default_factory=dict)
    label_origin: Literal["independent", "adjudicated", "synthetic"]

    @model_validator(mode="after")
    def unique_shared(self):
        keys = [(s.fact_id, s.worker_id) for s in self.shared]
        if len(keys) != len(set(keys)):
            raise ValueError("Shared S0-S3 must not be duplicated per arm")
        qid = self.registry.question.question_id
        facts = {f.fact_id for f in self.registry.facts}
        paths = {p.path_id for p in self.registry.paths}
        for shared in self.shared:
            if shared.fact_id not in facts:
                raise ValueError("Unknown shared fact")
            for stage in (shared.s0, shared.s1, shared.s2, shared.s3):
                worker_matches = (
                    stage.worker_id == shared.worker_id
                    or isinstance(stage, S0)
                    and stage.worker_id is None
                )
                if (
                    stage.question_id != qid
                    or stage.fact_id != shared.fact_id
                    or not worker_matches
                    or stage.arm is not None
                ):
                    raise ValueError("Shared stage provenance mismatch")
        for arm_id, arm in self.arms.items():
            for key, stage in arm.s4.items():
                if key not in {f"{f}|{w}" for f, w in keys}:
                    raise ValueError("S4 needs linked shared fact/Worker")
                if (
                    stage.question_id != qid
                    or stage.arm != arm_id
                    or key != f"{stage.fact_id}|{stage.worker_id}"
                ):
                    raise ValueError("S4 provenance mismatch")
            for collection, allowed in [(arm.s5a, facts), (arm.s5b, paths)]:
                for key, stage in collection.items():
                    if (
                        key not in allowed
                        or stage.question_id != qid
                        or stage.arm != arm_id
                        or (isinstance(stage, S5a) and stage.fact_id != key)
                        or (isinstance(stage, S5b) and stage.path_id != key)
                    ):
                        raise ValueError("S5 provenance mismatch")
        return self


class Scope(Record):
    included_case_ids: list[str]
    iaa_eligible_case_ids: list[str]
    descriptive_only_case_ids: list[str]
    decision_reason: str
    prior_exposure_by_reviewer: dict[str, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def subsets(self):
        included = set(self.included_case_ids)
        if len(included) != len(self.included_case_ids):
            raise ValueError("Duplicate included cases")
        iaa, descriptive = set(self.iaa_eligible_case_ids), set(self.descriptive_only_case_ids)
        if not iaa <= included or not descriptive <= included or iaa & descriptive:
            raise ValueError("Invalid IAA/descriptive scope")
        if any(iaa & set(ids) for ids in self.prior_exposure_by_reviewer.values()):
            raise ValueError("Previously discussed cases cannot silently enter independent IAA")
        return self


class Adjudication(Record):
    unit_id: str
    field: str
    reviewer1_label: str | None
    reviewer2_label: str | None
    adjudicated_label: str | None
    reason: str
    guideline_rule: str
    adjudicator: str
    timestamp: datetime
    codebook_version: str
    evidence_pointer: list[str] = Field(default_factory=list)
    resolution_status: Literal["resolved", "unresolved", "missing_record"] | None = None

    @model_validator(mode="after")
    def unresolved_is_not_forced(self):
        if self.resolution_status == "unresolved" and self.adjudicated_label != "unclear":
            raise ValueError("Unresolved semantic judgment must remain unclear")
        if self.resolution_status == "missing_record" and self.adjudicated_label is not None:
            raise ValueError("Missing record cannot be converted to a semantic judgment")
        return self


STAGE_MODELS = {"S0": S0, "S1": S1, "S2": S2, "S3": S3, "S4": S4, "S5a": S5a, "S5b": S5b}
