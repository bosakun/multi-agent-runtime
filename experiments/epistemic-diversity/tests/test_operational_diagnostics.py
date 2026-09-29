"""Future observer tests use fake transport only; sealed runner behavior is untouched."""

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from operational_diagnostics.campaign import save_report, summarize
from operational_diagnostics.http_metadata import MetadataRecorder, response_metadata

from app.core.errors import RuntimeFault
from app.core.models import AgentContext, ModelConfig
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelRequest


def model_request():
    return ModelRequest(
        agent_id="worker_0",
        instruction="Fixture instruction, unchanged by observer.",
        context=AgentContext(agent_id="worker_0", run_id="a" * 32, inputs={}),
        config=ModelConfig(model="fixture", max_output_tokens=2048, temperature=0),
        output_schema={"type": "object", "properties": {}, "additionalProperties": False},
    )


@pytest.mark.parametrize("reasoning_field", ["reasoning", "reasoning_content"])
@pytest.mark.parametrize("content", ["", '{"unfinished":', "{}"])
async def test_truncation_observed_but_not_salvaged(tmp_path, reasoning_field, content):
    dispatched = []

    def handler(request):
        dispatched.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": content, reasoning_field: "HIDDEN_REASONING_SECRET"},
                    }
                ],
                "usage": {"prompt_tokens": 700, "completion_tokens": 2048, "total_tokens": 2748},
                "debug": "SECRET_DEBUG",
            },
        )

    async with httpx.AsyncClient(
        base_url="https://fixture.invalid/v1/",
        transport=httpx.MockTransport(handler),
        event_hooks={"response": [MetadataRecorder(tmp_path)]},
    ) as client:
        with pytest.raises(RuntimeFault, match="provider_output_truncated"):
            await OpenAICompatibleProvider(
                client, "SECRET_KEY", token_limit_parameter="max_tokens"
            ).generate(model_request())
    assert len(dispatched) == 1
    assert dispatched[0]["max_tokens"] == 2048
    assert dispatched[0]["temperature"] == 0
    assert not {"think", "reasoning", "reasoning_effort"} & dispatched[0].keys()
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    text = files[0].read_text()
    assert "SECRET" not in text and "unfinished" not in text
    metadata = json.loads(text)
    assert metadata["finish_reason"] == "length"
    assert metadata["generated_tokens"] == 2048
    assert metadata["reasoning_tokens"] is None
    assert metadata["reasoning_characters"] == len("HIDDEN_REASONING_SECRET")
    assert metadata["final_content_characters"] == len(content)
    assert metadata["run_id"] == "a" * 32
    assert metadata["agent_id"] == "worker_0"


@pytest.mark.parametrize("reason", ["stop", "length"])
async def test_observer_preserves_wire_body_and_provider_result(tmp_path, reason):
    bodies = []

    def handler(request):
        bodies.append(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": reason, "message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 3},
            },
        )

    for hooks in ({}, {"response": [MetadataRecorder(tmp_path)]}):
        async with httpx.AsyncClient(
            base_url="https://fixture.invalid/v1/",
            transport=httpx.MockTransport(handler),
            event_hooks=hooks,
        ) as client:
            provider = OpenAICompatibleProvider(client, "fixture")
            if reason == "length":
                with pytest.raises(RuntimeFault, match="provider_output_truncated"):
                    await provider.generate(model_request())
            else:
                result = await provider.generate(model_request())
                assert result.output == {} and result.usage.output_tokens == 3
    assert bodies[0] == bodies[1]
    assert "max_completion_tokens" in json.loads(bodies[0])


@pytest.mark.parametrize("value", [None, -1, True, "2048"])
async def test_missing_or_invalid_usage_never_becomes_zero(value):
    metadata = await response_metadata(
        httpx.Response(
            200,
            json={"choices": [], "usage": {"completion_tokens": value}},
        )
    )
    assert metadata.generated_tokens is None
    assert metadata.final_content_characters is None


@pytest.mark.parametrize("status,body", [(500, "SECRET_SERVER_ERROR"), (200, "[1,2]")])
async def test_nonstandard_response_text_not_logged(tmp_path, status, body):
    response = httpx.Response(
        status, text=body, request=httpx.Request("POST", "https://fixture.invalid/", content=b"{}")
    )
    await MetadataRecorder(tmp_path)(response)
    text = next(tmp_path.glob("*.json")).read_text()
    assert "SECRET" not in text
    assert json.loads(text)["generated_tokens"] is None


async def test_recorder_never_overwrites_and_records_reasoning_count_only(tmp_path):
    response = httpx.Response(
        200,
        json={
            "choices": [{"finish_reason": "SECRET_REASON", "message": {"content": "{}"}}],
            "usage": {"completion_tokens_details": {"reasoning_tokens": 200}},
        },
        request=httpx.Request("POST", "https://fixture.invalid/", content=b"{}"),
    )
    recorder = MetadataRecorder(tmp_path)
    await recorder(response)
    previous = {p: p.read_bytes() for p in tmp_path.glob("*.json")}
    await recorder(response)
    assert len(list(tmp_path.glob("*.json"))) == 2
    for path, content in previous.items():
        assert path.read_bytes() == content
        metadata = json.loads(content)
        assert metadata["finish_reason"] == "other"
        assert metadata["reasoning_tokens"] == 200
        assert "SECRET" not in content.decode()


def phase_fixture(tmp_path):
    phase = tmp_path / "campaign/pilot"
    (phase / "call-journal").mkdir(parents=True)
    (phase / "traces").mkdir()
    call = {
        "run_id": "a" * 32,
        "agent_id": "worker_0",
        "error": "RuntimeFault",
        "latency_ms": 431000,
        "response": None,
        "request": {"config": {"max_output_tokens": 2048}},
    }
    (phase / "call-journal/0001.json").write_text(json.dumps(call))
    trace = {
        "run": {
            "state": {
                "agent_runs": [
                    {
                        "node_id": "worker_0",
                        "status": "failed",
                        "attempts": 1,
                        "latency_ms": 431000,
                        "result": {"error": {"code": "provider_output_truncated"}},
                    }
                ]
            }
        }
    }
    (phase / "traces/fixture.json").write_text(json.dumps(trace))
    data = {
        "metadata": {
            "protocol_version": "pilot-2.3",
            "executed_runs": 1,
            "budget_used_after": 1,
            "stopped_reason": "failure",
        },
        "records": [
            {
                "run_id": "a" * 32,
                "task_id": "fixture",
                "condition": "C3",
                "status": "partial",
                "errors": ["provider_output_truncated"],
                "trace_file": "traces/fixture.json",
                "metrics": {
                    "model_calls": 1,
                    "latency_ms": 431000,
                    "context_leaks": 0,
                    "result_leaks": 0,
                    "gold_leaks": 0,
                },
                "human_review": {"gold": "DO_NOT_EXPORT_GOLD"},
            }
        ],
    }
    (phase / "results.json").write_text(json.dumps(data))
    return phase


def test_offline_report_keeps_unknown_failed_usage_and_input_immutable(tmp_path):
    phase = phase_fixture(tmp_path)
    baseline = {p: p.read_bytes() for p in phase.rglob("*") if p.is_file()}
    summary = summarize(phase)
    assert summary["unknown_usage_calls"] == 1
    assert summary["calls"][0]["generated_tokens"] is None
    assert summary["calls"][0]["near_limit"] is None
    assert summary["failures"][0]["failed_nodes"][0]["latency_seconds"] == 431
    assert summary["failures"][0]["synthesizer_executed"] is False
    output = tmp_path / "report"
    save_report(phase, output)
    assert "DO_NOT_EXPORT_GOLD" not in (output / "operational.json").read_text()
    with pytest.raises(FileExistsError):
        save_report(phase, output)
    for path, content in baseline.items():
        assert path.read_bytes() == content


def test_offline_report_refuses_campaign_write_and_escaped_trace(tmp_path):
    phase = phase_fixture(tmp_path)
    with pytest.raises(ValueError, match="outside campaigns"):
        save_report(phase, phase / "report")
    data = json.loads((phase / "results.json").read_text())
    data["records"][0]["trace_file"] = "../outside.json"
    (phase / "results.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Trace path escapes"):
        summarize(phase)
