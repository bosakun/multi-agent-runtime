import pytest
from review_v3.failures import derive
from review_v3.logic import Outcome
from review_v3.metrics import (
    Unit,
    aggregate,
    complete_received_paths,
    downstream_outcome,
    fact_e2e,
    metric_units,
    summarize,
)
from synthetic import changed, labels


@pytest.mark.parametrize(
    "transition,expected",
    [
        ("identity_alias", Outcome.SUCCESS),
        ("separate_records", Outcome.SUCCESS),
        ("unknown", Outcome.NON_IDENTIFIABLE),
    ],
)
def test_e2e_transition(transition, expected):
    data = labels(transition=transition)
    row = data.shared[0]
    assert fact_e2e(row, data.arms["arm-x"].s4["f0|worker-x"]) == expected
    units = metric_units(data)
    assert units["path_end_to_end_survival:arm-x"][0].outcome == expected


def test_alias_excluded_publication_denominator():
    units = metric_units(labels())["publication_survival"]
    summary = summarize(units, structural_na_excluded=True)
    assert summary["potentially_eligible_n"] == 0
    assert summary["NA_n"] == 2 and summary["rate"] is None


def test_unknown_any_route_still_available():
    data = labels(transition="unknown")
    units = metric_units(data)
    assert units["any_route_synthesizer_availability:arm-x"][0].outcome == Outcome.SUCCESS
    summary = summarize(units["fact_end_to_end_survival:arm-x"])
    assert summary["non_identifiable_n"] == 2 and summary["evaluable_n"] == 0


def test_supplementary_not_artifact_e2e():
    data = changed(
        labels(),
        "s4",
        "correct",
        artifact_state="absent",
        supplementary_state="correct",
        received_via="supplementary_evidence",
    )
    units = metric_units(data)
    assert units["any_route_synthesizer_availability:arm-x"][0].outcome == Outcome.SUCCESS
    assert units["fact_end_to_end_survival:arm-x"][0].outcome == Outcome.FAILURE


def test_downstream_complete_path_eligibility():
    data = changed(labels(), "s5b", "unsupported")
    assert complete_received_paths(data, data.arms["arm-x"]) == ["p1"]
    assert downstream_outcome(data, data.arms["arm-x"]) == Outcome.FAILURE
    assert "answer_unsupported_despite_complete_received_path" in event_labels(
        derive(data, "arm-x")
    )
    incomplete = changed(data, "s4", "partial", artifact_state="partial")
    assert downstream_outcome(incomplete, incomplete.arms["arm-x"]) == Outcome.INELIGIBLE
    assert downstream_outcome(incomplete, incomplete.arms["arm-x"], True) == Outcome.INELIGIBLE
    assert "answer_unsupported_despite_complete_received_path" not in event_labels(
        derive(incomplete, "arm-x")
    )


def test_downstream_partial_support_not_failure_event():
    data = changed(labels(), "s5b", "partially_supported")
    assert downstream_outcome(data, data.arms["arm-x"]) == Outcome.FAILURE
    assert downstream_outcome(data, data.arms["arm-x"], True) == Outcome.SUCCESS
    assert not derive(data, "arm-x")["events"]


def test_downstream_missing_coverage():
    data = changed(labels(), "s5b", None)
    summary = summarize(metric_units(data)["downstream_evidential_support:arm-x"])
    assert summary["potentially_eligible_n"] == 1
    assert summary["missing_n"] == 1 and summary["evaluable_n"] == 0


def event_labels(result):
    return {label for event in result["events"] for label in event["labels"]}


@pytest.mark.parametrize(
    "state,label",
    [
        ("partial_loss", "publication_partial_loss"),
        ("lost", "publication_loss"),
        ("distorted", "publication_distortion"),
    ],
)
def test_publication_gating(state, label):
    data = changed(labels(transition="separate_records"), "s3", state)
    assert label in event_labels(derive(data, "arm-x"))
    absent = changed(data, "s2", "absent")
    assert label not in event_labels(derive(absent, "arm-x"))
    assert not any(
        label.startswith("publication") for label in event_labels(derive(labels(), "arm-x"))
    )


def test_transmission_cascade_no_double_count():
    data = changed(labels(), "s2", "absent")
    data = changed(data, "s3", "NA", artifact_fact_state="absent")
    data = changed(
        data,
        "s4",
        "absent",
        artifact_state="absent",
        machine_payload_match="mismatch",
        mismatch_fact_related=True,
    )
    result = derive(data, "arm-x")
    assert result["failure_count"] == 1
    assert result["first_observable_failure_stage"] == "S2"
    assert event_labels(result) == {"expression_absent_after_complete_access"}


def test_same_transition_distinct_count_once():
    data = changed(
        labels(),
        "s4",
        "distorted",
        artifact_state="distorted",
        machine_payload_match="mismatch",
        mismatch_fact_related=True,
    )
    result = derive(data, "arm-x")
    assert result["failure_count"] == 1
    assert event_labels(result) == {"transmission_record_mismatch", "transmission_distortion"}
    assert not result["has_multiple_distinct_observable_failures"]


def test_unrelated_metadata_mismatch_no_failure():
    data = changed(
        labels(), "s4", "correct", machine_payload_match="mismatch", mismatch_fact_related=False
    )
    assert not derive(data, "arm-x")["events"]


def test_first_observable_failure_and_uncertainty():
    data = changed(labels(), "s5b", "unsupported")
    assert derive(data, "arm-x")["first_observable_failure_stage"] == "S5"
    data = changed(data, "s2", "unclear")
    result = derive(data, "arm-x")
    assert result["first_observable_failure_stage"] == "undetermined"
    assert result["failure_count"] == 1  # Later observable event retained.


def test_bridge_not_asserted_not_failure():
    assert derive(labels(), "arm-x")["first_observable_failure_stage"] == "no_failure_observed"


def test_shared_s0_s3_not_tripled():
    units = metric_units(labels())
    assert len(units["access_coverage"]) == 2
    assert len(units["publication_survival"]) == 2
    assert len([k for k in units if k.startswith("downstream_evidential_support")]) == 3


def test_strict_sensitivity_partial_no_fractional_score():
    data = changed(labels(), "s2", "partial")
    strict = aggregate([data])["worker_public_expression_survival"]["question_macro_primary"]
    sensitive = aggregate([data], True)["worker_public_expression_survival"][
        "question_macro_primary"
    ]
    assert strict == 0.5 and sensitive == 1  # Binary numerator 1/2 vs 2/2, not partial weight.
    data = changed(data, "s2", "distorted")
    assert (
        aggregate([data], True)["worker_public_expression_survival"]["question_macro_primary"]
        == 0.5
    )


def test_question_macro_not_fact_pooling():
    small = changed(labels("small", 1), "s2", "absent")
    large = labels("large", 3)
    result = aggregate([small, large])["worker_public_expression_survival"]
    assert result["question_macro_primary"] == 0.5
    assert result["micro_secondary_descriptive"]["rate"] == 0.75
    with pytest.raises(ValueError):
        aggregate([small, small])


def test_coverage_categories_separate():
    summary = summarize([Unit("q", str(i), state) for i, state in enumerate(Outcome)])
    assert summary["missing_n"] == summary["unclear_n"] == summary["NA_n"] == 1
    assert summary["non_identifiable_n"] == 1
    assert summary["success_n"] == 1 and summary["evaluable_n"] == 2
