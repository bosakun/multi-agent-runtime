"""Future external cases and local synthetic vignettes live outside main scope."""

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from review_v3.codebook import CodebookDefinition, definition_hash
from review_v3.schema import Record
from review_v3.storage import digest
from review_v3.transparency import MainReviewSignoff

EDGE_CASES = (
    "correct",
    "partial",
    "distorted",
    "absent",
    "unclear",
    "alternative_path",
    "identity_alias",
    "unknown_transition",
    "separate_publication_record",
    "supplementary_evidence_route",
    "upstream_failure_cascade",
    "complete_path_unsupported_answer",
)


class CalibrationCase(Record):
    case_id: str
    namespace: Literal["external_hotpotqa", "synthetic_vignette"]
    source_hashes: dict[str, str]
    edge_cases: list[str]
    synthetic: bool

    @model_validator(mode="after")
    def coherent_namespace(self):
        if self.synthetic != (self.namespace == "synthetic_vignette"):
            raise ValueError("Synthetic and external material must be distinguished")
        if not set(self.edge_cases) <= set(EDGE_CASES):
            raise ValueError("Unknown calibration edge case")
        return self


class PilotSelection(Record):
    # Future HUMAN input; does not select cases, seed, sample size or reviewers.
    selection_rule: str = Field(min_length=1)
    pool_hash: str
    method: str
    seed: int | None = None
    selected_external_case_ids: list[str]
    excluded_main30_ids: list[str]
    excluded_study2_main_ids: list[str]
    excluded_study2_smoke_ids: list[str]
    prior_exposure_by_reviewer: dict[str, list[str]]
    result_aware_selection: Literal[False]
    fixed_at: datetime

    @model_validator(mode="after")
    def outside_main(self):
        selected = set(self.selected_external_case_ids)
        excluded = set(
            self.excluded_main30_ids
            + self.excluded_study2_main_ids
            + self.excluded_study2_smoke_ids
        )
        if len(selected) != len(self.selected_external_case_ids) or selected & excluded:
            raise ValueError("Pilot external cases must be unique and outside study scopes")
        return self


class PilotBatch(Record):
    batch_id: str
    namespace: Literal["pilot_registry", "pilot_stage"]
    codebook_version: str
    codebook_definition_hash: str
    protocol_hash: str
    packet_hashes: dict[str, str]
    case_ids: list[str]
    independent_ballot_locks: dict[str, str]
    independent_locks_at: datetime
    inspected_at: datetime
    adjudication_log_hash: str
    ambiguity_log_hash: str
    covered_edge_cases: list[str]
    new_guideline_rules: int = Field(ge=0)
    major_disagreements_resolvable: bool
    unresolved_ambiguities_documented: bool
    unresolved_blocker_ids: list[str]

    @model_validator(mode="after")
    def independent(self):
        if len(self.independent_ballot_locks) != 2 or not all(self.independent_ballot_locks):
            raise ValueError("Exactly two explicitly supplied independent locks required")
        hashes = list(self.independent_ballot_locks.values())
        if not all(hashes) or len(set(hashes)) != 2:
            raise ValueError("Distinct provenance-bearing independent ballots required")
        if self.inspected_at < self.independent_locks_at:
            raise ValueError("Disagreement inspection only after both independent locks")
        if not self.packet_hashes or not self.case_ids:
            raise ValueError("Batch must reference its locked materials/cases")
        if not set(self.covered_edge_cases) <= set(EDGE_CASES):
            raise ValueError("Unknown edge-case coverage")
        return self


class PilotClearance(Record):
    # Human-signed evidence of pilot completion; no live instance created here.
    batches: list[PilotBatch]
    final_pilot_definition: CodebookDefinition
    unresolved_ambiguity_disposition: str = Field(min_length=1)
    human_signoff: str = Field(min_length=1)
    signed_at: datetime
    main_signoff: MainReviewSignoff | None = None

    @model_validator(mode="after")
    def stable(self):
        if self.final_pilot_definition.status != "candidate":
            raise ValueError("Clearance must identify the actual 0.x pilot definition")
        final_hash = definition_hash(self.final_pilot_definition)
        if len({b.batch_id for b in self.batches}) != len(self.batches):
            raise ValueError("Pilot batch IDs must be unique")
        if any(
            a.inspected_at > b.independent_locks_at
            for a, b in zip(self.batches, self.batches[1:], strict=False)
        ):
            raise ValueError("Next independent batch follows previous inspection/revision")
        # Coverage of the adoption version, not incompatible old rules pooled together.
        adopted = [b for b in self.batches if b.codebook_definition_hash == final_hash]
        if not adopted or self.batches[-1] not in adopted:
            raise ValueError("Last pilot batch must match the adopted candidate")
        if any(b.codebook_version != self.final_pilot_definition.version for b in adopted):
            raise ValueError("Pilot codebook version/hash mismatch")
        if any(
            set(b.independent_ballot_locks) != set(adopted[-1].independent_ballot_locks)
            for b in adopted
        ):
            raise ValueError("Adopted pilot batches must preserve the same two reviewers")
        if any(
            b.protocol_hash != self.final_pilot_definition.document_hashes["PILOT-PROTOCOL.md"]
            for b in adopted
        ):
            raise ValueError("Pilot protocol hash mismatch")
        covered = {e for b in adopted for e in b.covered_edge_cases}
        if not calibration_stop_candidate(adopted, covered):
            raise ValueError("Pilot stability checklist not met")
        if self.signed_at < self.batches[-1].inspected_at:
            raise ValueError("Human sign-off must follow last batch inspection")
        return self

    @property
    def content_hash(self):
        return digest(self.model_dump(mode="json"))


def calibration_stop_candidate(batches, covered_edge_cases):
    # Legacy dicts give only a preliminary coverage summary (not freeze authorization).
    if batches and isinstance(batches[-1], PilotBatch):
        final = batches[-1]
        return bool(
            final.new_guideline_rules == 0
            and final.major_disagreements_resolvable
            and final.unresolved_ambiguities_documented
            and not final.unresolved_blocker_ids
            and set(EDGE_CASES) <= set(covered_edge_cases)
        )
    return bool(
        batches
        and batches[-1]["new_guideline_rules"] == 0
        and set(EDGE_CASES) <= set(covered_edge_cases)
    )
