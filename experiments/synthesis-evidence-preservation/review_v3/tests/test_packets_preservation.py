import json
from pathlib import Path

import pytest
from review_v3 import STATUS
from review_v3.manifest import freeze_candidate
from review_v3.packets import ArmSource, PrivateSource, WorkerSource, build_packet, public_output
from review_v3.provenance import arm_source, worker_source
from review_v3.schema import Scope
from review_v3.storage import file_hash, read, verify_snapshot
from review_v3.workflow import Workflow, frozen_registry
from synthetic import registry, workflow


def source(reg):
    output = {
        "candidate_answer": "Invented",
        "findings": [{"text": "Invented fact", "evidence_ids": ["s0"]}],
        "uncertainty": {"confidence": None, "assumptions": [], "unknowns": [], "evidence_ids": []},
    }
    worker = WorkerSource(
        worker_id="worker_0",
        actual_sentence_ids=["s0"],
        intended_sentence_ids=["s0"],
        public_output=output,
        public_artifact=output,
        publication_transition_type="identity_alias",
    )
    return PrivateSource(
        question=reg.question,
        sentences=reg.sentences,
        workers=[worker],
        arms={
            "B": ArmSource(
                artifacts_by_worker={"worker_0": output},
                supplementary_material="Invented raw evidence",
                final_output={"answer": "Invented final"},
            )
        },
        gold_answer="private-gold",
        gold_supporting_facts=[["Invented", 0]],
        condition_mapping={"B": "cited-evidence"},
        automated_scores={"F1": 1},
        aggregate_outcomes={"average": 1},
        source_hashes={"private-path": "opaque-hash"},
    )


def scope(reg):
    qid = reg.question.question_id
    return Scope(
        included_case_ids=[qid],
        iaa_eligible_case_ids=[qid],
        descriptive_only_case_ids=[],
        decision_reason="Synthetic scope only",
    )


def test_r1_raw_only_blank_registry(tmp_path):
    reg = registry()
    result = build_packet(
        source(reg),
        Workflow(reviewer_ids=("r1", "r2"), synthetic=True),
        reg,
        "R1",
        "r1",
        tmp_path / "packet",
        scope=scope(reg),
    )
    packet = result["packet"]
    assert set(packet["materials"]) == {"question_text", "reference_sentences"}
    assert packet["form"]["registry"]["facts"] == []
    assert packet["form"]["registry"]["paths"] == []
    assert "private-gold" not in json.dumps(packet)
    assert "opaque-hash" not in json.dumps(read(tmp_path / "packet/manifest.json"))
    assert read(tmp_path / "packet/manifest.json")["packet_hashes"]["packet.json"] == file_hash(
        tmp_path / "packet/packet.json"
    )


def test_r2_gold_only_after_both_r1_and_own_ballot(tmp_path):
    reg = registry()
    flow = Workflow(reviewer_ids=("r1", "r2"), synthetic=True)
    with pytest.raises(ValueError):
        build_packet(source(reg), flow, reg, "R2", "r1", tmp_path / "early", scope=scope(reg))
    for reviewer in flow.reviewer_ids:
        flow = flow.lock(reviewer, "R1", reg.model_dump(mode="json"), "fixture")
    flow = flow.advance("R1_LOCKED").advance("R2_OPEN")
    result = build_packet(
        source(reg), flow, reg, "R2", "r1", tmp_path / "aligned", scope=scope(reg)
    )
    assert result["packet"]["materials"]["benchmark_alignment"]["gold_answer"] == "private-gold"
    assert (
        result["packet"]["materials"]["own_locked_R1_registry"]["facts"]
        == reg.model_dump()["facts"]
    )
    assert "public_output" not in json.dumps(result["packet"])


def test_stage_projection_and_final_not_before_s5(tmp_path):
    reg = registry()
    flow = workflow(reg)
    reg = frozen_registry(reg, flow)
    for phase in ["S1", "S2", "S3", "S4", "S5"]:
        result = build_packet(
            source(reg),
            flow,
            reg,
            phase,
            "synthetic-r1",
            tmp_path / phase,
            "B",
            "anonymous-case",
            "anonymous-arm",
            scope(reg),
        )
        packet = result["packet"]
        contents = json.dumps(packet)
        assert "private-gold" not in contents and "automated_scores" not in contents
        assert "condition_mapping" not in contents and '"B"' not in contents
        assert "worker_0" not in contents
        assert ("final_output" in packet["materials"]) == (phase == "S5")
        if phase == "S1":
            assert "public_output" not in contents and "actual_synthesizer_input" not in contents
        for form in packet["form"]:
            assert form["annotation"]["state"] is None
            assert form["annotation"]["rationale"] is None
            assert form["annotation"]["reviewer_id"] is None
        flow = flow.lock("synthetic-r1", phase, {"synthetic": True}, "fixture")
    with pytest.raises((FileExistsError, ValueError)):
        build_packet(
            source(reg), flow, reg, "S5", "synthetic-r1", tmp_path / "S5", "B", scope=scope(reg)
        )


def test_scope_required_no_automatic_30_28(tmp_path):
    reg = registry()
    with pytest.raises(ValueError):
        build_packet(
            source(reg), Workflow(reviewer_ids=("r1", "r2")), reg, "R1", "r1", tmp_path / "p"
        )


def test_output_before_registry_freeze_and_private_fields_rejected(tmp_path):
    reg = registry()
    with pytest.raises(ValueError):
        build_packet(
            source(reg),
            Workflow(reviewer_ids=("r1", "r2")),
            reg,
            "S1",
            "r1",
            tmp_path / "p",
            scope=scope(reg),
        )
    with pytest.raises(ValueError):
        public_output({"answer": "Invented", "condition": "C3"})


def test_actual_input_mapping_hash_and_intended_separate():
    reg = registry()
    sentence = reg.sentences[0]
    payload = {"candidate_answer": "Invented", "findings": [], "uncertainty": {"unknowns": []}}
    journal = {
        "agent_id": "w",
        "error": None,
        "response": {"output": payload},
        "request": {
            "context": {
                "knowledge": [
                    {
                        "id": "s0",
                        "content": json.dumps(
                            {"title": sentence.title, "sentence_index": 0, "text": sentence.text}
                        ),
                    }
                ]
            }
        },
    }
    projected = worker_source("w", journal, reg.sentences, ["s1"], payload, "unknown", {})
    assert projected.actual_sentence_ids == ["s0"] and projected.intended_sentence_ids == ["s1"]
    assert projected.publication_transition_type == "unknown"  # Not classified from text equality.
    journal["request"]["context"]["knowledge"][0]["content"] = '{"text":"wrong"}'
    with pytest.raises(ValueError):
        worker_source("w", journal, reg.sentences, [], payload, "unknown", {})


def test_native_synthesis_source_supplementary_route():
    context = {
        "artifacts": [{"producer": "w", "payload": {"candidate_answer": "Invented"}}],
        "inputs": {"supplementary_material": "Invented evidence"},
        "knowledge": [],
    }
    request = {"messages": [{"role": "user", "content": json.dumps(context)}]}
    projected = arm_source(request, {"answer": "Invented"}, ["w"], {})
    assert projected.supplementary_material == "Invented evidence"
    assert set(projected.artifacts_by_worker) == {"w"}


def test_freeze_candidate_not_ready_not_human_labels():
    candidate = freeze_candidate()
    assert candidate["status"] == STATUS
    assert candidate["candidate"] == "HUMAN REVIEW V3 FREEZE CANDIDATE"
    assert candidate["human_labels"] == 0 and not candidate["final_frozen"]
    assert candidate["scope"] is candidate["bootstrap_config"] is None


def test_historical_frozen_assets_unchanged_hash_only():
    repo = Path(__file__).resolve().parents[4]
    study = repo / "experiments/synthesis-evidence-preservation"
    seal = read(study / "freezes/v1.json")
    expected = {**seal["code_hashes"], **seal["source_hashes"]}
    if not all((repo / path).is_file() for path in expected):
        pytest.skip("Historical local/private sealed data not distributed with checkout")
    assert verify_snapshot(repo, expected)["passed"]
    kit = study / "reports/review-kits/prepared-625d2bfc3c62491ba47d1540b0d59466"
    preparation = read(kit / "preparation-audit.json")
    for slot in preparation["prepared_slots"]:
        root = study / slot["path"]
        assert file_hash(root / "packet-manifest.json") == slot["packet_manifest_sha256"]
        assert verify_snapshot(root, read(root / "packet-manifest.json")["files"])["passed"]
