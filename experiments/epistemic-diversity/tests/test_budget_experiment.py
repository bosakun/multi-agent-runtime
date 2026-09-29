"""Fake HTTP exercises the exact diagnostic dispatch and fail-stop path, never Ollama."""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from operational_diagnostics import budget_experiment as experiment


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "SECRET_FAKE_KEY")
    monkeypatch.setenv("MAX_MODEL_CALLS", "60")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("MODEL_BASE_URL", raising=False)
    seal, campaign = tmp_path / "seal.json", tmp_path / "campaign"
    experiment.prepare(seal, campaign)
    return seal, campaign


def transport_for(errors=None):
    bodies = []
    active = 0
    maximum_active = 0

    async def handler(request):
        nonlocal active, maximum_active
        path = request.url.path
        if path == "/api/version":
            return httpx.Response(200, json={"version": "fixture"})
        if path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": "qwen3:14b", "digest": "fixture"}]}
            )
        if path == "/api/show":
            return httpx.Response(
                200, json={"details": {}, "capabilities": ["completion", "thinking"]}
            )
        assert path == "/v1/chat/completions"
        active += 1
        maximum_active = max(maximum_active, active)
        await asyncio.sleep(0)
        body = json.loads(request.content)
        bodies.append(body)
        try:
            error = (errors or {}).get(len(bodies))
            if error == "transport":
                raise httpx.ConnectError("SECRET_TRANSPORT_BODY")
            if error == "timeout":
                raise httpx.ReadTimeout("SECRET_TIMEOUT_BODY")
            if error == "http":
                return httpx.Response(500, text="SECRET_SERVER_BODY")
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
            context = json.loads(body["messages"][1]["content"])
            if context["agent_id"] == "synthesizer":
                output.update(conclusion="fixture", decision_summary="fixture")
            if error == "schema":
                output = {"invalid": "SECRET_MODEL_TEXT"}
            usage = {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
            if error == "missing_usage":
                usage = {}
            if error == "excess_usage":
                usage["completion_tokens"] = body["max_tokens"] + 1
            reason = "length" if error == "length" else "stop"
            if error == "unexpected_reason":
                reason = "tool_calls"
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "finish_reason": reason,
                            "message": {
                                "content": json.dumps(output),
                                "reasoning": "SECRET_HIDDEN_REASONING",
                            },
                        }
                    ],
                    "usage": usage,
                },
            )
        finally:
            active -= 1

    return httpx.MockTransport(handler), bodies, lambda: maximum_active


async def test_six_serial_calls_and_only_limit_changes(prepared):
    seal, campaign = prepared
    transport, bodies, concurrency = transport_for({2: "length"})
    destination = await experiment.run_campaign(seal, campaign, transport=transport)
    result = experiment.read(destination)
    assert result["budget_used_after"] == len(bodies) == 6
    assert result["stopped_reason"] is None
    assert concurrency() == 1
    assert result["records"][1]["status"] == "length_terminated"
    for first, second in zip(bodies[::2], bodies[1::2], strict=True):
        assert {first.pop("max_tokens"), second.pop("max_tokens")} == {2048, 4096}
        assert first == second
        assert not {"think", "reasoning", "reasoning_effort", "seed", "tools"} & first.keys()
    for path in campaign.rglob("*.json"):
        assert "SECRET" not in path.read_text()
    with pytest.raises(ValueError, match="already consumed"):
        await experiment.run_campaign(seal, campaign, transport=transport)


@pytest.mark.parametrize(
    "failure,code",
    [
        ("transport", "provider_transport_error"),
        ("timeout", "diagnostic_timeout"),
        ("http", "provider_http_500"),
        ("schema", "diagnostic_schema_invalid"),
        ("missing_usage", "diagnostic_missing_required_metadata"),
        ("excess_usage", "diagnostic_backend_limit_violation"),
        ("unexpected_reason", "diagnostic_unexpected_finish_reason"),
    ],
)
async def test_other_failures_stop_without_retry(prepared, failure, code):
    seal, campaign = prepared
    transport, bodies, _ = transport_for({1: failure})
    result = experiment.read(await experiment.run_campaign(seal, campaign, transport=transport))
    assert len(bodies) == result["budget_used_after"] == 1
    assert result["stopped_reason"] == code
    assert result["records"][0]["attempts"] == 1
    assert [r["status"] for r in result["records"]] == ["failed"] + ["unexecuted"] * 5
    assert all("SECRET" not in p.read_text() for p in campaign.rglob("*.json"))


async def test_budget_refused_before_preflight_or_generation(prepared, monkeypatch):
    seal, campaign = prepared
    monkeypatch.setenv("MAX_MODEL_CALLS", "5")
    transport, bodies, _ = transport_for()
    with pytest.raises(ValueError, match="all six"):
        await experiment.run_campaign(seal, campaign, transport=transport)
    assert bodies == []
    assert sorted(p.name for p in campaign.iterdir()) == ["binding.json"]


def test_prepare_refuses_overwrite_and_historical_descendants(prepared, tmp_path):
    seal, campaign = prepared
    before = (campaign / "binding.json").read_bytes()
    with pytest.raises(ValueError, match="immutable"):
        experiment.prepare(seal, campaign)
    for name in ("qwen3-14b", "qwen3-14b-protocol22", "qwen3-14b-protocol23"):
        with pytest.raises(ValueError, match="Historical campaign"):
            experiment.prepare(tmp_path / "unused.json", experiment.ROOT / "runs" / name / "child")
    assert (campaign / "binding.json").read_bytes() == before


async def test_rehashed_binding_settings_rejected(prepared):
    seal, campaign = prepared
    binding = experiment.read(campaign / "binding.json")
    binding["temperature"] = 1
    binding["sha256"] = experiment.digest({k: v for k, v in binding.items() if k != "sha256"})
    (campaign / "binding.json").write_text(json.dumps(binding))
    transport, bodies, _ = transport_for()
    with pytest.raises(ValueError, match="fixed controls"):
        await experiment.run_campaign(seal, campaign, transport=transport)
    assert bodies == []


async def test_preflight_failure_retains_unexecuted_cells_and_zero_calls(prepared):
    seal, campaign = prepared
    transport = httpx.MockTransport(lambda _: httpx.Response(503, text="SECRET_SERVER_BODY"))
    result = experiment.read(await experiment.run_campaign(seal, campaign, transport=transport))
    assert result["budget_used_after"] == 0
    assert result["stopped_reason"] == "diagnostic_preflight_HTTPStatusError"
    assert all(r["status"] == "unexecuted" for r in result["records"])
    assert "SECRET" not in json.dumps(result)


def test_stale_seal_rejected_without_campaign_mutation(prepared, monkeypatch):
    seal, campaign = prepared
    monkeypatch.setattr(experiment, "sources", lambda: {"modified": "source"})
    with pytest.raises(ValueError, match="source/plan changed"):
        experiment.verify_binding(seal, campaign)
    assert sorted(p.name for p in campaign.iterdir()) == ["binding.json"]
