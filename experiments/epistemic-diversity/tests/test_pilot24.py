"""Protocol extension preserves scientific factors and tests the 48-call HTTP path."""

import json
import sys
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epistemic.benchmark import load_task, partition
from epistemic.conditions import build_condition, configurations
from epistemic.models import ModelSettings
from epistemic.provider import CallBudget
from operational_recovery import pilot24 as pilot


def test_only_generation_limit_and_deadline_change():
    old = ModelSettings(
        provider="real", model="qwen3:14b", execution_profile="local_ollama", timeout_seconds=600
    )
    new = pilot.Settings(provider="real")
    for task_id in pilot.PILOT_IDS:
        task, gold = load_task(task_id)
        for config in [c for c in configurations() if c.id in ["C2", "C3"]]:
            args = task, config, partition(task, gold, pilot.SEED), pilot.SEED
            w1, a1, i1, s1 = build_condition(*args, old)
            w2, a2, i2, s2 = build_condition(*args, new)
            assert (w1, i1, s1) == (w2, i2, s2)
            for key in a1:
                a2[key].model.max_output_tokens = 2048
                a2[key].execution.timeout_seconds = 600
                assert a1[key] == a2[key]
    with pytest.raises(ValidationError):
        pilot.Settings(temperature=0.1)
    with pytest.raises(ValidationError):
        ModelSettings(
            execution_profile="local_ollama", max_output_tokens=4096, timeout_seconds=1200
        )


@pytest.fixture
def bound(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "CAMPAIGN", tmp_path / "pilot")
    monkeypatch.setattr(pilot, "FREEZE", tmp_path / "freeze.json")
    monkeypatch.setattr(pilot.diagnostic, "CAMPAIGN", tmp_path / "diagnostic")
    monkeypatch.setattr(pilot, "sources", lambda: {"test": "sealed"})
    monkeypatch.setattr(pilot, "gate", lambda: {"diagnostic": "passed"})
    monkeypatch.setenv("MAX_MODEL_CALLS", "60")
    backend = {"backend_version": "fake", "model_digest": "fake"}
    (tmp_path / "diagnostic/diagnostic").mkdir(parents=True)
    (tmp_path / "diagnostic/diagnostic/backend.json").write_text(json.dumps(backend))

    async def preflight(*_):
        return backend

    monkeypatch.setattr(pilot, "preflight", preflight)
    budget = CallBudget(tmp_path / "diagnostic/budget.sqlite", 60)
    for _ in range(3):
        budget.reserve()
    pilot.prepare()


def make_transport(fail=False):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        assert body["max_tokens"] == 4096 and body["temperature"] == 0
        assert not {"think", "reasoning_effort", "tools", "max_completion_tokens"} & body.keys()
        output = {
            "claims": [],
            "insights": [],
            "uncertainty": {
                "confidence": None,
                "assumptions": [],
                "evidence_ids": [],
                "unknowns": [],
            },
        }
        if json.loads(body["messages"][1]["content"])["agent_id"] == "synthesizer":
            output.update(conclusion="fake", decision_summary="fake")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "length" if fail and len(bodies) == 1 else "stop",
                        "message": {"content": json.dumps(output), "reasoning": "PRIVATE"},
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 30, "total_tokens": 50},
            },
        )

    return httpx.MockTransport(handler), bodies


async def test_full_fake_http_grid_integrity_and_no_reuse(bound):
    transport, bodies = make_transport()
    path = await pilot.execute(transport=transport)
    result = json.loads(path.read_text())
    assert len(bodies) == 48
    assert pilot.integral(result)
    assert result["metadata"]["budget_used_after"] == 51
    observations = list(path.parent.joinpath("http-observations").glob("*.json"))
    assert len(observations) == 48
    assert all("PRIVATE" not in p.read_text() for p in observations)
    with pytest.raises(ValueError):
        await pilot.execute(transport=transport)
    assert len(bodies) == 48


async def test_failure_retained_no_second_case_or_retry(bound):
    transport, bodies = make_transport(fail=True)
    result = json.loads((await pilot.execute(transport=transport)).read_text())
    assert not pilot.integral(result)
    assert len(result["records"]) == 1
    assert len(bodies) == 3  # Other independent workers finish; failed worker never retries.
    assert "provider_output_truncated" in result["records"][0]["errors"]
    assert result["metadata"]["stopped_reason"]


def test_stale_source_and_old_protocol_binding_rejected(bound, monkeypatch):
    pilot.verify_binding()
    monkeypatch.setattr(pilot, "sources", lambda: {"test": "changed"})
    with pytest.raises(ValueError, match="mismatch"):
        pilot.verify_binding()


async def test_mock_pipeline_full_grid(tmp_path):
    result = json.loads((await pilot.execute(mock=True, mock_output=tmp_path / "mock")).read_text())
    assert pilot.integral(result)
    assert result["metadata"]["pilot_model_calls"] == 48
    assert all(r["metrics"]["task_success"] == 1 for r in result["records"])
