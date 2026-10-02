from datetime import UTC, datetime

import pytest
from review_v3.adjudication import save_adjudication
from review_v3.ballots import reconcile_stage_ids, validate_ballot
from review_v3.run import main
from review_v3.schema import Adjudication
from review_v3.storage import ReviewStore, exclusive, read
from synthetic import labels, registry, workflow


def test_ballot_no_derived_failure_fields():
    stage = labels().shared[0].s2.model_dump(mode="json")
    ballot = [{"stage": "S2", "annotation": stage}]
    assert validate_ballot("S2", ballot, "synthetic-r1", "synthetic-v1")
    stage["first_observable_failure_stage"] = "S2"
    with pytest.raises(ValueError):
        validate_ballot("S2", ballot, "synthetic-r1", "synthetic-v1")


def test_ballot_reviewer_and_stage_gates():
    stage = labels().shared[0].s2.model_dump(mode="json")
    ballot = [{"stage": "S2", "annotation": stage}]
    with pytest.raises(ValueError):
        validate_ballot("S1", ballot, "synthetic-r1", "synthetic-v1")
    with pytest.raises(ValueError):
        validate_ballot("S2", ballot, "synthetic-r2", "synthetic-v1")
    with pytest.raises(ValueError):
        validate_ballot("S2", ballot * 2, "synthetic-r1", "synthetic-v1")


def test_anonymous_reconciliation_separate_copy():
    stage = labels().arms["arm-x"].s4["f0|worker-x"].model_dump(mode="json")
    stage.update(question_id="anonymous", worker_id="worker-1", arm="response-x")
    ballot = [{"stage": "S4", "annotation": stage}]
    linkage = {
        "question_id": "synthetic-q",
        "arm": "arm-x",
        "aliases": {"question": "anonymous", "arm": "response-x", "worker-x": "worker-1"},
    }
    converted = reconcile_stage_ids(ballot, linkage)
    assert converted[0]["annotation"]["worker_id"] == "worker-x"
    assert ballot[0]["annotation"]["worker_id"] == "worker-1"


def test_adjudication_requires_two_complete_independent_locks(tmp_path):
    flow = workflow()
    record = Adjudication(
        unit_id="synthetic-q",
        field="S2",
        reviewer1_label="correct",
        reviewer2_label="partial",
        adjudicated_label="unclear",
        reason="Synthetic ONLY",
        guideline_rule="synthetic-rule",
        adjudicator="synthetic-human",
        timestamp=datetime.now(UTC),
        codebook_version="synthetic-v1",
    )
    store = ReviewStore(tmp_path)
    with pytest.raises(ValueError):
        save_adjudication(store, flow, "synthetic-q", "v1", [record.model_dump()], {})
    for reviewer in flow.reviewer_ids:
        for phase in ("S1", "S2", "S3", "S4", "S5"):
            flow = flow.lock(reviewer, phase, {"synthetic": phase}, "synthetic-v1")
    save_adjudication(store, flow, "synthetic-q", "v1", [record.model_dump()], {"synthetic": True})
    assert (
        read(tmp_path / "adjudication_log/synthetic-q/v1.json")[0]["adjudicated_label"] == "unclear"
    )


def test_cli_schema_candidate_validate_only(capsys, tmp_path):
    assert main(["schema", "S3"]) == 0
    assert "publication_transition_type" in capsys.readouterr().out
    assert main(["candidate"]) == 0
    assert "NOT FINAL-FROZEN" in capsys.readouterr().out
    exclusive(tmp_path / "registry.json", registry().model_dump(mode="json"))
    assert main(["validate", "registry", str(tmp_path / "registry.json")]) == 0
    assert "semantic_review_performed" in capsys.readouterr().out
