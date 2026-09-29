"""Full-grid offline native transport, frozen-prefix and hard cumulative budget tests."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from epistemic.conditions import configurations
from external_benchmarks import provenance
from external_benchmarks import runner as pilot
from external_benchmarks.conditions import build
from external_benchmarks.dataset import load_public
from hotpot_main import data, runner
from hotpot_main.analysis import analyze
from test_hotpot import fake_transport, row


@pytest.fixture
async def ready(tmp_path, monkeypatch):
    raw_data = tmp_path / "data"
    raw_data.mkdir()
    raw = raw_data / "hotpot_dev_distractor_v1.json"
    raw.write_text(json.dumps([row(i) for i in range(30)]), encoding="utf-8")
    base_bundle = tmp_path / "base-bundle"
    provenance.prepare(raw, base_bundle)
    monkeypatch.setattr(pilot, "BUNDLE", base_bundle)
    monkeypatch.setattr(pilot, "MOCK", tmp_path / "base-mock")
    monkeypatch.setattr(pilot, "CAMPAIGN", tmp_path / "base-real")
    monkeypatch.setattr(pilot, "FREEZE", tmp_path / "base-freeze.json")
    monkeypatch.setattr(pilot, "sources", lambda: {"base": "sealed"})
    monkeypatch.setattr(data, "DATA", raw_data)
    monkeypatch.setattr(data, "PILOT_BUNDLE", base_bundle)
    monkeypatch.setattr(data, "BUNDLE", tmp_path / "main-bundle")
    monkeypatch.setattr(runner, "BUNDLE", data.BUNDLE)
    monkeypatch.setattr(runner, "MOCK", tmp_path / "main-mock")
    monkeypatch.setattr(runner, "CAMPAIGN", tmp_path / "main-real")
    monkeypatch.setattr(runner, "FREEZE", tmp_path / "main-freeze.json")
    monkeypatch.setattr(runner, "sources", lambda: {"main": "sealed"})

    async def host(*_):
        return {"ollama": {"version": "0.34.4", "digest": runner.EXPECTED_DIGEST}}

    monkeypatch.setattr(pilot, "host_probe", host)
    monkeypatch.setattr(runner, "host_probe", host)
    monkeypatch.setenv("MAX_MODEL_CALLS", "60")
    await pilot.execute(mock=True)
    await pilot.bind()
    transport, _ = fake_transport()
    await pilot.execute(transport=transport)
    data.prepare()
    monkeypatch.setenv("MAX_MODEL_CALLS", "456")
    return runner.verify_data()


async def test_full_grid_has_no_pilot_reexecution_and_cumulative_analysis_uses_fresh24(
    ready, tmp_path
):
    assert len(runner.grid(ready)) == 132
    assert sum(1 if c == "C0" else 4 for _, c in runner.grid(ready)) == 456
    base_hash = provenance.file_sha256(pilot.CAMPAIGN / "pilot/results.json")
    await runner.execute(mock=True)
    await runner.bind()
    transport, bodies = fake_transport()
    path = await runner.execute(transport=transport)
    result = json.loads(path.read_text(encoding="utf-8"))
    assert runner.integral(result, ready) and len(bodies) == 456
    assert all((r["question_id"], r["condition"]) in runner.grid(ready) for r in result["records"])
    report = json.loads(analyze(path, tmp_path / "analysis").read_text(encoding="utf-8"))
    assert all(c["n_tasks"] == 24 for c in report["fresh24_comparisons"].values())
    assert set(report["summaries"]["fresh24_prospective"]) == {"C0", "C1", "C2", "C3", "C4"}
    assert report["metadata"]["model_calls"] == 510
    assert runner.ledger_used(runner.CAMPAIGN / "budget.sqlite") == 456
    assert provenance.file_sha256(pilot.CAMPAIGN / "pilot/results.json") == base_hash
    with pytest.raises(ValueError, match="consumed"):
        await runner.execute(transport=transport)
    assert len(bodies) == 456


async def test_role_access_factorial_and_same_c2_c4_role_mapping(ready):
    question = load_public(runner.BUNDLE, ready["task_ids"])[0]
    definitions = {}
    for condition in configurations():
        _, agents, _, _ = build(question, condition, mock=True)
        definitions[condition.id] = agents
    for worker in ["worker_0", "worker_1", "worker_2"]:
        assert definitions["C2"][worker].instruction == definitions["C4"][worker].instruction
        assert definitions["C3"][worker].instruction == definitions["C1"][worker].instruction
        assert (
            definitions["C3"][worker].context.knowledge_ids
            == definitions["C4"][worker].context.knowledge_ids
        )
        assert (
            definitions["C1"][worker].context.knowledge_ids
            == definitions["C2"][worker].context.knowledge_ids
        )


async def test_insufficient_additional_budget_cannot_start_or_reselect(ready, monkeypatch):
    monkeypatch.setenv("MAX_MODEL_CALLS", "455")
    transport, bodies = fake_transport()
    with pytest.raises(ValueError, match="456-call"):
        await runner.execute(mock=True, transport=transport)
    assert not runner.MOCK.exists() and not bodies


async def test_bad_native_output_stops_without_retry_and_cannot_be_analyzed(ready, tmp_path):
    await runner.execute(mock=True)
    await runner.bind()
    transport, bodies = fake_transport(invalid=True)
    path = await runner.execute(transport=transport)
    result = json.loads(path.read_text(encoding="utf-8"))
    assert not runner.integral(result, ready) and len(result["records"]) == 1
    assert result["metadata"]["stopped_reason"] and len(bodies) <= 3
    with pytest.raises(ValueError, match="complete"):
        analyze(path, tmp_path / "incomplete-analysis")


async def test_manifest_and_source_drift_prevent_dispatch(ready, monkeypatch):
    await runner.execute(mock=True)
    await runner.bind()
    transport, bodies = fake_transport()
    monkeypatch.setattr(runner, "sources", lambda: {"main": "changed"})
    with pytest.raises(ValueError, match="drift"):
        await runner.execute(transport=transport)
    assert not bodies
