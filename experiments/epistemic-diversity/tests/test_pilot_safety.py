"""Real adapter exercised over fake HTTP: no external services or credentials."""

import json

import httpx
import pytest
from epistemic.benchmark_v2 import SEED, VERSION
from epistemic.freeze import bind_model, seal
from epistemic.mock import respond
from epistemic.models import ModelSettings
from epistemic.paths import read_json
from epistemic.runner import execute_campaign

from app.core.models import AgentContext, ModelConfig
from app.llm.provider import ModelRequest


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    import epistemic.freeze as freezing

    monkeypatch.setattr(freezing, "frozen_files", lambda: {"test_fixture_only": "stable"})
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-not-a-real-credential")
    monkeypatch.setenv("MODEL_BASE_URL", "https://example.invalid/v1/")
    frozen = tmp_path / "freeze.json"
    binding = tmp_path / "binding.json"
    seal(frozen)
    bind_model(binding, "test-model", "https://example.invalid/v1/", frozen)
    return frozen, binding


@pytest.mark.parametrize("failure", [False, True])
async def test_real_adapter_pilot_caps_and_stop(tmp_path, monkeypatch, prepared, failure):
    import epistemic.runner as runner

    frozen, binding = prepared
    dispatched = []

    async def handler(request):
        body = json.loads(request.content)
        dispatched.append(body)
        assert body["model"] == "test-model"
        assert body["temperature"] == 0
        assert body["max_completion_tokens"] == 2048
        if failure:
            return httpx.Response(429, json={"error": "synthetic rate limit"})
        context = AgentContext.model_validate_json(body["messages"][1]["content"])
        output = respond(
            ModelRequest(
                agent_id=context.agent_id,
                context=context,
                instruction=body["messages"][0]["content"],
                config=ModelConfig(provider="real", model="test-model"),
                output_schema=body["response_format"]["json_schema"]["schema"],
            )
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps(output.output)}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10},
            },
        )

    original = httpx.AsyncClient
    monkeypatch.setattr(
        runner.httpx,
        "AsyncClient",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(handler)),
    )
    result = await execute_campaign(
        tmp_path / "campaign",
        "pilot",
        1,
        ModelSettings(provider="real", model="test-model"),
        SEED,
        60,
        VERSION,
        binding,
        frozen,
    )
    data = read_json(result)
    assert len(dispatched) <= 48
    assert data["metadata"]["budget_used_after"] == len(dispatched)
    assert len(list((result.parent / "call-journal").glob("*.json"))) == len(dispatched)
    assert (result.parent / "pilot-human-review.md").exists()
    assert "fake-key-not" not in result.read_text()
    if failure:
        assert len(data["records"]) == 1
        assert data["records"][0]["errors"]
        assert data["metadata"]["stopped_reason"]
        assert len(dispatched) == 3
    else:
        assert len(dispatched) == 48 and len(data["records"]) == 12
        assert all(r["metrics"]["task_success"] == 1 for r in data["records"])


async def test_insufficient_real_pilot_budget_is_not_silently_truncated(tmp_path, prepared):
    frozen, binding = prepared
    with pytest.raises(ValueError, match="fixed 48-call pilot"):
        await execute_campaign(
            tmp_path / "too-small",
            "pilot",
            1,
            ModelSettings(provider="real", model="test-model"),
            SEED,
            47,
            VERSION,
            binding,
            frozen,
        )
    assert not (tmp_path / "too-small/pilot").exists()
