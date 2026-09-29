"""Compatibility controls and historical preservation; never invoke a live backend."""

import hashlib

import httpx
import pytest
from epistemic.benchmark_v2 import PILOT_IDS, SEED, VERSION
from epistemic.freeze import (
    FREEZE_PATH,
    PROTOCOL_VERSION,
    bind_model,
    reject_historical_path,
    seal,
    validate_binding,
    verify,
)
from epistemic.models import ModelSettings
from epistemic.paths import REPO, ROOT, digest, read_json, write_json
from epistemic.provider import AuditedProvider, CallBudget
from epistemic.runner import execute_campaign

from app.core.models import AgentContext, ModelConfig
from app.llm.mock_provider import MockProvider
from app.llm.provider import ModelRequest, ModelResponse


def test_profile_configuration_is_explicit():
    standard = ModelSettings()
    local = ModelSettings(execution_profile="local_ollama", timeout_seconds=600)
    assert standard.timeout_seconds == 90
    assert standard.backend_token_limit_parameter == "max_completion_tokens"
    assert local.backend_token_limit_parameter == "max_tokens"
    assert standard.temperature == local.temperature == 0
    assert standard.max_output_tokens == local.max_output_tokens == 2048
    assert FREEZE_PATH.name == "benchmark-2.0.0-protocol-2.3.json"


@pytest.mark.parametrize("protocol", ["pilot-2.1", "pilot-2.2"])
def test_old_signed_freeze_rejected(tmp_path, monkeypatch, protocol):
    import epistemic.freeze as freezing

    monkeypatch.setattr(freezing, "frozen_files", lambda: {"fixture": "stable"})
    path = tmp_path / "freeze.json"
    content = seal(path)
    content["protocol_version"] = protocol
    content["freeze_sha256"] = digest(
        {key: value for key, value in content.items() if key != "freeze_sha256"}
    )
    write_json(path, content)
    with pytest.raises(ValueError, match="historical freezes are archival"):
        verify(path)


@pytest.mark.parametrize("name", ["qwen3-14b", "qwen3-14b-protocol22"])
def test_historical_roots_and_descendants_rejected(name):
    for suffix in ("", "nested-new-campaign", "new-binding.json"):
        with pytest.raises(ValueError, match="Historical campaign is protected"):
            reject_historical_path(ROOT / "runs" / name / suffix)


@pytest.mark.parametrize(
    "field,value",
    [
        ("protocol_version", "pilot-2.2"),
        ("backend_token_limit_parameter", "max_completion_tokens"),
        ("planned_calls", 47),
        ("seed", SEED + 1),
        ("conditions", ["C3", "C2"]),
        ("task_ids", list(reversed(PILOT_IDS))),
        ("execution_controls", {"timeout_seconds": 300}),
    ],
)
def test_rehashed_binding_mismatch_rejected(tmp_path, monkeypatch, field, value):
    import epistemic.freeze as freezing

    monkeypatch.setattr(freezing, "frozen_files", lambda: {"fixture": "stable"})
    frozen = tmp_path / "freeze.json"
    seal(frozen)
    campaign = tmp_path / "new-local"
    binding = campaign / "binding.json"
    endpoint = "http://127.0.0.1:11434/v1/"
    content = bind_model(
        binding,
        "qwen3:14b",
        endpoint,
        frozen,
        execution_profile="local_ollama",
        campaign=campaign,
    )
    assert content["protocol_version"] == PROTOCOL_VERSION
    content[field] = value
    content["binding_sha256"] = digest(
        {key: item for key, item in content.items() if key != "binding_sha256"}
    )
    write_json(binding, content)
    with pytest.raises(ValueError):
        validate_binding(
            binding,
            ModelSettings(
                provider="real",
                model="qwen3:14b",
                execution_profile="local_ollama",
                timeout_seconds=600,
            ),
            endpoint,
            SEED,
            frozen,
        )


@pytest.mark.parametrize(
    "limits",
    [
        {"max_completion_tokens": 2048},
        {"max_tokens": 4096},
        {"max_tokens": 2048, "max_completion_tokens": 2048},
        {},
    ],
)
async def test_wire_guard_refuses_mismatch_before_transport(tmp_path, limits):
    dispatched = []
    provider = AuditedProvider(
        MockProvider(lambda _: ModelResponse(output={})),
        CallBudget(tmp_path / "budget.sqlite", 2),
        tmp_path / "journal",
        token_limit_parameter="max_tokens",
    )
    model_request = ModelRequest(
        agent_id="worker_0",
        instruction="fixture",
        output_schema={},
        context=AgentContext(run_id="fixture", agent_id="worker_0", inputs={}),
        config=ModelConfig(provider="mock", model="fixture"),
    )
    # Reserve a call without involving any external provider.
    await provider.generate(model_request)
    async with httpx.AsyncClient(
        base_url="http://fixture.invalid/v1/",
        transport=httpx.MockTransport(
            lambda request: dispatched.append(request) or httpx.Response(200)
        ),
        event_hooks={"request": [provider.audit_http_request]},
    ) as client:
        with pytest.raises(ValueError, match="Serialized token limit"):
            await client.post(
                "chat/completions",
                json={
                    "messages": [{}, {"content": model_request.context.model_dump_json()}],
                    **limits,
                },
            )
    assert dispatched == []
    journal = read_json(next((tmp_path / "journal").glob("*.json")))
    assert journal["backend_request"]["token_limit_fields"] == limits


@pytest.mark.parametrize(
    "group",
    [
        "benchmark20",
        "protocol21_campaign",
        "protocol22_campaign",
        "prompts",
        "configs",
        "historical_freezes",
    ],
)
def test_preservation_manifest(group):
    manifest = read_json(ROOT / "results/protocol23-preservation.json")
    files = manifest["before"][group]["files"]
    if group.endswith("campaign") and not any((REPO / path).exists() for path in files):
        pytest.skip("Ignored historical campaign is not present in this checkout")
    for path, expected in files.items():
        assert hashlib.sha256((REPO / path).read_bytes()).hexdigest() == expected, path


def test_scientific_sources_match_protocol22_seal():
    historical = read_json(ROOT / "freezes/benchmark-2.0.0-protocol-2.2.json")["files"]
    stable = [
        "conditions.py",
        "metrics.py",
        "analysis.py",
        "reasoning.py",
        "benchmark.py",
        "benchmark_v2.py",
        "mock.py",
        "benchmark_audit.py",
    ]
    for name in stable:
        path = ROOT / "src/epistemic" / name
        assert digest(path.read_text()) == historical[str(path.relative_to(REPO))]
    for directory in (ROOT / "prompts", ROOT / "configs", ROOT / "benchmarks/v2"):
        for path in directory.rglob("*"):
            if path.is_file():
                assert digest(path.read_text()) == historical[str(path.relative_to(REPO))]


async def test_mock_scientific_outputs_match_archived_protocol22(tmp_path, monkeypatch):
    import epistemic.freeze as freezing

    monkeypatch.setattr(freezing, "frozen_files", lambda: {"fixture": "stable"})
    frozen = tmp_path / "freeze.json"
    seal(frozen)
    result = await execute_campaign(
        tmp_path / "current",
        "pilot",
        1,
        ModelSettings(execution_profile="local_ollama", timeout_seconds=600),
        SEED,
        60,
        VERSION,
        freeze_path=frozen,
    )
    current = read_json(result)
    archived = read_json(ROOT / "results/mock-v2p22-local/records.json")
    assert current["metadata"]["budget_used_after"] == 48
    assert len(current["records"]) == len(archived["records"]) == 12
    resources = {"latency_ms", "input_tokens", "output_tokens", "total_tokens", "cost_usd"}
    for before, after in zip(archived["records"], current["records"], strict=True):
        for field in ("task_id", "condition", "assignment", "output", "status", "errors"):
            assert before[field] == after[field], (after["task_id"], field)
        assert {k: v for k, v in before["metrics"].items() if k not in resources} == {
            k: v for k, v in after["metrics"].items() if k not in resources
        }
        before_workers = {
            worker["producer"]: worker["payload"] for worker in before["human_review"]["workers"]
        }
        after_workers = {
            worker["producer"]: worker["payload"] for worker in after["human_review"]["workers"]
        }
        assert before_workers == after_workers


@pytest.mark.parametrize("name", ["qwen3-14b", "qwen3-14b-protocol22"])
async def test_old_campaign_launch_refused_before_any_creation(name, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Historical campaign is protected"):
        await execute_campaign(
            ROOT / "runs" / name / "attempted-resume",
            "pilot",
            1,
            ModelSettings(
                provider="real",
                model="qwen3:14b",
                execution_profile="local_ollama",
                timeout_seconds=600,
            ),
            SEED,
            60,
            VERSION,
        )
    assert not (ROOT / "runs" / name / "attempted-resume").exists()
