"""Saved-input regression plus deliberately simulated responses, not model evidence."""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from operational_recovery.observer import AnswerRecorder, answer_prefix
from operational_recovery.probe import observe_once
from operational_recovery.workload import (
    FAILED_JOURNAL,
    REFERENCE_REQUEST,
    ROOT,
    audit,
    load_saved_request,
    request_digest,
)

from app.core.errors import RuntimeFault
from app.llm.openai_provider import OpenAICompatibleProvider


def envelope(content, *, reason="length", usage=True):
    result = {
        "choices": [
            {
                "finish_reason": reason,
                "message": {"content": content, "reasoning": "HIDDEN_DO_NOT_STORE"},
            }
        ]
    }
    if usage:
        result["usage"] = {
            "prompt_tokens": 910,
            "completion_tokens": 2048,
            "total_tokens": 2958,
        }
    return result


async def test_exact_failed_request_and_truncated_answer_preserved(tmp_path):
    """Simulated partial output is NOT a reconstruction of the lost real output."""
    request = load_saved_request(REFERENCE_REQUEST)
    prefix = '{"claims":[{"subject":"fast_drive_cost","value":"over_budget","evidence_ids":['
    bodies = []

    def handler(req):
        bodies.append(json.loads(req.content))
        return httpx.Response(200, json=envelope(prefix))

    transport = httpx.MockTransport(handler)
    folder = tmp_path / "observation"
    result = await observe_once(request, folder, transport=transport)
    assert result["error"] == "provider_output_truncated"
    assert result["status"] == "failed"
    assert result["real_model_calls"] == 0
    assert result["output"] is None
    assert len(bodies) == 1  # No retry or JSON repair after the provider raises.
    observation = json.loads((folder / "response.json").read_text())
    assert observation["final_answer_prefix"] == prefix
    assert observation["generated_tokens"] == 2048
    assert observation["reasoning_tokens"] is None
    assert observation["answer_capture"] == "partial_answer"
    assert all("HIDDEN_DO_NOT_STORE" not in path.read_text() for path in folder.iterdir())
    async with httpx.AsyncClient(base_url="http://fake.invalid/v1/", transport=transport) as client:
        provider = OpenAICompatibleProvider(client, "fake", token_limit_parameter="max_tokens")
        with pytest.raises(RuntimeFault, match="provider_output_truncated"):
            await provider.generate(request)
    assert bodies[0] == bodies[1]  # Observation did not alter prompts, context, limits or thinking.
    assert bodies[0]["max_tokens"] == 2048
    assert bodies[0]["temperature"] == 0
    assert not {"think", "reasoning_effort", "tools"} & bodies[0].keys()
    before = {path.name: path.read_bytes() for path in folder.iterdir()}
    with pytest.raises(FileExistsError):
        await observe_once(request, folder, transport=transport)
    assert len(bodies) == 2
    assert before == {path.name: path.read_bytes() for path in folder.iterdir()}


@pytest.mark.parametrize(
    "content",
    [
        "<think>HIDDEN_DO_NOT_STORE",
        '<think>HIDDEN_DO_NOT_STORE</think>{"claims":[]}',
        '{"reasoning":"HIDDEN_DO_NOT_STORE","claims":[]}',
        '{"claims":[],"reasoning_content":"HIDDEN_DO_NOT_STORE"}',
        '{"claims":[],"other":"HIDDEN_DO_NOT_STORE"}',
        '{"claims":[]}HIDDEN_DO_NOT_STORE',
        r'{"claims":[],"\u0072easoning":"HIDDEN_DO_NOT_STORE"}',
        "HIDDEN_DO_NOT_STORE",
    ],
)
async def test_no_hidden_reasoning_or_arbitrary_model_prose(tmp_path, content):
    recorder = AnswerRecorder(tmp_path / "response.json")
    await recorder(httpx.Response(200, json=envelope(content)))
    saved = (tmp_path / "response.json").read_text()
    assert "HIDDEN_DO_NOT_STORE" not in saved
    assert json.loads(saved)["final_answer_prefix"] is None


def test_valid_and_partial_answer_prefixes_are_not_repaired():
    for text in ['{"claims":[]}', '{"claims":[', '{"claims":[],"insights":[']:
        assert answer_prefix(text)[0] == text
    assert answer_prefix('{"claims":[],"unrecognized')[0] is None
    assert answer_prefix('{"claims":[]}' + " " * 131072)[0] is None


async def test_reasoning_only_length_observation_and_unknown_usage(tmp_path):
    result = await observe_once(
        load_saved_request(REFERENCE_REQUEST),
        tmp_path / "reasoning-only",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=envelope("", usage=False))
        ),
    )
    assert result["error"] == "provider_output_truncated"
    metadata = result["observation"]
    assert metadata["final_content_characters"] == 0
    assert metadata["reasoning_characters"] == len("HIDDEN_DO_NOT_STORE")
    assert metadata["generated_tokens"] is None  # Missing is not zero.
    assert metadata["final_answer_prefix"] is None


async def test_timeout_saved_without_response_or_fabricated_usage(tmp_path):
    async def handler(_):
        await asyncio.sleep(1)
        raise AssertionError("deadline must expire first")

    result = await observe_once(
        load_saved_request(REFERENCE_REQUEST),
        tmp_path / "timeout",
        transport=httpx.MockTransport(handler),
        timeout_seconds=0.01,
    )
    assert result["error"] == "deadline_exceeded"
    assert result["observation"] is None
    assert not (tmp_path / "timeout/response.json").exists()
    assert json.loads((tmp_path / "timeout/result.json").read_text()) == result


async def test_schema_failure_is_retained_not_repaired(tmp_path):
    result = await observe_once(
        load_saved_request(REFERENCE_REQUEST),
        tmp_path / "schema",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=envelope('{"claims":42}', reason="stop"))
        ),
    )
    assert result["status"] == "failed"
    assert result["error"] == "schema_invalid"
    assert result["observation"]["final_answer_prefix"] == '{"claims":42}'


async def test_http_failure_body_not_persisted(tmp_path):
    result = await observe_once(
        load_saved_request(REFERENCE_REQUEST),
        tmp_path / "http",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(500, json=envelope('{"claims":["PRIVATE_ERROR"]}'))
        ),
    )
    assert result["error"] == "provider_http_500"
    assert "PRIVATE_ERROR" not in json.dumps(result)


async def test_cancellation_persisted_and_propagated(tmp_path):
    def handler(_):
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await observe_once(
            load_saved_request(REFERENCE_REQUEST),
            tmp_path / "cancelled",
            transport=httpx.MockTransport(handler),
        )
    saved = json.loads((tmp_path / "cancelled/result.json").read_text())
    assert saved["error"] == "cancelled"
    assert saved["observation"] is None


async def test_no_real_transport_or_historical_destination(tmp_path):
    request = load_saved_request(REFERENCE_REQUEST)
    with pytest.raises(ValueError, match="fake HTTP"):
        await observe_once(request, tmp_path / "real", transport=None)
    assert not (tmp_path / "real").exists()
    for name in ("runs", "freezes", "benchmarks", "diagnostics"):
        with pytest.raises(ValueError, match="protected"):
            await observe_once(
                request,
                ROOT / name / "must-not-exist",
                transport=httpx.MockTransport(lambda _: httpx.Response(200)),
            )


def test_workload_audit_exposes_structural_gap_without_inventing_causality():
    report = audit()
    assert report["generation_calls"] == 0
    assert report["readiness"] == "not_demonstrated"
    assert report["failed_workload"]["inference_rules"] == 4
    assert report["failed_workload"]["decision_rules"] == 2
    assert report["failed_workload"]["premise_occurrences"] == 14
    assert all(
        "inference_rules" in fixture["below_failed_workload"]
        for fixture in report["synthetic_fixtures"]
    )
    serialized = json.dumps(report)
    assert "gold" not in serialized
    assert "CANARY" not in serialized


def test_public_fixture_is_the_exact_saved_request_without_a_private_campaign_dependency():
    request = load_saved_request(REFERENCE_REQUEST)
    assert request_digest(request) == (
        "226720b117f7e0a18bc713cadd84adb392063dd97be5612a50592c6cd141c862"
    )
    if FAILED_JOURNAL.exists():
        assert request == load_saved_request(FAILED_JOURNAL)
    assert "response" not in json.loads(REFERENCE_REQUEST.read_text())


async def test_complete_json_with_length_is_still_failure(tmp_path):
    output = {
        "claims": [],
        "insights": [],
        "uncertainty": {"confidence": None, "assumptions": [], "evidence_ids": [], "unknowns": []},
    }
    for reason, expected in [("length", "failed"), ("stop", "schema_valid")]:
        result = await observe_once(
            load_saved_request(REFERENCE_REQUEST),
            tmp_path / reason,
            transport=httpx.MockTransport(
                lambda _, reason=reason: httpx.Response(
                    200, json=envelope(json.dumps(output), reason=reason)
                )
            ),
        )
        assert result["status"] == expected
        assert result["observation"]["answer_capture"] == "complete_json_candidate"
