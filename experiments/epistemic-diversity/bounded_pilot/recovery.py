"""Exactly one prospectively bound engineering call; no research-result pooling."""

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx
from epistemic.models import WorkerOutput
from epistemic.paths import ROOT, digest
from epistemic.runner import timestamp
from native_pilot.pilot26 import host_probe
from native_pilot.pilot26 import verify_binding as verify_previous
from operational_diagnostics.budget_experiment import exclusive
from operational_recovery.pilot24 import Settings, integral, read_signed, signed
from prospective_pilot.budget import ClosedCallBudget

from app.agents.executor import evidence_ids
from app.llm.provider import ModelRequest
from bounded_pilot.contract import BoundedAuditedProvider, BoundedProvider
from bounded_pilot.seals import sources

DIAGNOSTIC = ROOT / "runs/qwen3-14b-protocol27-diagnostic"
FAILED = ROOT / (
    "runs/qwen3-14b-protocol26-windows/pilot/call-journal/"
    "0011_54ccbae7d1e54dd88ec643dab90909b7_worker_2.json"
)
MOCK = ROOT / "results/protocol27-windows-mock/results.json"


def failed_request() -> ModelRequest:
    data = json.loads(FAILED.read_text(encoding="utf-8"))
    if data["response"] is not None or data["agent_id"] != "worker_2":
        raise ValueError("Diagnostic input is not the sealed failed worker")
    return ModelRequest.model_validate(data["request"])


def verify_mock() -> None:
    mock = json.loads(MOCK.read_text(encoding="utf-8"))
    if (
        not integral(mock)
        or mock["metadata"]["provider"] != "mock"
        or mock["metadata"]["protocol_version"] != "pilot-2.7"
        or mock["metadata"]["protocol_fingerprint"]
        != digest({"files": sources(), "settings": Settings(provider="mock").model_dump()})
    ):
        raise ValueError("Current-source 48-call Mock gate required")


async def prepare_diagnostic() -> None:
    if DIAGNOSTIC.exists():
        raise ValueError("Diagnostic directory consumed; no overwrite")
    previous = verify_previous()
    verify_mock()
    request = failed_request()
    host = await host_probe()
    exclusive(
        DIAGNOSTIC / "binding.json",
        signed(
            {
                "protocol_version": "pilot-2.7",
                "role": "selected-failure engineering diagnostic, not research result",
                "hard_call_limit": 1,
                "files": sources(),
                "previous_binding_sha256": previous["sha256"],
                "failed_journal_sha256": hashlib.sha256(FAILED.read_bytes()).hexdigest(),
                "request_sha256": digest(request.model_dump(mode="json")),
                "mock_gate_sha256": hashlib.sha256(MOCK.read_bytes()).hexdigest(),
                "api": "/api/chat",
                "think": False,
                "stream": False,
                "options": {"temperature": 0, "num_predict": 4096, "num_ctx": 8192},
                "backend_version": host["ollama"]["version"],
                "model_digest": host["ollama"]["digest"],
                "host_at_binding": host,
                "path": str(DIAGNOSTIC.resolve()),
            }
        ),
    )


def verify_diagnostic_binding() -> dict[str, Any]:
    binding = read_signed(DIAGNOSTIC / "binding.json")
    verify_mock()
    if (
        binding["files"] != sources()
        or binding["previous_binding_sha256"] != verify_previous()["sha256"]
        or binding["failed_journal_sha256"] != hashlib.sha256(FAILED.read_bytes()).hexdigest()
        or binding["request_sha256"] != digest(failed_request().model_dump(mode="json"))
        or binding["mock_gate_sha256"] != hashlib.sha256(MOCK.read_bytes()).hexdigest()
        or binding["path"] != str(DIAGNOSTIC.resolve())
        or binding["hard_call_limit"] != 1
        or binding["options"] != {"temperature": 0, "num_predict": 4096, "num_ctx": 8192}
        or binding["think"] is not False
    ):
        raise ValueError("Diagnostic source/request/controls drift")
    return binding


async def run_diagnostic(transport: httpx.AsyncBaseTransport | None = None) -> Path:
    binding = verify_diagnostic_binding()
    if sorted(p.name for p in DIAGNOSTIC.iterdir()) != ["binding.json"]:
        raise ValueError("Diagnostic consumed; no retry/resume")
    host = await host_probe()
    if any(
        host["ollama"][key] != binding[bound]
        for key, bound in (
            ("version", "backend_version"),
            ("digest", "model_digest"),
        )
    ):
        raise ValueError("Diagnostic backend drift")
    request = failed_request()
    budget = ClosedCallBudget(DIAGNOSTIC / "budget.sqlite", 1)
    result: dict[str, Any] = {
        "binding_sha256": binding["sha256"],
        "passed": False,
        "started_at": timestamp(),
        "calls_used": 0,
    }
    try:
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:11434/",
            timeout=1200,
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        ) as client:
            provider = BoundedAuditedProvider(
                BoundedProvider(client, DIAGNOSTIC / "observations"),
                budget,
                DIAGNOSTIC / "call-journal",
                max_concurrency=1,
            )
            client.event_hooks["request"].append(provider.audit_http_request)
            response = await provider.generate(request)
            parsed = WorkerOutput.model_validate(response.output)
            if not evidence_ids(parsed.model_dump()).issubset(request.context.evidence_scope()):
                raise ValueError("Diagnostic returned unauthorized citation")
            result.update(passed=True, usage=response.usage.model_dump())
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_code"] = getattr(exc, "code", None)
        raise
    finally:
        result.update(calls_used=budget.used, finished_at=timestamp())
        exclusive(DIAGNOSTIC / "result.json", signed(result))
    return DIAGNOSTIC / "result.json"


def diagnostic_gate() -> dict[str, Any]:
    binding = verify_diagnostic_binding()
    result = read_signed(DIAGNOSTIC / "result.json")
    if not result["passed"] or result["calls_used"] != 1:
        raise ValueError("The one-call native engineering diagnostic did not pass")
    if result["binding_sha256"] != binding["sha256"]:
        raise ValueError("Diagnostic gate binding mismatch")
    return result
