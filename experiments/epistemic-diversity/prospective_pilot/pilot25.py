"""New Windows C2/C3 pilot with context-scoped citation constraints and no retries."""

import hashlib
import json
import os
import random
import uuid
from pathlib import Path
from typing import Any

import httpx
from epistemic.benchmark_v2 import PILOT_IDS, SEED
from epistemic.conditions import configurations
from epistemic.mock import respond
from epistemic.paths import ROOT, digest
from epistemic.review import human_review
from epistemic.runner import make_plan, run_case, source_info, timestamp
from host_support.commands import NativeCommands
from host_support.preflight import capture
from operational_diagnostics.budget_experiment import checkpoint, exclusive
from operational_recovery.observer import AnswerRecorder
from operational_recovery.pilot24 import Settings, integral, read_signed, reserve_mock, signed

from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelProvider
from app.repositories.sql import SQLRepository
from prospective_pilot.budget import ClosedCallBudget
from prospective_pilot.contract import ScopedAuditedProvider
from prospective_pilot.seals import sources, verify_historical

PROTOCOL = "pilot-2.5"
CAMPAIGN = ROOT / "runs/qwen3-14b-protocol25-windows"
FREEZE = ROOT / "freezes/benchmark-2.0.0-protocol-2.5.json"
MOCK = ROOT / "results/protocol25-windows-mock"
ENDPOINT = "http://127.0.0.1:11434/v1/"
EXPECTED_DIGEST = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"


def controls() -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL,
        "benchmark_version": "2.0.0",
        "metrics_version": "2.0.0",
        "settings": Settings(provider="real").model_dump(),
        "endpoint": ENDPOINT,
        "expected_model_digest": EXPECTED_DIGEST,
        "task_ids": PILOT_IDS,
        "conditions": ["C2", "C3"],
        "seed": SEED,
        "repetitions": 1,
        "planned_calls": 48,
        "hard_call_limit": 60,
        "worker_concurrency": 1,
        "model_concurrency": 1,
        "thinking": "model_default",
        "backend_token_limit_parameter": "max_tokens",
        "citation_contract": "agent_context_enum_v1",
        "retry": False,
        "resume": False,
    }


async def host_probe(transport: httpx.AsyncBaseTransport | None = None) -> dict[str, Any]:
    observed = await capture(
        NativeCommands(ROOT.parents[1]),
        ENDPOINT,
        "qwen3:14b",
        EXPECTED_DIGEST,
        transport=transport,
    )
    if not observed.passed or not observed.runtime.python_utf8_mode:
        raise ValueError("Windows host preflight failed; no model generation permitted")
    return observed.model_dump(mode="json")


async def prepare() -> None:
    if CAMPAIGN.exists() or FREEZE.exists():
        raise ValueError("Require a fresh Protocol 2.5 campaign and freeze; no overwrite")
    base = verify_historical()
    mock_result = MOCK / "results.json"
    mock = json.loads(mock_result.read_text(encoding="utf-8"))
    if (
        not integral(mock)
        or mock["metadata"]["provider"] != "mock"
        or mock["metadata"]["protocol_version"] != PROTOCOL
        or mock["metadata"]["protocol_fingerprint"]
        != digest({"files": sources(), "settings": Settings(provider="mock").model_dump()})
    ):
        raise ValueError("Current-source 48-call Mock gate has not passed")
    backend = await host_probe()
    freeze = signed(
        {
            **controls(),
            "base_freeze_sha256": base["freeze_sha256"],
            "files": sources(),
            "mock_gate_sha256": hashlib.sha256(mock_result.read_bytes()).hexdigest(),
            "authorization": (
                "User selected option 1: improve evidence-ID output constraints "
                "and run a fresh Pilot"
            ),
        }
    )
    exclusive(FREEZE, freeze)
    exclusive(
        CAMPAIGN / "binding.json",
        signed(
            {
                **controls(),
                "freeze_sha256": freeze["sha256"],
                "campaign_path": str(CAMPAIGN.resolve()),
                "budget_path": str((CAMPAIGN / "budget.sqlite").resolve()),
                "backend_version": backend["ollama"]["version"],
                "model_digest": backend["ollama"]["digest"],
                "host_at_binding": backend,
            }
        ),
    )


def verify_binding() -> dict[str, Any]:
    freeze = read_signed(FREEZE)
    binding = read_signed(CAMPAIGN / "binding.json")
    for payload in (freeze, binding):
        if any(payload.get(k) != v for k, v in controls().items()):
            raise ValueError("Protocol 2.5 fixed controls changed")
    if (
        freeze["files"] != sources()
        or freeze["base_freeze_sha256"] != verify_historical()["freeze_sha256"]
        or binding["freeze_sha256"] != freeze["sha256"]
        or binding["campaign_path"] != str(CAMPAIGN.resolve())
        or binding["budget_path"] != str((CAMPAIGN / "budget.sqlite").resolve())
        or binding["model_digest"] != EXPECTED_DIGEST
        or not binding["backend_version"]
        or freeze["mock_gate_sha256"]
        != hashlib.sha256((MOCK / "results.json").read_bytes()).hexdigest()
    ):
        raise ValueError("Protocol 2.5 source/freeze/binding/gate mismatch")
    return binding


async def execute(
    *,
    mock: bool = False,
    mock_output: Path | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> Path:
    binding = None if mock else verify_binding()
    settings = Settings(provider="mock" if mock else "real")
    limit = min(60, int(os.environ.get("MAX_MODEL_CALLS", "60")))
    if limit < 48:
        raise ValueError("The entire fixed 48-call Pilot must fit the budget")
    if mock:
        output = reserve_mock(mock_output)
        budget_path = output / "budget.sqlite"
        backend = None
    else:
        if sorted(p.name for p in CAMPAIGN.iterdir()) != ["binding.json"]:
            raise ValueError("Campaign consumed; no retry, resume or overwrite")
        backend = await host_probe(transport)
        assert binding is not None
        if any(
            backend["ollama"][key] != binding[bound]
            for key, bound in (("version", "backend_version"), ("digest", "model_digest"))
        ):
            raise ValueError("Backend/model changed after binding")
        output = CAMPAIGN / "pilot"
        output.mkdir(exist_ok=False)
        exclusive(output / "backend.json", backend)
        budget_path = CAMPAIGN / "budget.sqlite"
    budget = ClosedCallBudget(budget_path, limit)
    if budget.used:
        raise ValueError("Fresh Pilot budget must start at zero")
    plan = make_plan("pilot", 1, limit, "2.0.0")
    metadata: dict[str, Any] = {
        **controls(),
        "experiment_id": uuid.uuid4().hex,
        "timestamp": timestamp(),
        "phase": "pilot",
        "provider": settings.provider,
        "settings": settings.model_dump(),
        "execution_profile": "local_ollama",
        "thinking_configuration": "model_default",
        "freeze_sha256": binding["freeze_sha256"] if binding else None,
        "model_binding": binding,
        "source": source_info(),
        "protocol_fingerprint": digest({"files": sources(), "settings": settings.model_dump()}),
        "plan": plan,
        "budget_used_before": 0,
        "budget_limit": limit,
        "budget_used_after": 0,
        "pilot_model_calls": 0,
        "executed_runs": 0,
        "stopped_reason": None,
        "interpretation": "MOCK VALIDATION — NOT LLM RESULTS" if mock else "REAL MODEL PILOT",
    }
    records: list[dict[str, Any]] = []
    data = {"metadata": metadata, "records": records}
    exclusive(output / "manifest.json", metadata)
    checkpoint(output / "results.json", data)
    database = (output / "runtime.sqlite").resolve().as_posix()
    repository = SQLRepository("sqlite+aiosqlite:///" + database)
    await repository.initialize()
    observations = output / "http-observations"
    observations.mkdir()

    async def response_hook(response: httpx.Response) -> None:
        body = json.loads(response.request.content)
        context = json.loads(body["messages"][1]["content"])
        recorder = AnswerRecorder(observations / f"{context['run_id']}_{context['agent_id']}.json")
        await recorder(response)
        observed = recorder.observation
        if response.is_success and (
            not observed
            or observed["input_tokens"] is None
            or observed["generated_tokens"] is None
            or observed["generated_tokens"] > 4096
            or observed["finish_reason"] not in {"stop", "length"}
        ):
            raise ValueError("Backend usage/finish reason violates operational controls")

    try:
        async with httpx.AsyncClient(
            base_url=ENDPOINT,
            timeout=1200,
            transport=transport,
            trust_env=False,
            follow_redirects=False,
        ) as client:
            base: ModelProvider = (
                MockProvider(respond)
                if mock
                else OpenAICompatibleProvider(client, "ollama", token_limit_parameter="max_tokens")
            )
            provider = ScopedAuditedProvider(
                base,
                budget,
                output / "call-journal",
                max_concurrency=1,
                token_limit_parameter="max_tokens",
            )
            if not mock:
                client.event_hooks["request"].append(provider.audit_http_request)
                client.event_hooks["response"].append(response_hook)
            for task, repetition in plan["blocks"]:
                configs = [c for c in configurations() if c.id in ("C2", "C3")]
                random.Random(digest([task, SEED, "condition-order"])).shuffle(configs)
                for config in configs:
                    print(
                        json.dumps(
                            {
                                "event": "CASE_STARTED",
                                "task": task,
                                "condition": config.id,
                                "calls_used": budget.used,
                            }
                        ),
                        flush=True,
                    )
                    record = await run_case(
                        repository,
                        provider,
                        settings,
                        task,
                        config,
                        SEED,
                        repetition,
                        metadata["experiment_id"],
                        metadata,
                        output,
                    )
                    records.append(record)
                    metadata.update(
                        executed_runs=len(records),
                        budget_used_after=budget.used,
                        pilot_model_calls=budget.used,
                    )
                    if (
                        record["status"] != "succeeded"
                        or record["errors"]
                        or any(
                            record["metrics"][k]
                            for k in ("context_leaks", "result_leaks", "gold_leaks")
                        )
                    ):
                        metadata["stopped_reason"] = "runtime/schema/transport/boundary failure"
                    checkpoint(output / "results.json", data)
                    print(
                        json.dumps(
                            {
                                "event": "CASE_COMPLETED",
                                "task": task,
                                "condition": config.id,
                                "status": record["status"],
                                "calls_used": budget.used,
                                "errors": record["errors"],
                            }
                        ),
                        flush=True,
                    )
                    if metadata["stopped_reason"]:
                        break
                if metadata["stopped_reason"]:
                    break
    except BaseException as exc:
        metadata["stopped_reason"] = type(exc).__name__
        raise
    finally:
        await repository.close()
        metadata.update(
            executed_runs=len(records),
            budget_used_after=budget.used,
            pilot_model_calls=budget.used,
            finished_at=timestamp(),
        )
        metadata["operational_integrity"] = integral(data)
        checkpoint(output / "results.json", data)
        human_review(data, output / "pilot-human-review.md")
    return output / "results.json"
