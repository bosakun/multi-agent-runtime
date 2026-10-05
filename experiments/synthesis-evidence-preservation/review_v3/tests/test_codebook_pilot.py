"""Invented metadata/labels ONLY. No real pilot, review or semantic inference."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from review_v3.adjudication import save_adjudication
from review_v3.calibration import (
    EDGE_CASES,
    PilotBatch,
    PilotClearance,
    PilotSelection,
    calibration_stop_candidate,
)
from review_v3.codebook import (
    CodebookDefinition,
    CodebookRevision,
    PathAdmission,
    RequirednessCheck,
    candidate_definition,
    definition_hash,
    validate_revision_history,
)
from review_v3.manifest import freeze_candidate
from review_v3.metrics import observed_state
from review_v3.schema import S1, S2, S3, Adjudication
from review_v3.storage import ReviewStore, digest, file_hash, read
from review_v3.transparency import SIGNOFF_ITEMS, MainReviewSignoff
from review_v3.workflow import Workflow
from synthetic import workflow

TIME = datetime(2020, 1, 1, tzinfo=UTC)


def batch(**updates):
    candidate = candidate_definition()
    values = dict(
        batch_id="synthetic-batch",
        namespace="pilot_stage",
        codebook_version=candidate.version,
        codebook_definition_hash=definition_hash(candidate),
        protocol_hash=candidate.document_hashes["PILOT-PROTOCOL.md"],
        packet_hashes={"invented": "synthetic-hash"},
        case_ids=["invented-case"],
        independent_ballot_locks={"synthetic-r1": "hash-r1", "synthetic-r2": "hash-r2"},
        independent_locks_at=TIME,
        inspected_at=TIME + timedelta(hours=1),
        adjudication_log_hash="synthetic-adj",
        ambiguity_log_hash="synthetic-ambiguity",
        covered_edge_cases=list(EDGE_CASES),
        new_guideline_rules=0,
        major_disagreements_resolvable=True,
        unresolved_ambiguities_documented=True,
        unresolved_blocker_ids=[],
    )
    return PilotBatch(**{**values, **updates})


def clearance(**updates):
    values = dict(
        batches=[batch()],
        final_pilot_definition=candidate_definition(),
        unresolved_ambiguity_disposition="Invented metadata; not human review",
        human_signoff="SYNTHETIC ONLY",
        signed_at=TIME + timedelta(hours=2),
    )
    return PilotClearance(**{**values, **updates})


def definition_v1():
    return CodebookDefinition.model_validate(
        {**candidate_definition().model_dump(), "version": "1.0.0", "status": "freeze_candidate"}
    )


def main_signoff():
    definition = definition_v1()
    return MainReviewSignoff(
        version="synthetic-v1", confirmed_items=list(SIGNOFF_ITEMS),
        codebook_version=definition.version,
        codebook_definition_hash=definition_hash(definition),
        translation_policy_version="synthetic-policy",
        translation_policy_hash=definition.language_policy_hash,
        reviewers=[dict(
            reviewer_id=r, relationship_to_author=["none"],
            involvement_in_implementation=False, involvement_in_experiment_design=False,
            prior_result_exposure=False, prior_case_exposure=[], disclosure_notes="Synthetic only",
        ) for r in ("synthetic-r1", "synthetic-r2")],
        adjudication_policy_version="synthetic-policy",
        adjudication_policy_hash=definition.document_hashes["ADJUDICATION-RULES.md"],
        adjudicator_contexts=[dict(
            adjudicator_id="synthetic-only", prior_result_exposure=True, prior_case_exposure=[],
            disclosure_notes="Invented known-results limitation",
            allocation_blinded_where_feasible=True,
        )],
        study1_main_n=30,
        study1_scope=dict(
            included_case_ids=[f"invented-{i}" for i in range(30)],
            iaa_eligible_case_ids=[f"invented-{i}" for i in range(30)],
            descriptive_only_case_ids=[],
            decision_reason="Synthetic count test, not real scope decision",
        ),
        human_signoff="SYNTHETIC ONLY", signed_at=TIME + timedelta(hours=3),
    )


def test_codebook_schema_version_and_unique_rule_ids():
    candidate = candidate_definition()
    assert candidate.version == "0.3.0" and candidate.status == "candidate"
    ids = [r.rule_id for r in candidate.rules]
    assert len(ids) == len(set(ids)) and "ADJ-UNCLEAR-001" in ids
    assert "S3-ALIAS-001" in ids and "PATH-REQUIRED-001" in ids
    assert CodebookDefinition.model_validate_json(candidate.model_dump_json()) == candidate
    with pytest.raises(ValidationError):
        CodebookDefinition(**{**candidate.model_dump(), "version": "1.0.0"})
    with pytest.raises(ValidationError):
        CodebookDefinition(**{**candidate.model_dump(), "rules": candidate.rules * 2})


@pytest.mark.parametrize("state", ["partial", "distorted", "absent", "unclear"])
def test_artificial_semantic_categories_not_collapsed(state):
    # Expected categories are AUTHOR-SUPPLIED fixture values, not an NLP classifier.
    annotation = S2(question_id="invented", state=state, applicability="applicable")
    assert observed_state(annotation) == state


def test_missing_vs_unclear_including_s1_missing_display():
    ambiguous = S1(
        question_id="invented",
        state="unclear",
        applicability="applicable",
        record_availability="mapping_unresolved",
    )
    missing = S1(
        question_id="invented",
        state="unclear",
        applicability="applicable",
        record_availability="missing",
    )
    assert observed_state(ambiguous) == "unclear"
    assert observed_state(missing) is None
    assert observed_state(S2(question_id="invented")) is None


def test_alias_remains_structural_na():
    record = S3(
        question_id="invented",
        publication_transition_type="identity_alias",
        state="NA",
        applicability="not_applicable",
        applicability_reason="no_separate_transition",
    )
    assert observed_state(record) == "NA"


def admission(**updates):
    return PathAdmission(
        **{
            "path_id": "invented-alternative",
            "candidate_before_system_output": True,
            "all_factual_premises_registered": "yes",
            "reference_support_sufficient": "yes",
            "answers_question_sufficiently": "yes",
            "requires_external_factual_premise": "no",
            "compositional_relation_explained": "yes",
            "validity": "yes",
            "rationale": "Invented prerequisites supplied, not discovered",
            "evidence_pointer": ["s1"],
            **updates,
        }
    )


def test_alternative_path_human_supplied_admission():
    assert admission().validity == "yes"
    with pytest.raises(ValidationError):
        admission(candidate_before_system_output=False)
    with pytest.raises(ValidationError):
        admission(reference_support_sufficient="unclear")


def test_invalid_external_premise_path_not_primary_valid():
    assert admission(requires_external_factual_premise="yes", validity="no").validity == "no"
    with pytest.raises(ValidationError):
        admission(requires_external_factual_premise="yes")


@pytest.mark.parametrize("decision", ["yes", "no", "unclear"])
def test_requiredness_is_this_path_conditional(decision):
    supplied = RequirednessCheck(
        path_id="p1",
        fact_id="f1",
        removal_breaks_this_path=decision,
        required_within_path=decision,
        rationale="Invented THIS path",
    )
    assert supplied.required_within_path == decision
    with pytest.raises(ValidationError):
        RequirednessCheck(
            **{
                **supplied.model_dump(),
                "required_within_path": "no" if decision == "yes" else "yes",
            }
        )


def test_batch_requires_independent_locks_before_inspection():
    assert batch().namespace == "pilot_stage"
    with pytest.raises(ValidationError):
        batch(independent_ballot_locks={"one": "hash"})
    with pytest.raises(ValidationError):
        batch(inspected_at=TIME - timedelta(hours=1))


@pytest.mark.parametrize(
    "updates",
    [
        {"new_guideline_rules": 1},
        {"major_disagreements_resolvable": False},
        {"unresolved_ambiguities_documented": False},
        {"unresolved_blocker_ids": ["blocker"]},
    ],
)
def test_stop_criterion_all_conditions_required(updates):
    b = batch(**updates)
    assert not calibration_stop_candidate([b], EDGE_CASES)
    with pytest.raises(ValidationError):
        clearance(batches=[b])


def test_stop_requires_coverage_and_adopted_version():
    assert calibration_stop_candidate([batch()], EDGE_CASES)
    assert not calibration_stop_candidate([batch()], ["correct"])
    assert clearance().human_signoff == "SYNTHETIC ONLY"
    with pytest.raises(ValidationError):
        clearance(batches=[batch(codebook_definition_hash="old-version")])
    with pytest.raises(ValidationError):
        clearance(human_signoff="")


def test_selection_is_external_unselected_by_tooling():
    values = dict(
        selection_rule="Invented deterministic method",
        pool_hash="invented",
        method="fixed-id-order",
        selected_external_case_ids=["outside"],
        excluded_main30_ids=["main"],
        excluded_study2_main_ids=["main"],
        excluded_study2_smoke_ids=["smoke"],
        prior_exposure_by_reviewer={},
        result_aware_selection=False,
        fixed_at=TIME,
    )
    assert PilotSelection(**values).seed is None
    with pytest.raises(ValidationError):
        PilotSelection(**{**values, "selected_external_case_ids": ["main"]})
    with pytest.raises(ValidationError):
        PilotSelection(**{**values, "result_aware_selection": True})


def test_revision_history_preserves_versions():
    old, new = candidate_definition(), definition_v1()
    revision = CodebookRevision(
        change_id="invented-change",
        old_definition_hash=definition_hash(old),
        new_definition_hash=definition_hash(new),
        old_version=old.version,
        new_version=new.version,
        reason="Synthetic promotion only",
        affected_fields=[],
        affected_rule_ids=[],
        affected_pilot_units=[],
        impact_and_reannotation="No invented semantic rules changed",
        semantic_rules_changed=False,
        timestamp=TIME,
    )
    assert validate_revision_history([old, new], [revision])
    assert old.version == "0.3.0"
    with pytest.raises(ValueError):
        validate_revision_history([old, new], [])
    with pytest.raises(ValidationError):
        CodebookRevision(**{**revision.model_dump(), "new_version": "0.1.0"})


def unfrozen_main():
    # Invented registry/locks, test the non-synthetic authorization branch only.
    return workflow().model_copy(
        update={
            "synthetic": False,
            "codebook_hash": None,
            "codebook_version": None,
            "calibration_completed": False,
        }
    )


def test_main_freeze_requires_signed_clearance_and_human_signoff():
    flow = unfrozen_main()
    with pytest.raises(ValueError):
        flow.authorize("S1", "synthetic-r1")
    for signoff, clear in ((None, clearance()), ("synthetic", None)):
        with pytest.raises(ValueError):
            flow.freeze_codebook("1.0.0", definition_v1().model_dump(), True, signoff, clear)
    sealed = flow.freeze_codebook(
        "1.0.0", definition_v1().model_dump(), True, "SYNTHETIC ONLY",
        clearance(main_signoff=main_signoff())
    )
    sealed.authorize("S1", "synthetic-r1")
    assert sealed.pilot_clearance_hash and sealed.codebook_human_signoff


def test_changed_rules_after_pilot_cannot_freeze():
    changed = definition_v1().model_dump()
    changed["document_hashes"]["CODEBOOK.md"] = "b" * 64
    with pytest.raises(ValueError):
        unfrozen_main().freeze_codebook("1.0.0", changed, True, "synthetic", clearance())


def test_pilot_candidate_does_not_require_main_freeze_or_promote():
    flow = unfrozen_main().model_copy(update={"review_mode": "pilot"})
    with pytest.raises(ValueError):
        flow.authorize("S1", "synthetic-r1")
    pilot = flow.authorize_pilot_candidate(candidate_definition(), "SYNTHETIC ONLY")
    pilot.authorize("S1", "synthetic-r1")
    assert not pilot.calibration_completed and pilot.codebook_version == "0.3.0"
    with pytest.raises(ValueError):
        pilot.freeze_codebook("1.0.0", {}, True, "synthetic", clearance())
    with pytest.raises(ValueError):
        Workflow(review_mode="pilot", reviewer_ids=("synthetic-1", "synthetic-2")).authorize(
            "R1", "synthetic-1"
        )


def test_unresolved_adjudication_separate_and_original_labels_immutable(tmp_path):
    flow = workflow()
    store = ReviewStore(tmp_path)
    original = {"invented": "partial"}
    store.append("stage_labels_reviewer1", "invented", "v1", original)
    original_hash = file_hash(tmp_path / "stage_labels_reviewer1/invented/v1.json")
    for reviewer in flow.reviewer_ids:
        for phase in ("S1", "S2", "S3", "S4", "S5"):
            flow = flow.lock(reviewer, phase, {"fixture": phase}, "synthetic-v1")
    record = Adjudication(
        unit_id="invented",
        field="S2",
        reviewer1_label="partial",
        reviewer2_label="distorted",
        adjudicated_label="unclear",
        reason="Artificial unresolved boundary",
        guideline_rule="ADJ-UNCLEAR-001",
        evidence_pointer=["invented-output:1"],
        adjudicator="synthetic-only",
        timestamp=TIME,
        codebook_version="synthetic-v1",
        resolution_status="unresolved",
    )
    save_adjudication(store, flow, "invented", "v1", [record.model_dump()], {"S2": "unclear"})
    assert file_hash(tmp_path / "stage_labels_reviewer1/invented/v1.json") == original_hash
    assert read(tmp_path / "final_adjudicated_labels/invented/v1.json")["S2"] == "unclear"
    with pytest.raises(ValidationError):
        Adjudication(**{**record.model_dump(), "adjudicated_label": "correct"})


def test_real_path_adjudication_requires_rule_pointer_and_disposition(tmp_path):
    flow = workflow()
    for reviewer in flow.reviewer_ids:
        for phase in ("S1", "S2", "S3", "S4", "S5"):
            flow = flow.lock(reviewer, phase, {"fixture": phase}, "synthetic-v1")
    flow = flow.model_copy(update={"synthetic": False, "codebook_rule_ids": ["ADJ-UNCLEAR-001"]})
    record = Adjudication(
        unit_id="invented",
        field="S2",
        reviewer1_label="partial",
        reviewer2_label="distorted",
        adjudicated_label="unclear",
        reason="Artificial",
        guideline_rule="unknown-rule",
        adjudicator="invented",
        timestamp=TIME,
        codebook_version="synthetic-v1",
    )
    with pytest.raises(ValueError):
        save_adjudication(ReviewStore(tmp_path), flow, "invented", "v1", [record.model_dump()], {})


def test_candidate_remains_unstarted_no_labels_or_real_packets():
    result = freeze_candidate()
    assert result["codebook_candidate"]["version"] == "0.3.0"
    assert result["pilot_batches_completed"] == result["human_labels"] == 0
    assert result["pilot_clearance"] is None and result["human_signoff"] is None
    assert not result["final_frozen"]
    assert digest(result["codebook_candidate"]) == definition_hash(candidate_definition())


def test_pilot_batches_cannot_pool_duplicate_or_changed_reviewers():
    first = batch()
    second = batch(
        batch_id="second",
        independent_locks_at=TIME + timedelta(hours=2),
        inspected_at=TIME + timedelta(hours=3),
    )
    assert clearance(batches=[first, second], signed_at=TIME + timedelta(hours=4))
    with pytest.raises(ValidationError):
        clearance(batches=[first, first])
    switched = second.model_copy(
        update={"independent_ballot_locks": {"third": "h3", "fourth": "h4"}}
    )
    with pytest.raises(ValidationError):
        clearance(batches=[first, switched], signed_at=TIME + timedelta(hours=4))


def test_new_cli_schema_metadata_only(capsys):
    from review_v3.run import main

    assert main(["codebook-candidate"]) == 0
    assert '"version": "0.3.0"' in capsys.readouterr().out
    for kind in ("codebook", "pilot-batch", "pilot-clearance", "path-admission", "ambiguity"):
        assert main(["schema", kind]) == 0
        assert "properties" in capsys.readouterr().out
