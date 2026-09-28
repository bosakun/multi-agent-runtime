import pytest
from epistemic.analysis import aggregate, holm, mcnemar, paired_inference
from epistemic.metrics import contradictions, diversity, valid_claim
from epistemic.models import Claim, GoldClaim


def test_valid_claim_requires_complete_exact_citations():
    gold = [GoldClaim(subject="capacity", value="ready", supporting_sets=[["e1", "e2"]])]
    assert valid_claim(Claim(subject="CAPACITY", value="ready", evidence_ids=["e2", "e1"]), gold)
    for value, ids in [
        ("ready", ["e1"]),
        ("ready", ["e1", "e2", "wrong"]),
        ("absent", ["e1", "e2"]),
    ]:
        assert not valid_claim(Claim(subject="capacity", value=value, evidence_ids=ids), gold)


def test_diversity_metrics_hand_calculation():
    result = diversity([{"a", "b"}, {"b", "c"}, {"b"}])
    assert result["unique"] == pytest.approx(2 / 3)
    assert result["redundancy"] == pytest.approx(2 / 5)
    assert result["jaccard"] == pytest.approx((1 / 3 + 1 / 2 + 1 / 2) / 3)
    assert diversity([{"a"}])["unique"] is None
    assert diversity([set(), set()])["jaccard"] is None
    assert diversity([{"a"}, {"b"}, {"c"}])["unique"] == 1


def test_contradictions():
    assert (
        contradictions(
            [
                Claim(subject="A", value="yes", evidence_ids=[]),
                Claim(subject="a", value="no", evidence_ids=[]),
            ]
        )
        == 1
    )


def test_paired_statistics_and_corrections():
    result = paired_inference([1.0, 1.0, 1.0, 1.0])
    assert result["p"] == 0.125
    assert result["ci95"] == [1.0, 1.0]
    assert result["dz"] is None
    assert paired_inference([0.0] * 4)["p"] == 1
    assert paired_inference([1.0, -1.0, 0.5]) == paired_inference([1.0, -1.0, 0.5])
    assert mcnemar([(1, 0)] * 4)["p"] == 0.125
    assert mcnemar([(1, 1)])["p"] == 1
    assert holm([0.01, 0.02, 0.8]) == pytest.approx([0.03, 0.04, 0.8])


def record(task, condition, repetition, value):
    return {
        "task_id": task,
        "condition": condition,
        "repetition": repetition,
        "metrics": {
            "gold_claim_coverage": value,
            "worker_evidence_coverage": value,
            "task_success": int(value),
        },
    }


def test_aggregation_averages_repetitions_and_preserves_failures():
    records = [
        record(t, c, r, float(c == "C3"))
        for t in ["a", "b"]
        for c in ["C2", "C3"]
        for r in [0, 1, 2]
    ]
    report = aggregate(records)
    assert report["primary"][0]["n_tasks"] == 2  # NOT six repetitions
    assert report["summaries"]["C2"]["task_success"]["mean"] == 0
    assert len(report["failure_cases"]) == 6
    assert report["incomplete_blocks"]
    with pytest.raises(ValueError, match="Duplicate"):
        aggregate(records + [records[0]])


def test_unpaired_repetitions_do_not_enter_pair_means():
    records = [record("a", "C3", 0, 1), record("a", "C2", 0, 1), record("a", "C3", 1, 0)]
    assert aggregate(records)["primary"][0]["mean_difference"] == 0
