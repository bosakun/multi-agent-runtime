"""Local guards from 2.2, retained under the current amendment; no live model calls."""

import asyncio
import json

import httpx
import pytest
from epistemic.benchmark import load_task, partition
from epistemic.benchmark_v2 import PILOT_IDS, SEED, VERSION
from epistemic.conditions import build_condition, configurations
from epistemic.freeze import (
    bind_model,
    seal,
    validate_binding,
    validate_execution_endpoint,
    validate_local_campaign,
)
from epistemic.mock import respond
from epistemic.models import ModelSettings
from epistemic.paths import digest, read_json, write_json
from epistemic.provider import AuditedProvider, CallBudget
from epistemic.runner import execute_campaign

from app.core.models import AgentContext, ModelConfig
from app.llm.provider import ModelRequest, ModelResponse


def local_settings(provider="mock"):
    return ModelSettings(
        provider=provider, model="qwen3:14b", timeout_seconds=600, execution_profile="local_ollama"
    )


@pytest.fixture
def local_prepared(tmp_path, monkeypatch):
    import epistemic.freeze as freezing

    monkeypatch.setattr(freezing, "frozen_files", lambda: {"fixture": "stable"})
    monkeypatch.setenv("OPENAI_API_KEY", "fake-fixture-key")
    monkeypatch.setenv("MODEL_BASE_URL", "http://127.0.0.1:11434/v1/")
    freeze = tmp_path / "freeze.json"
    seal(freeze)
    campaign = tmp_path / "fresh-local"
    binding = campaign / "binding.json"
    bind_model(
        binding,
        "qwen3:14b",
        "http://127.0.0.1:11434/v1/",
        freeze,
        execution_profile="local_ollama",
        campaign=campaign,
    )
    return freeze, binding, campaign


@pytest.mark.parametrize(
    "override",
    [
        {"timeout_seconds": 90},
        {"timeout_seconds": 300},
        {"temperature": 0.5},
        {"max_output_tokens": 4096},
    ],
)
def test_local_settings_fixed(override):
    with pytest.raises(ValueError, match="Local Ollama requires"):
        ModelSettings.model_validate({**local_settings().model_dump(), **override})


def test_local_endpoint_cannot_apply_to_cloud():
    with pytest.raises(ValueError, match="loopback"):
        validate_execution_endpoint(local_settings(), "https://example.invalid/v1/")
    with pytest.raises(ValueError, match="requires the local_ollama"):
        validate_execution_endpoint(ModelSettings(), "http://127.0.0.1:11434/v1/")


def test_local_binding_new_root_and_old_seal_rejection(local_prepared):
    freeze, path, campaign = local_prepared
    binding = read_json(path)
    validate_binding(path, local_settings("real"), binding["endpoint"], SEED, freeze)
    with pytest.raises(ValueError, match="nonexistent"):
        bind_model(
            campaign / "other.json",
            "qwen3:14b",
            binding["endpoint"],
            freeze,
            execution_profile="local_ollama",
            campaign=campaign,
        )
    validate_local_campaign(binding, campaign, path)
    with pytest.raises(ValueError, match="named in its binding"):
        validate_local_campaign(binding, campaign.parent / "other", path)
    (campaign / "budget.sqlite").touch()
    with pytest.raises(ValueError, match="already contains artifacts"):
        validate_local_campaign(binding, campaign, path)
    binding["freeze_sha256"] = "old-protocol-2.1"
    binding["binding_sha256"] = digest({k: v for k, v in binding.items() if k != "binding_sha256"})
    write_json(path, binding)
    with pytest.raises(ValueError, match="does not match verified freeze"):
        validate_binding(path, local_settings("real"), binding["endpoint"], SEED, freeze)


@pytest.mark.parametrize("condition", ["C2", "C3"])
async def test_local_guard_rejects_reused_root_before_dispatch(local_prepared, condition):
    freeze, path, campaign = local_prepared
    marker = campaign / "retained-result.json"
    marker.write_text(condition)
    with pytest.raises(ValueError, match="already contains artifacts"):
        await execute_campaign(
            campaign, "pilot", 1, local_settings("real"), SEED, 60, VERSION, path, freeze
        )
    assert marker.read_text() == condition
    assert not (campaign / "budget.sqlite").exists()
    assert not (campaign / "pilot").exists()


@pytest.mark.parametrize("task_id", PILOT_IDS)
def test_only_scheduling_and_timeout_change_worker_visibility(task_id):
    task, gold = load_task(task_id)
    groups = partition(task, gold, SEED)
    for config in configurations()[2:4]:
        a = build_condition(task, config, groups, SEED, ModelSettings())
        b = build_condition(
            task,
            config,
            groups,
            SEED,
            local_settings().model_copy(update={"model": "public-rule-mock-v2"}),
        )
        assert a[0].max_parallel == 3 and b[0].max_parallel == 1
        assert a[2:] == b[2:]
        for key in a[1]:
            standard, local = a[1][key], b[1][key]
            assert standard.context == local.context
            assert standard.instruction == local.instruction
            assert standard.model == local.model
            assert standard.publish_to == local.publish_to
            assert standard.execution.timeout_seconds == 90
            assert local.execution.timeout_seconds == 600
        assert all(e.target == "synthesizer" for e in b[0].edges)


async def test_provider_serialization_and_cancellation_budget(tmp_path):
    active = 0
    maximum = 0
    entered = asyncio.Event()
    release = asyncio.Event()

    class BlockingProvider:
        async def generate(self, request):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            entered.set()
            try:
                await release.wait()
                return ModelResponse(output={})
            finally:
                active -= 1

    provider = AuditedProvider(
        BlockingProvider(),
        CallBudget(tmp_path / "budget", 5),
        tmp_path / "journal",
        max_concurrency=1,
    )
    request = ModelRequest(
        agent_id="worker_0",
        context=AgentContext(
            run_id="fixture",
            agent_id="worker_0",
            task="fixture",
            inputs={},
        ),
        instruction="fixture",
        config=ModelConfig(provider="mock", model="fixture"),
        output_schema={},
    )
    first = asyncio.create_task(provider.generate(request))
    await asyncio.wait_for(entered.wait(), 1)
    second = asyncio.create_task(provider.generate(request))
    await asyncio.sleep(0)
    assert provider.budget.used == 1  # waiting dispatch is not charged
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    release.set()
    await second
    assert maximum == 1 and provider.budget.used == 2
    assert provider.calls[0].error == "CancelledError"
    assert len(list((tmp_path / "journal").glob("*.json"))) == 2


async def test_local_profile_mock_pilot_complete(tmp_path, local_prepared):
    freeze, _, _ = local_prepared
    result = await execute_campaign(
        tmp_path / "offline", "pilot", 1, local_settings(), SEED, 60, VERSION, freeze_path=freeze
    )
    data = read_json(result)
    assert data["metadata"]["protocol_version"] == "pilot-2.3"
    assert data["metadata"]["worker_concurrency"] == 1
    assert data["metadata"]["model_concurrency"] == 1
    assert data["metadata"]["budget_used_after"] == 48
    assert len(data["records"]) == 12
    assert all(r["metrics"]["task_success"] == 1 for r in data["records"])
    for path in (result.parent / "call-journal").glob("*.json"):
        context = read_json(path)["request"]["context"]
        if context["agent_id"].startswith("worker_"):
            assert context["artifacts"] == []
        else:
            assert context["knowledge"] == [] and len(context["artifacts"]) == 3


@pytest.mark.parametrize("truncated", [False, True])
async def test_local_adapter_fake_http_serial_pilot(local_prepared, monkeypatch, truncated):
    import epistemic.runner as runner

    freeze, binding, campaign = local_prepared
    active = maximum = 0
    calls = []

    async def handler(request):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        try:
            body = json.loads(request.content)
            calls.append(body)
            assert body["temperature"] == 0 and body["max_tokens"] == 2048
            assert "max_completion_tokens" not in body
            assert not {"think", "reasoning", "reasoning_effort"} & body.keys()
            if truncated:
                return httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": "{}"}, "finish_reason": "length"}]},
                )
            context = AgentContext.model_validate_json(body["messages"][1]["content"])
            output = respond(
                ModelRequest(
                    agent_id=context.agent_id,
                    context=context,
                    instruction=body["messages"][0]["content"],
                    config=ModelConfig(provider="real", model="qwen3:14b"),
                    output_schema=body["response_format"]["json_schema"]["schema"],
                )
            )
            await asyncio.sleep(0.001)
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {"content": json.dumps(output.output)},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 10},
                },
            )
        finally:
            active -= 1

    original = httpx.AsyncClient

    def fake_client(**kwargs):
        assert kwargs["timeout"] == 600
        return original(**kwargs, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(runner.httpx, "AsyncClient", fake_client)
    result = await execute_campaign(
        campaign, "pilot", 1, local_settings("real"), SEED, 60, VERSION, binding, freeze
    )
    assert maximum == 1 and len(calls) == (3 if truncated else 48)
    data = read_json(result)
    assert len(data["records"]) == (1 if truncated else 12)
    if truncated:
        assert data["metadata"]["stopped_reason"]
        assert "provider_output_truncated" in data["records"][0]["errors"]
    else:
        assert all(record["errors"] == [] for record in data["records"])
    for path in (result.parent / "call-journal").glob("*.json"):
        assert read_json(path)["backend_request"] == {
            "token_limit_parameter": "max_tokens",
            "token_limit_fields": {"max_tokens": 2048},
            "thinking_fields": [],
        }
    with pytest.raises(ValueError, match="Phase already exists"):
        await execute_campaign(
            campaign, "pilot", 1, local_settings("real"), SEED, 60, VERSION, binding, freeze
        )
