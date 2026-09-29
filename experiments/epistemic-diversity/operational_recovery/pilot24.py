"""A separately sealed pilot amendment composing, not modifying, the frozen runtime."""

import hashlib
import json
import os
import random
import uuid
from pathlib import Path
from typing import Any, Literal

import httpx
from epistemic.benchmark_v2 import PILOT_IDS, SEED
from epistemic.conditions import configurations
from epistemic.freeze import verify
from epistemic.mock import respond
from epistemic.models import ModelSettings
from epistemic.paths import digest
from epistemic.provider import AuditedProvider, CallBudget
from epistemic.review import human_review
from epistemic.runner import make_plan, run_case, source_info, timestamp
from operational_diagnostics.budget_experiment import checkpoint, exclusive, preflight
from pydantic import model_validator

from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelProvider
from app.repositories.sql import SQLRepository
from operational_recovery import live_diagnostic as diagnostic
from operational_recovery.observer import AnswerRecorder
from operational_recovery.workload import ROOT

PROTOCOL = "pilot-2.4"
CAMPAIGN = ROOT / "runs/qwen3-14b-protocol24"
FREEZE = ROOT / "freezes/benchmark-2.0.0-protocol-2.4.json"


class Settings(ModelSettings):
    """Only the new cohort accepts the increased common generation/deadline budget."""

    max_output_tokens: int = 4096
    timeout_seconds: float = 1200
    execution_profile: Literal["standard", "local_ollama"] = "local_ollama"
    model: str = "qwen3:14b"

    @model_validator(mode="after")
    def local_execution_invariants(self) -> "Settings":
        if (
            self.execution_profile != "local_ollama"
            or self.max_output_tokens != 4096
            or self.timeout_seconds != 1200
            or self.temperature != 0
            or self.model != "qwen3:14b"
        ):
            raise ValueError("Protocol 2.4 requires local qwen3:14b, 4096/1200/temperature 0")
        return self


def sources() -> dict[str, str]:
    verify()
    paths = [ROOT.parents[1] / name for name in diagnostic.files()]
    paths += [Path(__file__), ROOT / "pilot24.py", ROOT / "docs/protocol-2.4-amendment.md"]
    return {
        str(p.relative_to(ROOT.parents[1])): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(set(paths))
    }


def signed(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, "sha256": digest(payload)}


def read_signed(path: Path) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(path.read_text())
    if digest({k: v for k, v in value.items() if k != "sha256"}) != value["sha256"]:
        raise ValueError("Seal/binding signature mismatch")
    return value


def gate() -> dict[str, Any]:
    diagnostic.verify_binding()
    path = diagnostic.CAMPAIGN / "diagnostic/results.json"
    result: dict[str, Any] = json.loads(path.read_text())
    if (
        not result["pilot_gate"]
        or result["budget_used_after"] != 3
        or result["stopped_reason"]
        or len(result["records"]) != 3
        or any(r["status"] != "schema_valid" for r in result["records"][1:])
    ):
        raise ValueError("Representative diagnostic gate has not passed")
    return {
        "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "backend_sha256": hashlib.sha256(
            (diagnostic.CAMPAIGN / "diagnostic/backend.json").read_bytes()
        ).hexdigest(),
        "binding_sha256": diagnostic.verify_binding()["sha256"],
    }


def prepare() -> None:
    evidence = gate()
    if CAMPAIGN.exists() or FREEZE.exists():
        raise ValueError("New Pilot requires fresh freeze and campaign; never overwrite")
    freeze = signed(
        {
            "protocol_version": PROTOCOL,
            "benchmark_version": "2.0.0",
            "metrics_version": "2.0.0",
            "base_freeze_sha256": verify()["freeze_sha256"],
            "files": sources(),
            "settings": Settings(provider="real").model_dump(),
            "seed": SEED,
            "task_ids": PILOT_IDS,
            "conditions": ["C2", "C3"],
            "repetitions": 1,
            "planned_calls": 48,
            "worker_concurrency": 1,
            "model_concurrency": 1,
            "thinking": "model_default",
            "backend_token_limit_parameter": "max_tokens",
            "diagnostic_gate": evidence,
        }
    )
    exclusive(FREEZE, freeze)
    exclusive(
        CAMPAIGN / "binding.json",
        signed(
            {
                "protocol_version": PROTOCOL,
                "freeze_sha256": freeze["sha256"],
                "campaign_path": str(CAMPAIGN.resolve()),
                "endpoint": diagnostic.ENDPOINT,
                "settings": freeze["settings"],
                "task_ids": PILOT_IDS,
                "conditions": ["C2", "C3"],
                "seed": SEED,
                "planned_calls": 48,
                "backend_token_limit_parameter": "max_tokens",
                "shared_budget_path": str((diagnostic.CAMPAIGN / "budget.sqlite").resolve()),
                "hard_call_limit": 60,
            }
        ),
    )


def verify_binding() -> dict[str, Any]:
    freeze, binding = read_signed(FREEZE), read_signed(CAMPAIGN / "binding.json")
    for payload in (freeze, binding):
        if any(
            payload[key] != expected
            for key, expected in {
                "seed": SEED,
                "task_ids": PILOT_IDS,
                "conditions": ["C2", "C3"],
                "planned_calls": 48,
                "backend_token_limit_parameter": "max_tokens",
            }.items()
        ):
            raise ValueError("Fixed Pilot controls mismatch")
    if (
        freeze["files"] != sources()
        or freeze["diagnostic_gate"] != gate()
        or freeze["protocol_version"] != PROTOCOL
        or binding["protocol_version"] != PROTOCOL
        or binding["freeze_sha256"] != freeze["sha256"]
        or binding["campaign_path"] != str(CAMPAIGN.resolve())
        or binding["endpoint"] != diagnostic.ENDPOINT
        or binding["settings"] != Settings(provider="real").model_dump()
        or freeze["settings"] != binding["settings"]
        or binding["seed"] != SEED
        or binding["task_ids"] != PILOT_IDS
        or binding["conditions"] != ["C2", "C3"]
        or binding["planned_calls"] != 48
        or binding["shared_budget_path"] != str((diagnostic.CAMPAIGN / "budget.sqlite").resolve())
    ):
        raise ValueError("Protocol/source/binding mismatch")
    return binding


def reserve_mock(output: Path | None) -> Path:
    if output is None or output.exists():
        raise ValueError("Mock output must be a fresh separate directory")
    if output.resolve().is_relative_to((ROOT / "runs").resolve()):
        raise ValueError("Mock validation must not write real campaign paths")
    output.mkdir(parents=True, exist_ok=False)
    return output


def create_observations(output: Path) -> Path:
    path = output / "http-observations"
    path.mkdir()
    return path


def reserve_phase(campaign: Path) -> Path:
    if campaign.resolve() != CAMPAIGN.resolve():
        raise ValueError("Only the newly bound campaign is permitted")
    if sorted(p.name for p in campaign.iterdir()) != ["binding.json"]:
        raise ValueError("Campaign already consumed; no retry, resume or overwrite")
    output = campaign / "pilot"
    output.mkdir(exist_ok=False)
    return output


def integral(data: dict[str, Any]) -> bool:
    records, meta = data["records"], data["metadata"]
    return (
        len(records) == meta["executed_runs"] == 12
        and meta["pilot_model_calls"] == 48
        and not meta["stopped_reason"]
        and {(r["task_id"], r["condition"]) for r in records}
        == {(task, condition) for task in PILOT_IDS for condition in ("C2", "C3")}
        and all(
            r["status"] == "succeeded"
            and not r["errors"]
            and all(r["metrics"][k] == 0 for k in ("context_leaks", "result_leaks", "gold_leaks"))
            and r["metrics"]["model_calls"] == 4
            for r in records
        )
    )


async def execute(
    *,
    mock: bool = False,
    mock_output: Path | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> Path:
    binding = None if mock else verify_binding()
    settings = Settings(provider="mock" if mock else "real")
    budget_path = (
        mock_output / "budget.sqlite"
        if mock and mock_output
        else diagnostic.CAMPAIGN / "budget.sqlite"
    )
    limit = min(60, int(os.environ.get("MAX_MODEL_CALLS", "60")))
    if mock:
        output = reserve_mock(mock_output)
    else:
        existing = CallBudget(budget_path, limit)
        if existing.used != 3 or limit - existing.used < 48:
            raise ValueError("Exactly diagnostic 3 + fresh Pilot 48 calls must fit budget")
        backend = await preflight(
            {"endpoint": diagnostic.ENDPOINT, "model": settings.model}, transport
        )
        reference = json.loads((diagnostic.CAMPAIGN / "diagnostic/backend.json").read_text())
        if any(backend[k] != reference[k] for k in ("backend_version", "model_digest")):
            raise ValueError("Backend/model changed after representative diagnostic")
        output = reserve_phase(CAMPAIGN)
        exclusive(output / "backend.json", backend)
    budget = CallBudget(budget_path, limit)
    before = budget.used
    plan = make_plan("pilot", 1, limit - before, "2.0.0")
    metadata: dict[str, Any] = {
        "experiment_id": uuid.uuid4().hex,
        "timestamp": timestamp(),
        "phase": "pilot",
        "provider": settings.provider,
        "settings": settings.model_dump(),
        "seed": SEED,
        "benchmark_version": "2.0.0",
        "metrics_version": "2.0.0",
        "protocol_version": PROTOCOL,
        "execution_profile": "local_ollama",
        "worker_concurrency": 1,
        "model_concurrency": 1,
        "backend_token_limit_parameter": "max_tokens",
        "thinking_configuration": "model_default",
        "freeze_sha256": binding["freeze_sha256"] if binding else None,
        "model_binding": binding,
        "source": source_info(),
        "protocol_fingerprint": digest({"files": sources(), "settings": settings.model_dump()}),
        "plan": plan,
        "budget_used_before": before,
        "budget_limit": limit,
        "budget_used_after": before,
        "pilot_model_calls": 0,
        "executed_runs": 0,
        "stopped_reason": None,
        "interpretation": "MOCK VALIDATION — NOT LLM RESULTS" if mock else "REAL MODEL PILOT",
    }
    records: list[dict[str, Any]] = []
    data = {"metadata": metadata, "records": records}
    exclusive(output / "manifest.json", metadata)
    checkpoint(output / "results.json", data)
    repository = SQLRepository(f"sqlite+aiosqlite:///{(output / 'runtime.sqlite').resolve()}")
    await repository.initialize()
    observations = create_observations(output)

    async def response_hook(response: httpx.Response) -> None:
        body = json.loads(response.request.content)
        context = json.loads(body["messages"][1]["content"])
        destination = observations / f"{context['run_id']}_{context['agent_id']}.json"
        recorder = AnswerRecorder(destination)
        await recorder(response)
        observation = recorder.observation
        if response.is_success and (
            not observation
            or observation["input_tokens"] is None
            or observation["generated_tokens"] is None
            or observation["generated_tokens"] > 4096
            or observation["finish_reason"] not in {"stop", "length"}
        ):
            raise ValueError("Backend usage/finish reason violated operational controls")

    try:
        async with httpx.AsyncClient(
            base_url=diagnostic.ENDPOINT,
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
            provider = AuditedProvider(
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
                configs = [c for c in configurations() if c.id in ["C2", "C3"]]
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
                        pilot_model_calls=budget.used - before,
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
            pilot_model_calls=budget.used - before,
            finished_at=timestamp(),
        )
        metadata["operational_integrity"] = integral(data)
        checkpoint(output / "results.json", data)
        human_review(data, output / "pilot-human-review.md")
    return output / "results.json"
