"""Additive recovery safety gates, append-only writes and actual-prefix offline transport."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from epistemic.models import CallRecord
from hotpot_recovery import runner
from hotpot_recovery.provider import AppendOnlyAuditedProvider
from prospective_pilot.budget import ClosedCallBudget
from test_hotpot import fake_transport

from app.llm.mock_provider import MockProvider


def test_minimum_recovery_grid_and_controls_preserve_full_scope():
    cells = runner.work_grid()
    assert len(cells) == 61 and cells[0] == (runner.FAILED_QID, "C1")
    assert sum(2 if cell == cells[0] else 1 if cell[1] == "C0" else 4 for cell in cells) == 206
    assert runner.controls()["cumulative_reservations"] == 511
    assert runner.controls()["cumulative_runs"] == 150
    assert runner.controls()["cumulative_calls"] == 510
    assert runner.controls()["retry"] is False
    assert runner.controls()["resume"] is False


def test_append_only_checkpoints_do_not_replace_open_files(tmp_path, monkeypatch):
    provider = AppendOnlyAuditedProvider(
        MockProvider(runner.pilot.mock_response),
        ClosedCallBudget(tmp_path / "budget.sqlite", 1),
        tmp_path / "journal",
        history=tmp_path / "history",
    )
    record = CallRecord(run_id="run", agent_id="worker_0", request={})
    provider.calls.append(record)

    def forbidden(*_):
        raise AssertionError("replace is prohibited")

    monkeypatch.setattr(Path, "replace", forbidden)
    provider._checkpoint(record)
    first = next((tmp_path / "history").glob("*.json"))
    before = first.read_bytes()
    with first.open("rb"):
        record.error = "PermissionError"
        provider._checkpoint(record)
        provider.finalize()
    assert first.read_bytes() == before
    assert len(list((tmp_path / "history").glob("*.json"))) == 2
    with pytest.raises(FileExistsError):
        provider.finalize()


def test_immutable_copy_rejects_existing_destination(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "copy"
    source.write_bytes(b"non-ascii: \xe6\x97\xa5\r\n")
    runner.copy_new(source, destination)
    assert destination.read_bytes() == source.read_bytes()
    with pytest.raises(FileExistsError):
        runner.copy_new(source, destination)


async def test_insufficient_budget_and_consumed_target_make_no_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "MOCK", tmp_path / "mock")
    monkeypatch.setenv("MAX_MODEL_CALLS", "205")
    with pytest.raises(ValueError, match="206-call"):
        await runner.execute(mock=True)
    assert not runner.MOCK.exists()
    monkeypatch.setenv("MAX_MODEL_CALLS", "206")
    runner.MOCK.mkdir()
    with pytest.raises(ValueError, match="consumed"):
        await runner.execute(mock=True)


async def test_offline_native_recovery_reuses_workers_and_only_sends_206(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "CAMPAIGN", tmp_path / "campaign")
    monkeypatch.setattr(runner, "FREEZE", tmp_path / "freeze.json")
    monkeypatch.setattr(runner, "MOCK", tmp_path / "mock")
    monkeypatch.setenv("MAX_MODEL_CALLS", "206")

    async def host():
        return {"ollama": {"version": "0.34.4", "digest": runner.EXPECTED_DIGEST}}

    monkeypatch.setattr(runner, "host_probe", host)
    prior_hashes = runner.prior_files()
    await runner.execute(mock=True)
    await runner.bind()
    transport, bodies = fake_transport()
    path = await runner.execute(transport=transport)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert runner.integral(data) and len(bodies) == 206
    assert data["records"][0]["calls"] == 4
    assert data["records"][0]["new_calls"] == data["records"][0]["reused_calls"] == 2
    first_agents = [json.loads(body["messages"][1]["content"])["agent_id"] for body in bodies[:2]]
    assert first_agents == ["worker_0", "synthesizer"]
    synthesis = json.loads(bodies[1]["messages"][1]["content"])
    assert [a["producer"] for a in synthesis["artifacts"]] == ["worker_0", "worker_1", "worker_2"]
    for _, call in runner.reuse_calls():
        reused = next(a for a in synthesis["artifacts"] if a["producer"] == call.agent_id)
        assert reused["payload"] == call.response["output"]
    assert runner.prior_files() == prior_hashes
    assert runner.main.ledger_used(runner.CAMPAIGN / "budget.sqlite") == 206
    with pytest.raises(ValueError, match="consumed"):
        await runner.execute(transport=transport)
    assert len(bodies) == 206
    monkeypatch.setattr(runner, "sources", lambda: {"tampered": "source"})
    with pytest.raises(ValueError, match="drift"):
        runner.verify_binding()
    assert len(bodies) == 206
