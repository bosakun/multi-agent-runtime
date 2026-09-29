"""Exactly the 132 missing cells, with a separate non-resumable 456-call ledger."""

import json
import os
import random
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any

import httpx
from bounded_pilot.contract import BoundedAuditedProvider, BoundedProvider
from epistemic.conditions import configurations
from epistemic.paths import ROOT, digest
from epistemic.runner import timestamp
from external_benchmarks import runner as pilot
from external_benchmarks.conditions import build
from external_benchmarks.dataset import SEED, load_public, supporting_pairs
from external_benchmarks.models import FinalAnswer, PrivateGold
from external_benchmarks.provenance import file_sha256, verify_bundle
from external_benchmarks.scoring import score
from native_pilot.pilot26 import EXPECTED_DIGEST, host_probe
from operational_diagnostics.budget_experiment import checkpoint, exclusive
from operational_recovery.pilot24 import read_signed, reserve_mock, signed
from prospective_pilot.budget import ClosedCallBudget

from app.agents.executor import AgentExecutor
from app.llm.mock_provider import MockProvider
from app.llm.provider import ModelProvider
from app.orchestration.orchestrator import Orchestrator
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository
from app.tools.gateway import ToolRegistry
from hotpot_main.data import BUNDLE as BUNDLE
from hotpot_main.data import sources as sources

CAMPAIGN = ROOT / "runs/hotpotqa-protocol31-qwen3-14b-windows"
FREEZE = ROOT / "freezes/hotpotqa-dev-distractor-protocol-3.1.json"
MOCK = ROOT.parents[1] / "reports/hotpotqa-main-mock"


def controls() -> dict[str, Any]:
    return {
        **pilot.controls(),
        "protocol_version": "hotpotqa-3.1",
        "phase": "additional",
        "task_count": 30,
        "conditions": ["C0", "C1", "C2", "C3", "C4"],
        "planned_runs": 132,
        "planned_calls": 456,
        "hard_call_limit": 456,
        "cumulative_runs": 150,
        "cumulative_calls": 510,
        "primary_inference": "C3-C2 answer F1 on next24 non-Pilot questions",
        "secondary_inference": "P2-P5 answer F1 on next24, Holm family of four",
    }


def fingerprint(mock: bool) -> str:
    return digest(
        {"files": sources(), "controls": controls(), "provider": "mock" if mock else "real"}
    )


def ledger_used(path: Path) -> int:
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        return int(db.execute("SELECT used FROM budget WHERE id=1").fetchone()[0])


def base_gate(mock: bool) -> tuple[Path, dict[str, Any]]:
    if not mock:
        pilot.verify_binding()
    path = (pilot.MOCK if mock else pilot.CAMPAIGN / "pilot") / "results.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    budget = pilot.MOCK / "budget.sqlite" if mock else pilot.CAMPAIGN / "budget.sqlite"
    if (
        not pilot.integral(data)
        or not data["metadata"].get("finished_at")
        or not data["metadata"].get("operational_integrity")
        or data["metadata"]["provider"] != ("mock" if mock else "real")
        or data["metadata"]["fingerprint"] != pilot.fingerprint(mock)
        or ledger_used(budget) != 54
    ):
        raise ValueError("Require a finished integral same-source Pilot and its 54-call ledger")
    return path, data


def grid(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    previous = {(qid, c) for qid in manifest["pilot_task_ids"] for c in ["C0", "C2", "C3"]}
    full = {(qid, c) for qid in manifest["task_ids"] for c in controls()["conditions"]}
    return full - previous


def integral(data: dict[str, Any], manifest: dict[str, Any]) -> bool:
    meta, records = data["metadata"], data["records"]
    return (
        len(records) == meta["executed_runs"] == 132
        and meta["model_calls"] == 456
        and not meta["stopped_reason"]
        and {(r["question_id"], r["condition"]) for r in records} == grid(manifest)
        and all(
            r["status"] == "succeeded"
            and not r["errors"]
            and not any(r["audit"].values())
            and r["calls"] == (1 if r["condition"] == "C0" else 4)
            for r in records
        )
    )


def verify_data() -> dict[str, Any]:
    manifest = verify_bundle(BUNDLE)
    base = verify_bundle(vars(pilot)["BUNDLE"])
    if (
        len(manifest["task_ids"]) != 30
        or len(set(manifest["task_ids"])) != 30
        or manifest["task_ids"][:6] != manifest["pilot_task_ids"]
        or manifest["pilot_task_ids"] != base["task_ids"]
        or manifest["pilot_dataset_sha256"] != base["sha256"]
        or any(manifest["files"].get(k) != v for k, v in base["files"].items())
        or manifest["raw_sha256"] != base["raw_sha256"]
    ):
        raise ValueError("Thirty-question corpus/Pilot prefix drift")
    return manifest


async def bind() -> None:
    if CAMPAIGN.exists() or FREEZE.exists():
        raise ValueError("Require fresh additional campaign and freeze")
    manifest = verify_data()
    base_path, _ = base_gate(False)
    mock_path = MOCK / "results.json"
    mock = json.loads(mock_path.read_text(encoding="utf-8"))
    if (
        not integral(mock, manifest)
        or mock["metadata"]["provider"] != "mock"
        or mock["metadata"]["fingerprint"] != fingerprint(True)
        or mock["metadata"]["dataset_sha256"] != manifest["sha256"]
        or ledger_used(MOCK / "budget.sqlite") != 456
    ):
        raise ValueError("Current-source 132-case / 456-call Mock gate required")
    host = await host_probe()
    freeze = signed(
        {
            **controls(),
            "files": sources(),
            "dataset_sha256": manifest["sha256"],
            "task_ids": manifest["task_ids"],
            "pilot_result_sha256": file_sha256(base_path),
            "pilot_binding_sha256": file_sha256(pilot.CAMPAIGN / "binding.json"),
            "pilot_budget_calls": 54,
            "mock_sha256": file_sha256(mock_path),
            "authorization": "User selected 30 questions x five conditions, 510 total calls",
        }
    )
    exclusive(FREEZE, freeze)
    exclusive(
        CAMPAIGN / "binding.json",
        signed(
            {
                **controls(),
                "freeze_sha256": freeze["sha256"],
                "dataset_sha256": manifest["sha256"],
                "campaign": str(CAMPAIGN.resolve()),
                "backend_version": host["ollama"]["version"],
                "host": host,
            }
        ),
    )


def verify_binding() -> dict[str, Any]:
    manifest = verify_data()
    base_path, _ = base_gate(False)
    freeze, binding = read_signed(FREEZE), read_signed(CAMPAIGN / "binding.json")
    if (
        any(value.get(k) != v for value in (freeze, binding) for k, v in controls().items())
        or freeze["files"] != sources()
        or freeze["task_ids"] != manifest["task_ids"]
        or freeze["dataset_sha256"] != manifest["sha256"]
        or binding["dataset_sha256"] != manifest["sha256"]
        or binding["freeze_sha256"] != freeze["sha256"]
        or binding["campaign"] != str(CAMPAIGN.resolve())
        or freeze["pilot_result_sha256"] != file_sha256(base_path)
        or freeze["pilot_binding_sha256"] != file_sha256(pilot.CAMPAIGN / "binding.json")
        or freeze["mock_sha256"] != file_sha256(MOCK / "results.json")
    ):
        raise ValueError("Additional campaign source/data/binding drift")
    return binding


async def execute(*, mock: bool = False, transport: httpx.AsyncBaseTransport | None = None) -> Path:
    manifest = verify_data()
    base_path, base_data = base_gate(mock)
    binding = None if mock else verify_binding()
    if min(456, int(os.environ.get("MAX_MODEL_CALLS", "456"))) < 456:
        raise ValueError("The complete 456-call additional grid must fit budget")
    if mock:
        target = reserve_mock(MOCK)
        budget_path = target / "budget.sqlite"
    else:
        if sorted(p.name for p in CAMPAIGN.iterdir()) != ["binding.json"]:
            raise ValueError("Additional campaign consumed; no retry/resume/overwrite")
        host = await host_probe()
        assert binding is not None
        if (
            host["ollama"]["version"] != binding["backend_version"]
            or host["ollama"]["digest"] != EXPECTED_DIGEST
        ):
            raise ValueError("Backend/model drift")
        target = CAMPAIGN / "additional"
        target.mkdir(exist_ok=False)
        exclusive(target / "backend.json", host)
        budget_path = CAMPAIGN / "budget.sqlite"
    budget = ClosedCallBudget(budget_path, 456)
    if budget.used:
        raise ValueError("Fresh ledger must start at zero")
    meta: dict[str, Any] = {
        **controls(),
        "experiment_id": uuid.uuid4().hex,
        "started_at": timestamp(),
        "provider": "mock" if mock else "real",
        "fingerprint": fingerprint(mock),
        "dataset_sha256": manifest["sha256"],
        "task_ids": manifest["task_ids"],
        "pilot_task_ids": manifest["pilot_task_ids"],
        "pilot_result_sha256": file_sha256(base_path),
        "prior_calls": base_data["metadata"]["model_calls"],
        "model_binding": binding,
        "executed_runs": 0,
        "model_calls": 0,
        "stopped_reason": None,
        "interpretation": "MOCK VALIDATION, NOT MODEL PERFORMANCE"
        if mock
        else "REAL HOTPOTQA ADDITIONAL GRID",
    }
    records: list[dict[str, Any]] = []
    data = {"metadata": meta, "records": records}
    exclusive(target / "manifest.json", meta)
    checkpoint(target / "results.json", data)
    repository = SQLRepository(
        "sqlite+aiosqlite:///" + (target / "runtime.sqlite").resolve().as_posix()
    )
    try:
        await repository.initialize()
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:11434/",
            timeout=1200,
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        ) as client:
            for question in load_public(BUNDLE, manifest["task_ids"]):
                configs = [c for c in configurations() if (question.id, c.id) in grid(manifest)]
                random.Random(digest([SEED, question.id, "condition-order"])).shuffle(configs)
                for condition in configs:
                    workflow, agents, inputs, partitions = build(question, condition, mock=mock)
                    base: ModelProvider = (
                        MockProvider(
                            pilot.single_mock if condition.id == "C0" else pilot.mock_response
                        )
                        if mock
                        else BoundedProvider(client, target / "http-observations")
                    )
                    provider = BoundedAuditedProvider(
                        base,
                        budget,
                        target / "call-journal" / question.id / condition.id,
                        max_concurrency=1,
                    )
                    client.event_hooks["request"] = [] if mock else [provider.audit_http_request]
                    runtime = Orchestrator(
                        repository,
                        ContextBuilder(repository),
                        AgentExecutor({"mock" if mock else "real": provider}, pilot.schemas()),
                        ToolRegistry(),
                    )
                    print(
                        json.dumps(
                            {
                                "event": "CASE_STARTED",
                                "question": question.id,
                                "condition": condition.id,
                                "additional_calls": budget.used,
                                "total_calls": 54 + budget.used,
                            }
                        ),
                        flush=True,
                    )
                    run = await runtime.create(workflow, agents, inputs)
                    run = await runtime.execute(run.id)
                    audit = pilot.audit_projection(question, agents, provider)
                    final = next(
                        (a for a in run.state.artifacts if a.id in run.state.final_artifact_ids),
                        None,
                    )
                    answer = FinalAnswer.model_validate(final.payload) if final else None
                    predictions = {
                        "answer": {question.id: answer.answer if answer else ""},
                        "sp": {
                            question.id: supporting_pairs(question, answer.evidence_ids)
                            if answer
                            else []
                        },
                    }
                    # Load private gold only after inference; never add it to public context.
                    gold = PrivateGold.model_validate_json(
                        (BUNDLE / "gold" / f"{question.id}.json").read_text(encoding="utf-8")
                    )
                    errors = [
                        event.result.error.code
                        for event in run.state.agent_runs
                        if event.result is not None and event.result.error is not None
                    ]
                    record = {
                        "question_id": question.id,
                        "condition": condition.id,
                        "run_id": run.id,
                        "status": run.status.value,
                        "errors": errors,
                        "calls": len(provider.calls),
                        "audit": audit,
                        "predictions": predictions,
                        "metrics": score(predictions, [gold]),
                        "output": answer.model_dump(mode="json") if answer else None,
                        "partitions": partitions,
                        "usage": run.usage().model_dump(),
                    }
                    records.append(record)
                    exclusive(target / "records" / f"{question.id}_{condition.id}.json", record)
                    meta.update(executed_runs=len(records), model_calls=budget.used)
                    if record["status"] != "succeeded" or errors or any(audit.values()):
                        meta["stopped_reason"] = "runtime/schema/transport/access failure"
                    checkpoint(target / "results.json", data)
                    print(
                        json.dumps(
                            {
                                "event": "CASE_COMPLETED",
                                "question": question.id,
                                "condition": condition.id,
                                "status": record["status"],
                                "additional_calls": budget.used,
                                "total_calls": 54 + budget.used,
                            }
                        ),
                        flush=True,
                    )
                    if meta["stopped_reason"]:
                        break
                if meta["stopped_reason"]:
                    break
    except BaseException as exc:
        meta["stopped_reason"] = type(exc).__name__
        raise
    finally:
        await repository.close()
        meta.update(executed_runs=len(records), model_calls=budget.used, finished_at=timestamp())
        if meta["fingerprint"] != fingerprint(mock):
            meta["stopped_reason"] = "source drift during execution"
        meta["operational_integrity"] = integral(data, manifest)
        checkpoint(target / "results.json", data)
    return target / "results.json"
