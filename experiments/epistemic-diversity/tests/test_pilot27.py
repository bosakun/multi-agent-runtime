"""Context projection, wire provenance, fail-stop, immutable gates and full Pilot grid."""

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bounded_pilot import pilot27 as pilot
from bounded_pilot.contract import BoundedAuditedProvider as NativeAuditedProvider
from bounded_pilot.contract import bounded_schema as scoped_schema
from bounded_pilot.contract import validate_citation_lengths
from native_pilot.provider import native_body, parse_native
from prospective_pilot.budget import ClosedCallBudget

from app.core.errors import RuntimeFault
from app.core.models import AgentContext, ModelConfig
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelRequest


def fixture_request():
    from epistemic.models import WorkerOutput

    return ModelRequest(
        agent_id="worker_0",
        instruction="Original instruction",
        context=AgentContext(agent_id="worker_0", run_id="wire-test"),
        config=ModelConfig(model="qwen3:14b", temperature=0, max_output_tokens=4096),
        output_schema=WorkerOutput.model_json_schema(),
    )


async def test_native_preserves_exact_original_prompt_messages():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )

    request = fixture_request()
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:11434/v1/",
        transport=httpx.MockTransport(handler),
    ) as client:
        await OpenAICompatibleProvider(client, "ollama").generate(request)
    assert native_body(request)["messages"] == seen[0]["messages"]


@pytest.mark.parametrize("field", ["think", "options", "format"])
async def test_native_wire_drift_rejected_before_dispatch(tmp_path, field):
    provider = NativeAuditedProvider(
        MockProvider(lambda _: {}),
        ClosedCallBudget(tmp_path / "budget.sqlite", 1),
    )
    request = fixture_request()
    request.output_schema = scoped_schema(request.output_schema, request.context)
    from epistemic.models import CallRecord

    provider.calls.append(
        CallRecord(
            run_id=request.context.run_id,
            agent_id=request.agent_id,
            request=request.model_dump(mode="json"),
        )
    )
    body = native_body(request)
    body[field] = {} if field != "think" else True
    with pytest.raises(ValueError, match="differs"):
        await provider.audit_http_request(
            httpx.Request(
                "POST",
                "http://127.0.0.1:11434/api/chat",
                json=body,
            )
        )


@pytest.fixture
async def bound(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "CAMPAIGN", tmp_path / "campaign")
    monkeypatch.setattr(pilot, "FREEZE", tmp_path / "freeze.json")
    monkeypatch.setattr(pilot, "MOCK", tmp_path / "mock")
    monkeypatch.setattr(pilot, "sources", lambda: {"fixture": "sealed"})
    monkeypatch.setattr(pilot, "diagnostic_gate", lambda: {"sha256": "diagnostic-passed"})
    monkeypatch.setattr(pilot, "verify_historical", lambda: {"freeze_sha256": "base"})
    monkeypatch.setenv("MAX_MODEL_CALLS", "60")

    async def host_probe(*_):
        return {"ollama": {"version": "fake", "digest": pilot.EXPECTED_DIGEST}}

    monkeypatch.setattr(pilot, "host_probe", host_probe)
    path = await pilot.execute(mock=True, mock_output=pilot.MOCK)
    assert pilot.integral(json.loads(path.read_text(encoding="utf-8")))
    await pilot.prepare()


def fake_transport(*, invalid_id=False, truncate=False):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        context = AgentContext.model_validate_json(body["messages"][1]["content"])
        assert body["options"] == {"temperature": 0, "num_predict": 4096, "num_ctx": 8192}
        assert body["think"] is False and body["stream"] is False
        assert "tools" not in body and request.url.path == "/api/chat"
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
        if invalid_id and len(bodies) == 1:
            output["uncertainty"]["evidence_ids"] = ["none"]
        if context.agent_id == "synthesizer":
            output.update(conclusion="fake", decision_summary="fake")
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "length" if truncate and len(bodies) == 1 else "stop",
                "message": {"role": "assistant", "content": json.dumps(output), "thinking": ""},
                "prompt_eval_count": 20,
                "eval_count": 30,
            },
        )

    return httpx.MockTransport(handler), bodies


async def test_full_fake_http_grid_journals_effective_schema_and_refuses_reuse(bound):
    transport, bodies = fake_transport()
    path = await pilot.execute(transport=transport)
    result = json.loads(path.read_text(encoding="utf-8"))
    assert pilot.integral(result) and len(bodies) == 48
    assert result["metadata"]["budget_used_after"] == 48
    journals = list((path.parent / "call-journal").glob("*.json"))
    assert len(journals) == 48
    for journal_path in journals:
        record = json.loads(journal_path.read_text(encoding="utf-8"))
        context = AgentContext.model_validate(record["request"]["context"])
        assert record["backend_request"]["allowed_evidence_ids"] == sorted(context.evidence_scope())
        assert record["request"]["output_schema"] == scoped_schema(
            record["request"]["output_schema"],
            context,
        )
    observations = list(path.parent.joinpath("http-observations").glob("*.json"))
    assert len(observations) == 48
    assert all("PRIVATE" not in p.read_text(encoding="utf-8") for p in observations)
    with pytest.raises(ValueError, match="consumed"):
        await pilot.execute(transport=transport)
    assert len(bodies) == 48


@pytest.mark.parametrize("failure", ["invalid_id", "truncate"])
async def test_backend_noncompliance_remains_failure_without_repair_or_retry(bound, failure):
    transport, bodies = fake_transport(**{failure: True})
    result = json.loads((await pilot.execute(transport=transport)).read_text(encoding="utf-8"))
    assert not pilot.integral(result) and len(result["records"]) == 1
    assert len(bodies) == 3
    expected = (
        "unknown_evidence_reference" if failure == "invalid_id" else "provider_output_truncated"
    )
    assert expected in result["records"][0]["errors"]
    assert result["metadata"]["stopped_reason"]


async def test_backend_drift_blocks_dispatch_and_source_drift_invalidates_seal(bound, monkeypatch):
    async def changed_host(*_):
        return {"ollama": {"version": "changed", "digest": pilot.EXPECTED_DIGEST}}

    monkeypatch.setattr(pilot, "host_probe", changed_host)
    transport, bodies = fake_transport()
    with pytest.raises(ValueError, match="changed"):
        await pilot.execute(transport=transport)
    assert not bodies
    assert sorted(p.name for p in pilot.CAMPAIGN.iterdir()) == ["binding.json"]
    monkeypatch.setattr(pilot, "sources", lambda: {"fixture": "changed"})
    with pytest.raises(ValueError, match="mismatch"):
        pilot.verify_binding()


async def test_insufficient_budget_cannot_silently_reduce_grid(bound, monkeypatch):
    monkeypatch.setenv("MAX_MODEL_CALLS", "47")
    transport, bodies = fake_transport()
    with pytest.raises(ValueError, match="48-call"):
        await pilot.execute(transport=transport)
    assert not bodies


@pytest.mark.parametrize(
    "change,code",
    [
        ({"done_reason": "length"}, "provider_output_truncated"),
        ({"done": False}, "provider_incomplete_response"),
        ({"eval_count": 4097}, "provider_context_or_output_budget_exceeded"),
        ({"prompt_eval_count": 4097}, "provider_context_or_output_budget_exceeded"),
        ({"eval_count": True}, "provider_invalid_usage"),
        ({"message": {"content": "{}", "thinking": "SECRET"}}, "unexpected_thinking_output"),
        ({"message": {"content": "{}", "tool_calls": [{}]}}, "unexpected_tool_calls"),
    ],
)
def test_native_parser_fail_closed(change, code):
    data = {
        "done": True,
        "done_reason": "stop",
        "message": {"content": "{}"},
        "prompt_eval_count": 10,
        "eval_count": 20,
    }
    data.update(change)
    with pytest.raises(RuntimeFault) as error:
        parse_native(data)
    assert error.value.code == code


async def test_native_failed_response_observation_never_saves_thinking(bound):
    transport, bodies = fake_transport()
    original = transport.handler

    def with_thinking(request):
        response = original(request)
        data = response.json()
        data["message"]["thinking"] = "SECRET_HIDDEN_REASONING"
        return httpx.Response(200, json=data)

    result_path = await pilot.execute(transport=httpx.MockTransport(with_thinking))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert not pilot.integral(result)
    assert len(bodies) == 3
    assert "unexpected_thinking_output" in result["records"][0]["errors"]
    observations = list((result_path.parent / "http-observations").glob("*.json"))
    assert len(observations) == 3
    assert all("SECRET_HIDDEN_REASONING" not in p.read_text(encoding="utf-8") for p in observations)
    assert all(
        json.loads(p.read_text(encoding="utf-8"))["thinking_chars"] > 0 for p in observations
    )


def test_all_citation_arrays_bound_to_context_without_mutating_original():
    from epistemic.models import FinalOutput, WorkerOutput

    from app.core.models import Knowledge

    context = AgentContext(
        agent_id="worker_0",
        run_id="scope",
        knowledge=[
            Knowledge(id="a", content="first"),
            Knowledge(id="b", content="second"),
        ],
    )

    def citation_limits(value):
        result = []
        if isinstance(value, dict):
            properties = value.get("properties", {})
            if "evidence_ids" in properties:
                result.append(properties["evidence_ids"])
            for child in value.values():
                result.extend(citation_limits(child))
        elif isinstance(value, list):
            for child in value:
                result.extend(citation_limits(child))
        return result

    for model in [WorkerOutput, FinalOutput]:
        original = model.model_json_schema()
        before = json.dumps(original)
        bounded = scoped_schema(original, context)
        arrays = citation_limits(bounded)
        assert len(arrays) == 2
        assert all(a["maxItems"] == 2 and a["items"]["enum"] == ["a", "b"] for a in arrays)
        assert json.dumps(original) == before
    validate_citation_lengths({"uncertainty": {"evidence_ids": ["a", "b"]}}, 2)
    with pytest.raises(RuntimeFault, match="citation_array_limit_exceeded"):
        validate_citation_lengths({"uncertainty": {"evidence_ids": ["a"] * 3}}, 2)


async def test_backend_ignoring_maxitems_is_rejected_without_trimming_or_retry(bound):
    transport, bodies = fake_transport()
    original = transport.handler

    def overlong(request):
        response = original(request)
        data = response.json()
        body = json.loads(request.content)
        context = AgentContext.model_validate_json(body["messages"][1]["content"])
        allowed = sorted(context.evidence_scope())
        output = json.loads(data["message"]["content"])
        output["uncertainty"]["evidence_ids"] = [allowed[0]] * (len(allowed) + 1)
        data["message"]["content"] = json.dumps(output)
        return httpx.Response(200, json=data)

    path = await pilot.execute(transport=httpx.MockTransport(overlong))
    result = json.loads(path.read_text(encoding="utf-8"))
    assert not pilot.integral(result) and len(bodies) == 3
    assert "citation_array_limit_exceeded" in result["records"][0]["errors"]
    assert len(result["records"]) == 1
