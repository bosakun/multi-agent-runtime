"""Published-source projection, official scoring, access policy and safe offline migration."""

import hashlib
import json
import sys
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from external_benchmarks import provenance, runner
from external_benchmarks.conditions import build, document_partitions, pilot_conditions
from external_benchmarks.dataset import public_question, select, supporting_pairs
from external_benchmarks.models import PrivateGold
from external_benchmarks.scoring import score, upstream
from operational_recovery.pilot24 import read_signed

from app.core.models import AgentContext


def row(index=0):
    return {
        "_id": f"{index:024x}",
        "question": "What name is given in the document?",
        "context": [
            [f"Document {n}", [" The named person is Ada.", " Another sentence."]]
            for n in range(10)
        ],
        "answer": "PRIVATE_GOLD_ONLY_SENTINEL",
        "supporting_facts": [["Document 0", 0]],
        "type": "bridge",
        "level": "hard",
    }


def test_public_projection_preserves_titles_text_and_indices_but_excludes_annotations():
    original = row()
    projected = public_question(original)
    serialized = projected.model_dump_json()
    assert "PRIVATE_GOLD_ONLY_SENTINEL" not in serialized
    assert "supporting_facts" not in serialized and '"level"' not in serialized
    assert '"type"' not in serialized
    assert projected.sentences[0].text == " The named person is Ada."
    assert supporting_pairs(projected, [projected.sentences[0].id]) == [["Document 0", 0]]
    with pytest.raises(ValueError):
        supporting_pairs(projected, ["invented-id"])


def test_sampling_and_document_routing_cannot_depend_on_gold_or_difficulty():
    rows = [row(i) for i in range(12)]
    changed = deepcopy(rows)
    for item in changed:
        item.update(answer="DIFFERENT", supporting_facts=[], type="comparison", level="easy")
    chosen, before = select(rows)
    after, counts = select(changed)
    assert [q.model_dump() for q in chosen] == [q.model_dump() for q in after]
    assert before == counts
    for question in chosen:
        parts = document_partitions(question)
        all_ids = [eid for ids in parts.values() for eid in ids]
        assert set(all_ids) == {s.id for s in question.sentences}
        assert len(all_ids) == len(set(all_ids))
        for document in range(10):
            ids = {s.id for s in question.sentences if s.document == document}
            assert sum(ids.issubset(set(part)) for part in parts.values()) == 1


@pytest.mark.parametrize("change", [{"_id": "../../escape"}, {"context": []}])
def test_invalid_public_structure_rejected(change):
    original = row()
    original.update(change)
    with pytest.raises(ValueError):
        public_question(original)


def test_official_answer_normalization_and_supporting_fact_sets():
    annotation = PrivateGold(id="q", answer="The Beatles", supporting_facts=[("Title", 0)])
    result = score(
        {"answer": {"q": "beatles!"}, "sp": {"q": [["Title", 0], ["Title", 0]]}}, [annotation]
    )
    assert all(value == 1 for value in result.values())
    assert upstream()["exact_match_score"]("The Beatles", "beatles!")


def test_official_joint_formula_and_answer_scoring_not_old_conjunctive_success():
    annotation = PrivateGold(
        id="q", answer="red blue", supporting_facts=[("Title", 0), ("Title", 1)]
    )
    result = score({"answer": {"q": "red"}, "sp": {"q": [["Title", 0]]}}, [annotation])
    assert result["f1"] == pytest.approx(2 / 3)
    assert result["sp_f1"] == pytest.approx(2 / 3)
    assert result["joint_f1"] == pytest.approx(0.4)
    exact = score({"answer": {"q": "red blue"}, "sp": {"q": []}}, [annotation])
    assert exact["em"] == exact["f1"] == 1
    assert exact["joint_em"] == 0  # evidence faults do not erase answer EM/F1


def test_official_yes_no_and_complete_cohort_requirements():
    annotation = PrivateGold(id="q", answer="yes", supporting_facts=[("Title", 0)])
    result = score({"answer": {"q": "yes indeed"}, "sp": {"q": [["Title", 0]]}}, [annotation])
    assert result["f1"] == 0
    with pytest.raises(ValueError):
        score({"answer": {}, "sp": {}}, [annotation])


def test_access_conditions_preserve_original_factors_without_oracle_routing():
    question = public_question(row())
    for config in pilot_conditions():
        _, agents, inputs, _ = build(question, config, mock=True)
        assert inputs.inputs == {} and inputs.task == question.question
        if config.id == "C0":
            assert len(agents) == 1
        else:
            assert agents["synthesizer"].context.knowledge_ids == []
        worker_ids = [
            set(agent.context.knowledge_ids)
            for key, agent in agents.items()
            if key.startswith("worker_")
        ]
        if config.id == "C3":
            assert not any(worker_ids[i] & worker_ids[j] for i in range(3) for j in range(i))
        else:
            assert all(ids == {s.id for s in question.sentences} for ids in worker_ids)


def test_download_checksum_and_receipt_hash_are_distinct(tmp_path, monkeypatch):
    payload = json.dumps([row(i) for i in range(6)]).encode()
    checksum = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(provenance, "DATA", tmp_path / "data")
    monkeypatch.setattr(provenance, "MIRROR_SHA256", checksum)
    monkeypatch.setattr(
        provenance.urllib.request, "urlopen", lambda *_args, **_kwargs: BytesIO(payload)
    )
    raw = provenance.download(mirror=True)
    receipt = read_signed(provenance.DATA / "download.json")
    assert receipt["raw_sha256"] == checksum
    assert receipt["sha256"] != checksum
    verification = read_signed(provenance.verify_download())
    assert verification["raw_sha256"] == checksum
    provenance.prepare(raw, tmp_path / "bundle")
    with pytest.raises(ValueError, match="overwrite"):
        provenance.download(mirror=True)


def test_bad_mirror_checksum_writes_no_corpus(tmp_path, monkeypatch):
    monkeypatch.setattr(provenance, "DATA", tmp_path / "data")
    monkeypatch.setattr(
        provenance.urllib.request, "urlopen", lambda *_args, **_kwargs: BytesIO(b"[]")
    )
    with pytest.raises(ValueError, match="checksum"):
        provenance.download(mirror=True)
    assert not list(provenance.DATA.glob("*.json"))


def test_prepared_inventory_including_nested_manifest_is_guarded(tmp_path):
    raw = tmp_path / "fixture.json"
    raw.write_text(json.dumps([row(i) for i in range(6)]), encoding="utf-8")
    bundle = tmp_path / "bundle"
    provenance.prepare(raw, bundle)
    provenance.verify_bundle(bundle)
    (bundle / "public" / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory drift"):
        provenance.verify_bundle(bundle)


@pytest.fixture
async def bound(tmp_path, monkeypatch):
    raw = tmp_path / "fixture.json"
    raw.write_text(json.dumps([row(i) for i in range(6)]), encoding="utf-8")
    bundle = tmp_path / "bundle"
    provenance.prepare(raw, bundle)
    monkeypatch.setattr(runner, "BUNDLE", bundle)
    monkeypatch.setattr(runner, "MOCK", tmp_path / "mock")
    monkeypatch.setattr(runner, "CAMPAIGN", tmp_path / "campaign")
    monkeypatch.setattr(runner, "FREEZE", tmp_path / "freeze.json")
    monkeypatch.setattr(runner, "sources", lambda: {"fixture": "sealed"})
    monkeypatch.setenv("MAX_MODEL_CALLS", "60")

    async def host(*_):
        return {"ollama": {"version": "fake", "digest": runner.EXPECTED_DIGEST}}

    monkeypatch.setattr(runner, "host_probe", host)
    mock = await runner.execute(mock=True)
    assert runner.integral(json.loads(mock.read_text(encoding="utf-8")))
    await runner.bind()
    return bundle


def fake_transport(*, invalid=False, truncate=False):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        assert request.url.path == "/api/chat" and body["think"] is False
        assert "PRIVATE_GOLD_ONLY_SENTINEL" not in json.dumps(body)
        context = AgentContext.model_validate_json(body["messages"][1]["content"])
        allowed = sorted(context.evidence_scope())
        citations = ["invented-id"] if invalid and len(bodies) == 1 else allowed[:1]
        uncertainty = {"confidence": None, "assumptions": [], "evidence_ids": [], "unknowns": []}
        if "answer" in body["format"]["properties"]:
            output = {"answer": "NOT_GOLD", "evidence_ids": citations, "uncertainty": uncertainty}
        else:
            output = {
                "candidate_answer": "",
                "findings": [{"text": "observed", "evidence_ids": citations}],
                "uncertainty": uncertainty,
            }
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "length" if truncate and len(bodies) == 1 else "stop",
                "message": {"content": json.dumps(output), "thinking": ""},
                "prompt_eval_count": 20,
                "eval_count": 30,
            },
        )

    return httpx.MockTransport(handler), bodies


async def test_full_fake_native_grid_and_official_analysis_without_gold_inputs(bound, tmp_path):
    transport, bodies = fake_transport()
    path = await runner.execute(transport=transport)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert runner.integral(data) and len(bodies) == 54 and len(data["records"]) == 18
    assert all(not any(record["audit"].values()) for record in data["records"])
    report = json.loads(runner.analyze(path, tmp_path / "analysis").read_text(encoding="utf-8"))
    assert set(report["summaries"]) == {"C0", "C2", "C3"}
    assert all(values["f1"] == 0 for values in report["summaries"].values())
    assert report["primary_C3_minus_C2_answer_f1"]["n_tasks"] == 6
    with pytest.raises(ValueError, match="consumed"):
        await runner.execute(transport=transport)
    assert len(bodies) == 54


@pytest.mark.parametrize("fault", ["invalid", "truncate"])
async def test_backend_faults_fail_stop_no_repair_retry_or_incomplete_analysis(
    bound, tmp_path, fault
):
    transport, bodies = fake_transport(**{fault: True})
    path = await runner.execute(transport=transport)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert not runner.integral(data) and len(data["records"]) == 1
    assert len(bodies) <= 3 and data["metadata"]["stopped_reason"]
    with pytest.raises(ValueError, match="complete"):
        runner.analyze(path, tmp_path / "analysis")


async def test_source_data_and_backend_drift_prevent_dispatch(bound, monkeypatch):
    transport, bodies = fake_transport()

    async def changed_host():
        return {"ollama": {"version": "changed", "digest": runner.EXPECTED_DIGEST}}

    monkeypatch.setattr(runner, "host_probe", changed_host)
    with pytest.raises(ValueError, match="drift"):
        await runner.execute(transport=transport)
    assert not bodies
    monkeypatch.setattr(runner, "sources", lambda: {"fixture": "changed"})
    with pytest.raises(ValueError, match="mismatch"):
        runner.verify_binding()


async def test_insufficient_budget_does_not_reduce_grid(bound, monkeypatch):
    monkeypatch.setenv("MAX_MODEL_CALLS", "53")
    transport, bodies = fake_transport()
    with pytest.raises(ValueError, match="54-call"):
        await runner.execute(transport=transport)
    assert not bodies
