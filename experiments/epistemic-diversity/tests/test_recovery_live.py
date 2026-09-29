"""Newly authorized diagnostic, tested with fake HTTP before source sealing."""

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from operational_recovery import live_diagnostic as live


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "CAMPAIGN", tmp_path / "campaign")
    monkeypatch.setattr(live, "files", lambda: {"test": "sealed"})
    monkeypatch.setenv("MAX_MODEL_CALLS", "60")

    async def preflight(*_):
        return {"backend": "fake"}

    monkeypatch.setattr(live, "preflight", preflight)
    live.prepare()


def handler_for(failures):
    bodies = []

    def handler(req):
        body = json.loads(req.content)
        bodies.append(body)
        output = {
            "claims": [],
            "insights": [],
            "uncertainty": {
                "confidence": None,
                "assumptions": [],
                "unknowns": [],
                "evidence_ids": [],
            },
        }
        if json.loads(body["messages"][1]["content"])["agent_id"] == "synthesizer":
            output.update(conclusion="fake", decision_summary="fake")
        reason = failures.get(len(bodies), "stop")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": reason,
                        "message": {"content": json.dumps(output), "reasoning": "PRIVATE_THOUGHT"},
                    }
                ],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": body["max_tokens"] - 1,
                    "total_tokens": body["max_tokens"] + 19,
                },
            },
        )

    return httpx.MockTransport(handler), bodies


async def test_diagnostic_baseline_length_then_gate_and_no_reuse(prepared):
    transport, bodies = handler_for({1: "length"})
    result = json.loads((await live.run(transport=transport)).read_text())
    assert result["pilot_gate"] is True
    assert result["budget_used_after"] == len(bodies) == 3
    first, second = bodies[:2]
    assert first.pop("max_tokens") == 2048
    assert second.pop("max_tokens") == 4096
    assert first == second
    assert "PRIVATE_THOUGHT" not in json.dumps(result)
    with pytest.raises(ValueError, match="consumed"):
        await live.run(transport=transport)
    assert len(bodies) == 3


async def test_candidate_length_stops_and_never_approves_pilot(prepared):
    transport, bodies = handler_for({2: "length"})
    result = json.loads((await live.run(transport=transport)).read_text())
    assert not result["pilot_gate"]
    assert result["budget_used_after"] == len(bodies) == 2
    assert result["stopped_reason"] == "provider_output_truncated"


async def test_diagnostic_budget_before_network(prepared, monkeypatch):
    monkeypatch.setenv("MAX_MODEL_CALLS", "50")
    transport, bodies = handler_for({})
    with pytest.raises(ValueError, match="48-call"):
        await live.run(transport=transport)
    assert bodies == []
