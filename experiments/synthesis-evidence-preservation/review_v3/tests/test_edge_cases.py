import pytest
from pydantic import ValidationError
from review_v3.assembly import assemble_question
from review_v3.failures import derive, derive_question
from review_v3.logic import Outcome, conjunction, disjunction
from review_v3.metrics import complete_received_paths, downstream_outcome, metric_units
from review_v3.schema import S1, QuestionLabels, Registry
from review_v3.storage import exclusive, snapshot, verify_snapshot
from review_v3.workflow import Workflow, registry_digest
from synthetic import changed, labels


def alternative_path(data):
    value = data.model_dump(mode="json")
    registry = value["registry"]
    registry["frozen_hash"] = None
    registry["paths"].append(
        {
            "path_id": "p2",
            "path_basis": "raw_discovered_alternative",
            "target_answer": "Invented",
            "validity": "yes",
        }
    )
    registry["memberships"].append({**registry["memberships"][0], "path_id": "p2"})
    registry["frozen_hash"] = registry_digest(Registry.model_validate(registry))
    for arm in value["arms"].values():
        arm["s5b"]["p2"] = {**arm["s5b"]["p1"], "path_id": "p2"}
    return QuestionLabels.model_validate(value)


def test_received_alternative_support_prevents_false_downstream_failure():
    data = alternative_path(changed(labels(), "s5b", "unsupported"))
    value = data.model_dump(mode="json")
    value["arms"]["arm-x"]["s5b"]["p2"]["state"] = "fully_supported"
    data = QuestionLabels.model_validate(value)
    assert complete_received_paths(data, data.arms["arm-x"]) == ["p1", "p2"]
    assert downstream_outcome(data, data.arms["arm-x"]) == Outcome.SUCCESS
    assert not derive(data, "arm-x")["events"]


def test_unreceived_alternative_not_support_success():
    data = alternative_path(labels())
    data = changed(data, "s4", "absent", artifact_state="absent")
    assert not complete_received_paths(data, data.arms["arm-x"])
    assert downstream_outcome(data, data.arms["arm-x"]) == Outcome.INELIGIBLE


def test_shared_failure_events_count_once_across_arms():
    data = changed(labels(), "s2", "absent")
    result = derive_question(data)
    assert result["failure_count"] == 1
    assert all(r["failure_count"] == 1 for r in result["by_arm"].values())


def test_unknown_prior_publication_first_is_undetermined():
    data = changed(labels(transition="unknown"), "s5b", "unsupported")
    assert derive(data, "arm-x")["first_observable_failure_stage"] == "undetermined"


def test_distinct_observable_failures_not_category():
    data = changed(labels(), "s2", "distorted")
    data = changed(data, "s5b", "unsupported")
    result = derive(data, "arm-x")
    assert result["failure_count"] == 2 and result["has_multiple_distinct_observable_failures"]
    assert result["first_observable_failure_stage"] == "S2"


def test_missing_input_record_not_access_none():
    annotation = S1(question_id="synthetic", actual_sentence_ids=None)
    assert annotation.state is None
    data = changed(labels(), "s1", None)
    assert metric_units(data)["access_coverage"][0].outcome == Outcome.MISSING


def test_unknown_versus_missing_transition():
    data = changed(labels(transition="unknown"), "s3", None, publication_transition_type=None)
    assert metric_units(data)["fact_end_to_end_survival:arm-x"][0].outcome == Outcome.MISSING


def test_path_missing_no_vacuous_success():
    assert conjunction([]) == Outcome.MISSING
    assert conjunction([Outcome.SUCCESS, Outcome.MISSING]) == Outcome.MISSING
    assert disjunction([Outcome.FAILURE, Outcome.NON_IDENTIFIABLE]) == Outcome.NON_IDENTIFIABLE


def test_workflow_reload_cannot_skip_or_forge_locks():
    with pytest.raises(ValidationError):
        Workflow(state="R2_OPEN", reviewer_ids=("r1", "r2"))
    with pytest.raises(ValidationError):
        Workflow(reviewer_ids=("same", "same"))


def test_preservation_tampering_and_missing_are_not_success(tmp_path):
    exclusive(tmp_path / "old.json", {"historical": True})
    before = snapshot(tmp_path, ["old.json"])
    assert verify_snapshot(tmp_path, before)["passed"]
    assert not verify_snapshot(tmp_path, {"old.json": "different"})["passed"]
    assert verify_snapshot(tmp_path, {"missing.json": "x"})["missing"] == ["missing.json"]


def test_assembly_blank_shared_stages_once_no_human_label_creation():
    data = labels()
    assembled = assemble_question(data.registry, ["worker-x"], list(data.arms), [], "synthetic")
    assert len(assembled.shared) == 2 and len(assembled.arms) == 3
    assert all(row.s2.state is None for row in assembled.shared)
    assert all(not arm.s4 for arm in assembled.arms.values())
    assert metric_units(assembled)["access_coverage"][0].outcome == Outcome.MISSING


def test_missing_applicability_not_evaluable():
    data = changed(labels(), "s2", "correct", applicability=None)
    assert metric_units(data)["worker_public_expression_survival"][0].outcome == Outcome.MISSING


def test_no_tooling_writes_into_old_study_namespace():
    from pathlib import Path

    from review_v3.storage import ensure_local_output

    study = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError):
        ensure_local_output(study / "reports/review-kits/new-v3.json")
    ensure_local_output(study / "review_v3/local/session.json")


def test_real_metric_requires_explicit_human_scope():
    from review_v3.metrics import aggregate

    data = labels().model_copy(update={"label_origin": "adjudicated"})
    with pytest.raises(ValueError):
        aggregate([data])


def test_no_silent_frozen_registry_mutation_in_analysis():
    data = labels()
    data.registry.facts.append(data.registry.facts[0])
    with pytest.raises(ValueError):
        metric_units(data)


def test_unclear_registry_support_set_not_complete_path():
    from review_v3.logic import question_path_outcome

    value = labels().registry.model_dump()
    value["frozen_hash"] = None
    value["support_sets"][0]["support_set_sufficient"] = "unclear"
    reg = Registry.model_validate(value)
    assert (
        question_path_outcome(reg, {"f0": Outcome.SUCCESS, "f1": Outcome.SUCCESS})
        == Outcome.UNCLEAR
    )


def test_reference_ineligible_not_artificial_e2e_failure():
    data = changed(labels(), "s0", "partial")
    assert metric_units(data)["path_end_to_end_survival:arm-x"][0].outcome == Outcome.INELIGIBLE
