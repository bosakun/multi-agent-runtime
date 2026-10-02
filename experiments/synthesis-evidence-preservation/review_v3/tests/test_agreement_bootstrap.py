import pytest
from pydantic import ValidationError
from review_v3.agreement import multilabel, nominal, stage_agreement
from review_v3.bootstrap import (
    BootstrapConfig,
    clustered_bootstrap,
    macro_statistic,
    resample_blocks,
)
from review_v3.calibration import EDGE_CASES, CalibrationCase, calibration_stop_candidate
from synthetic import labels


def config(**overrides):
    return BootstrapConfig(
        draws=20,
        seed=17,
        ci_type="percentile",
        confidence_level=0.95,
        zero_denominator_rule="exclude_draw",
        **overrides,
    )


def test_raw_agreement_and_unweighted_kappa():
    result = nominal(["a", "a", "b", "b"], ["a", "b", "b", "b"])
    assert result["raw_percent_agreement"] == 75
    assert result["cohens_kappa_unweighted"] == pytest.approx(0.5)
    assert result["confusion_matrix"]["a"]["b"] == 1


def test_undefined_kappa_visible_and_missing_not_unclear():
    result = nominal(["same", "same"], ["same", "same"])
    assert result["cohens_kappa_unweighted"] is None and result["undefined_reason"] == "Pe=1"
    result = nominal([None, "unclear"], ["unclear", "unclear"])
    assert result["missing_pair_n"] == 1 and result["n_evaluable"] == 1
    assert result["marginal_counts"]["reviewer1"] == {"unclear": 1}
    assert nominal([], [])["undefined_reason"] == "no_evaluable_units"


def test_applicability_independent_semantic_agreement():
    a = labels().shared[0].s2
    b = a.model_copy(update={"reviewer_id": "synthetic-r2", "state": "unclear"})
    result = stage_agreement([a], [b])
    assert result["applicability"]["raw_percent_agreement"] == 100
    assert result["semantic"]["raw_percent_agreement"] == 0
    with pytest.raises(ValueError):
        stage_agreement([a], [b], origin="adjudicated")


def test_multilabel_jaccard_empty_and_label_wise():
    result = multilabel([set(), {"a", "b"}], [set(), {"b", "c"}])
    assert result["exact_set_agreement"] == 0.5
    assert result["jaccard"] == pytest.approx(2 / 3)
    assert result["nonempty_jaccard"] == pytest.approx(1 / 3)
    assert result["label_wise"]["a"]["positive_counts"] == {"reviewer1": 1, "reviewer2": 0}


def test_clustered_block_preservation():
    questions = [labels("q1"), labels("q2")]
    for sample in resample_blocks(questions, config()):
        assert len(sample) == 2
        for block in sample:
            assert set(block.arms) == {"arm-x", "arm-y", "arm-z"}
            assert len(block.shared) == 2
            assert block.registry.question.question_id in {"q1", "q2"}
    assert list(resample_blocks(questions, config())) == list(resample_blocks(questions, config()))


def test_bootstrap_config_required_and_real_gate():
    with pytest.raises(ValidationError):
        BootstrapConfig()
    real = labels().model_copy(update={"label_origin": "adjudicated"})
    with pytest.raises(ValueError):
        clustered_bootstrap([real], macro_statistic("access_coverage"), config())


def test_synthetic_bootstrap_only_and_zero_denominator():
    synthetic = [labels("q1"), labels("q2")]
    result = clustered_bootstrap(synthetic, macro_statistic("access_coverage"), config())
    assert result["evaluable_draws"] == 20
    assert result["interval"] == [1, 1]  # Invented data, not research CI.
    result = clustered_bootstrap(synthetic, lambda _: None, config())
    assert result["excluded_draws"] == 20 and result["interval"] is None
    reject = config().model_copy(update={"zero_denominator_rule": "reject"})
    with pytest.raises(ValueError):
        clustered_bootstrap(synthetic, lambda _: None, reject)


def test_calibration_namespaces_and_edge_cases():
    case = CalibrationCase(
        case_id="vignette",
        namespace="synthetic_vignette",
        synthetic=True,
        source_hashes={},
        edge_cases=list(EDGE_CASES),
    )
    assert len(case.edge_cases) == 12
    assert calibration_stop_candidate([{"new_guideline_rules": 0}], case.edge_cases)
    assert not calibration_stop_candidate([{"new_guideline_rules": 1}], case.edge_cases)
