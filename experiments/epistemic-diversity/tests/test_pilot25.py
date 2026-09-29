"""Context projection, wire provenance, fail-stop, immutable gates and full Pilot grid."""

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from epistemic.models import FinalOutput, WorkerOutput
from epistemic.provider import BudgetExceeded
from prospective_pilot import pilot25 as pilot
from prospective_pilot.budget import ClosedCallBudget
from prospective_pilot.contract import scoped_schema
from prospective_pilot.seals import verify_historical

from app.core.models import AgentContext, Artifact, Knowledge


def citation_arrays(schema):
    found = []
    if isinstance(schema, dict):
        properties = schema.get("properties", {})
        if "evidence_ids" in properties:
            found.append(properties["evidence_ids"])
        for child in schema.values():
            found.extend(citation_arrays(child))
    elif isinstance(schema, list):
        for child in schema:
            found.extend(citation_arrays(child))
    return found


@pytest.mark.parametrize("model", [WorkerOutput, FinalOutput])
def test_all_nested_citations_use_only_authorized_context_without_mutation(model):
    context = AgentContext(
        agent_id="worker_1",
        run_id="example",
        knowledge=[
            Knowledge(id="allowed-b", content="public"),
            Knowledge(id="allowed-a", content="public"),
        ],
    )
    original = model.model_json_schema()
    before = json.dumps(original)
    result = scoped_schema(original, context)
    assert len(citation_arrays(result)) == 2  # shared Claim and Uncertainty definitions
    assert all(a["items"]["enum"] == ["allowed-a", "allowed-b"] for a in citation_arrays(result))
    assert "none" not in json.dumps(result)
    assert json.dumps(original) == before


def test_synthesizer_scope_comes_only_from_released_artifact_evidence():
    context = AgentContext(
        agent_id="synthesizer",
        run_id="example",
        artifacts=[
            Artifact(
                name="worker",
                version=1,
                producer="worker_0",
                node_id="workers",
                schema_id="worker",
                readers=["synthesizer"],
                evidence_ids=["released"],
                payload={"uncited_hidden_id": "not-released"},
            )
        ],
    )
    result = scoped_schema(FinalOutput.model_json_schema(), context)
    assert all(a["items"]["enum"] == ["released"] for a in citation_arrays(result))
    assert "not-released" not in json.dumps(result)


def test_empty_scope_allows_empty_arrays_not_placeholder_or_invalid_empty_enum():
    context = AgentContext(agent_id="synthesizer", run_id="example")
    result = scoped_schema(FinalOutput.model_json_schema(), context)
    assert all(a["maxItems"] == 0 and "enum" not in a["items"] for a in citation_arrays(result))
    with pytest.raises(ValueError):
        scoped_schema({"type": "object", "properties": {}}, context)


def test_windows_historical_path_normalization_does_not_weaken_content_validation():
    assert verify_historical()["protocol_version"] == "pilot-2.3"


def test_closed_budget_limit_and_windows_rename(tmp_path):
    path = tmp_path / "budget.sqlite"
    budget = ClosedCallBudget(path, 2)
    budget.reserve()
    budget.reserve()
    with pytest.raises(BudgetExceeded):
        budget.reserve()
    assert budget.used == 2
    renamed = tmp_path / "closed.sqlite"
    path.rename(renamed)
    assert renamed.exists()


@pytest.fixture
async def bound(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "CAMPAIGN", tmp_path / "campaign")
    monkeypatch.setattr(pilot, "FREEZE", tmp_path / "freeze.json")
    monkeypatch.setattr(pilot, "MOCK", tmp_path / "mock")
    monkeypatch.setattr(pilot, "sources", lambda: {"fixture": "sealed"})
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
        allowed = sorted(context.evidence_scope())
        arrays = citation_arrays(body["response_format"]["json_schema"]["schema"])
        assert len(arrays) == 2
        assert all(
            a["items"].get("enum") == allowed if allowed else a["maxItems"] == 0 for a in arrays
        )
        assert body["temperature"] == 0 and body["max_tokens"] == 4096
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
        if invalid_id and len(bodies) == 1:
            output["uncertainty"]["evidence_ids"] = ["none"]
        if context.agent_id == "synthesizer":
            output.update(conclusion="fake", decision_summary="fake")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "length" if truncate and len(bodies) == 1 else "stop",
                        "message": {"content": json.dumps(output), "reasoning": "PRIVATE"},
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 30, "total_tokens": 50},
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
