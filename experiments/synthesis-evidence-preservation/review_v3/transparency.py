"""Author-only human declarations. No assignment, annotation or auto-clearance."""

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from review_v3.schema import Record, Scope
from review_v3.storage import digest


class ReviewerProfile(Record):
    reviewer_id: str = Field(min_length=1)
    relationship_to_author: list[
        Literal[
            "none", "family", "academic_advisor", "friend_or_peer",
            "collaborator", "other", "undisclosed",
        ]
    ] = Field(min_length=1)
    involvement_in_implementation: bool
    involvement_in_experiment_design: bool
    prior_result_exposure: bool
    prior_case_exposure: list[str]
    disclosure_notes: str = Field(min_length=1)

    @model_validator(mode="after")
    def relationships(self):
        values = self.relationship_to_author
        if len(set(values)) != len(values) or (
            len(values) > 1 and ({"none", "undisclosed"} & set(values))
        ):
            raise ValueError("Do not mix no/undisclosed relationship with declared relationships")
        return self


class AdjudicatorContext(Record):
    adjudicator_id: str = Field(min_length=1)
    prior_result_exposure: bool
    prior_case_exposure: list[str]
    disclosure_notes: str = Field(min_length=1)
    allocation_blinded_where_feasible: Literal[True]


SIGNOFF_ITEMS = (
    "critical_edge_cases_actually_reviewed", "final_batch_new_rules_zero",
    "unresolved_ambiguities_recorded", "no_freeze_blockers",
    "final_codebook_version_hash_checked", "translation_policy_version_hash_checked",
    "reviewer_composition_checked", "adjudication_policy_checked",
    "main_scope_checked", "main_iaa_scope_checked",
)


class MainReviewSignoff(Record):
    version: str = Field(min_length=1)
    confirmed_items: list[str]
    codebook_version: str
    codebook_definition_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    translation_policy_version: str = Field(min_length=1)
    translation_policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewers: list[ReviewerProfile] = Field(min_length=2, max_length=2)
    adjudication_policy_version: str = Field(min_length=1)
    adjudication_policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    third_adjudicator_used: bool
    adjudicator_contexts: list[AdjudicatorContext]
    study1_main_n: Literal[30, 28]
    study1_scope: Scope
    human_signoff: str = Field(min_length=1)
    signed_at: datetime

    @model_validator(mode="after")
    def explicit_confirmation(self):
        if set(self.confirmed_items) != set(SIGNOFF_ITEMS) or len(self.confirmed_items) != 10:
            raise ValueError("All ten HUMAN confirmations required; no automatic completion")
        if self.third_adjudicator_used != bool(self.adjudicator_contexts):
            raise ValueError("Third-adjudicator policy must match its optional context records")
        ids = [r.reviewer_id for r in self.reviewers]
        if len(set(ids)) != 2:
            raise ValueError("Two distinct pseudonymous reviewers required")
        if any(r.involvement_in_implementation or r.involvement_in_experiment_design
               for r in self.reviewers):
            raise ValueError("Retain non-implementer/non-experiment-designer reviewer policy")
        if len(self.study1_scope.included_case_ids) != self.study1_main_n:
            raise ValueError("Human-selected 30/28 scope must match its inclusion manifest")
        if not self.study1_scope.decision_reason or not self.study1_scope.iaa_eligible_case_ids:
            raise ValueError("Explicit main and IAA scope decisions required")
        return self

    @property
    def content_hash(self):
        return digest(self.model_dump(mode="json"))
