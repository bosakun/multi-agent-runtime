"""Fresh published-benchmark cohorts; official scoring is separate from runtime integrity."""

import json
import os
import random
import uuid
from pathlib import Path
from typing import Any

import httpx
from bounded_pilot.contract import BoundedAuditedProvider, BoundedProvider
from epistemic.paths import ROOT, digest
from epistemic.runner import timestamp
from native_pilot.pilot26 import EXPECTED_DIGEST, host_probe
from operational_diagnostics.budget_experiment import checkpoint, exclusive
from operational_recovery.pilot24 import read_signed, reserve_mock, signed
from prospective_pilot.budget import ClosedCallBudget

from app.agents.executor import AgentExecutor
from app.core.models import AgentContext, AgentDefinition, Usage
from app.core.schemas import SchemaRegistry
from app.llm.mock_provider import MockProvider
from app.llm.provider import ModelProvider, ModelRequest, ModelResponse
from app.orchestration.orchestrator import Orchestrator
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository
from app.tools.gateway import ToolRegistry
from external_benchmarks.conditions import build, pilot_conditions
from external_benchmarks.dataset import SEED, load_public, supporting_pairs
from external_benchmarks.models import (
    EmptyInput,
    FinalAnswer,
    PrivateGold,
    PublicQuestion,
    WorkerAnswer,
)
from external_benchmarks.provenance import (
    BUNDLE,
    SCORER_COMMIT,
    SCORER_SHA256,
    file_sha256,
    sources,
    verify_bundle,
)
from external_benchmarks.scoring import score

CAMPAIGN = ROOT / "runs/hotpotqa-protocol30-qwen3-14b-windows"
FREEZE = ROOT / "freezes/hotpotqa-dev-distractor-protocol-3.0.json"
MOCK = ROOT.parents[1] / "reports/hotpotqa-mock"


def controls() -> dict[str, Any]:
    return {
        "protocol_version": "hotpotqa-3.0",
        "benchmark": "HotpotQA",
        "setting": "distractor",
        "split": "dev",
        "task_count": 6,
        "conditions": ["C0", "C2", "C3"],
        "repetitions": 1,
        "seed": SEED,
        "planned_runs": 18,
        "planned_calls": 54,
        "hard_call_limit": 60,
        "primary_endpoint": "official_answer_f1",
        "scorer_commit": SCORER_COMMIT,
        "scorer_sha256": SCORER_SHA256,
        "model": "qwen3:14b",
        "model_digest": EXPECTED_DIGEST,
        "temperature": 0,
        "api": "/api/chat",
        "think": False,
        "num_ctx": 8192,
        "num_predict": 4096,
        "timeout_seconds": 1200,
        "worker_concurrency": 1,
        "model_concurrency": 1,
        "partition": "gold_blind_document_greedy_public_text_length",
        "retry": False,
        "repair": False,
        "resume": False,
    }


def fingerprint(mock: bool) -> str:
    return digest(
        {"files": sources(), "controls": controls(), "provider": "mock" if mock else "real"}
    )


def integral(data: dict[str, Any]) -> bool:
    meta, records = data["metadata"], data["records"]
    return (
        len(records) == meta["executed_runs"] == 18
        and meta["model_calls"] == 54
        and not meta["stopped_reason"]
        and {(r["question_id"], r["condition"]) for r in records}
        == {(qid, condition) for qid in meta["task_ids"] for condition in controls()["conditions"]}
        and all(
            r["status"] == "succeeded"
            and not r["errors"]
            and r["calls"] == (1 if r["condition"] == "C0" else 4)
            and not any(r["audit"].values())
            for r in records
        )
    )


async def bind() -> None:
    if CAMPAIGN.exists() or FREEZE.exists():
        raise ValueError("Require fresh external-benchmark campaign/freeze")
    manifest = verify_bundle(BUNDLE)
    mock_path = MOCK / "results.json"
    mock = json.loads(mock_path.read_text(encoding="utf-8"))
    if (
        not integral(mock)
        or mock["metadata"]["provider"] != "mock"
        or mock["metadata"]["fingerprint"] != fingerprint(True)
        or mock["metadata"]["dataset_sha256"] != manifest["sha256"]
    ):
        raise ValueError("Current-source 54-call official-data Mock gate required")
    host = await host_probe()
    freeze = signed(
        {
            **controls(),
            "files": sources(),
            "dataset_sha256": manifest["sha256"],
            "task_ids": manifest["task_ids"],
            "mock_sha256": file_sha256(mock_path),
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
    manifest = verify_bundle(BUNDLE)
    freeze, binding = read_signed(FREEZE), read_signed(CAMPAIGN / "binding.json")
    if any(payload.get(k) != v for payload in (freeze, binding) for k, v in controls().items()):
        raise ValueError("Published-benchmark controls drift")
    if (
        freeze["files"] != sources()
        or freeze["dataset_sha256"] != manifest["sha256"]
        or freeze["task_ids"] != manifest["task_ids"]
        or binding["freeze_sha256"] != freeze["sha256"]
        or binding["dataset_sha256"] != manifest["sha256"]
        or binding["campaign"] != str(CAMPAIGN.resolve())
        or freeze["mock_sha256"] != file_sha256(MOCK / "results.json")
    ):
        raise ValueError("Published-benchmark source/data/binding mismatch")
    return binding


def schemas() -> SchemaRegistry:
    registry = SchemaRegistry()
    registry.register("hotpot.input.v1", EmptyInput)
    registry.register("hotpot.worker.v1", WorkerAnswer)
    registry.register("hotpot.final.v1", FinalAnswer)
    return registry


def mock_response(request: ModelRequest) -> ModelResponse:
    context = request.context
    allowed = sorted(context.evidence_scope())
    citations = allowed[:1]
    uncertainty: dict[str, Any] = {
        "confidence": None,
        "assumptions": [],
        "evidence_ids": [],
        "unknowns": [],
    }
    if context.agent_id == "synthesizer":
        output: dict[str, Any] = {
            "answer": "MOCK_NO_INFERENCE",
            "evidence_ids": citations,
            "uncertainty": uncertainty,
        }
    else:
        output = {
            "candidate_answer": "",
            "findings": [{"text": "Mock plumbing only", "evidence_ids": citations}],
            "uncertainty": uncertainty,
        }
    return ModelResponse(output=output, usage=Usage(model_calls=1))


def single_mock(request: ModelRequest) -> ModelResponse:
    output: dict[str, Any] = {
        "answer": "MOCK_NO_INFERENCE",
        "evidence_ids": sorted(request.context.evidence_scope())[:1],
        "uncertainty": {
            "confidence": None,
            "assumptions": [],
            "evidence_ids": [],
            "unknowns": [],
        },
    }
    return ModelResponse(output=output, usage=Usage(model_calls=1))


async def execute(
    *,
    mock: bool = False,
    output: Path | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> Path:
    manifest = verify_bundle(BUNDLE)
    binding = None if mock else verify_binding()
    limit = min(60, int(os.environ.get("MAX_MODEL_CALLS", "60")))
    if limit < 54:
        raise ValueError("Entire 54-call Hotpot Pilot must fit budget")
    if mock:
        target = reserve_mock(output or MOCK)
        budget_path = target / "budget.sqlite"
    else:
        if sorted(p.name for p in CAMPAIGN.iterdir()) != ["binding.json"]:
            raise ValueError("Campaign consumed; no retry/resume/overwrite")
        host = await host_probe()
        assert binding is not None
        if (
            host["ollama"]["version"] != binding["backend_version"]
            or host["ollama"]["digest"] != EXPECTED_DIGEST
        ):
            raise ValueError("Backend/model drift")
        target = CAMPAIGN / "pilot"
        target.mkdir(exist_ok=False)
        exclusive(target / "backend.json", host)
        budget_path = CAMPAIGN / "budget.sqlite"
    budget = ClosedCallBudget(budget_path, limit)
    if budget.used:
        raise ValueError("Fresh budget must start at zero")
    meta: dict[str, Any] = {
        **controls(),
        "experiment_id": uuid.uuid4().hex,
        "started_at": timestamp(),
        "provider": "mock" if mock else "real",
        "fingerprint": fingerprint(mock),
        "dataset_sha256": manifest["sha256"],
        "task_ids": manifest["task_ids"],
        "model_binding": binding,
        "executed_runs": 0,
        "model_calls": 0,
        "stopped_reason": None,
        "interpretation": "MOCK VALIDATION, NOT MODEL PERFORMANCE"
        if mock
        else "REAL HOTPOTQA DEV PILOT",
    }
    records: list[dict[str, Any]] = []
    data = {"metadata": meta, "records": records}
    exclusive(target / "manifest.json", meta)
    checkpoint(target / "results.json", data)
    repository = SQLRepository(
        "sqlite+aiosqlite:///" + (target / "runtime.sqlite").resolve().as_posix()
    )
    await repository.initialize()
    try:
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:11434/",
            timeout=1200,
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        ) as client:
            for question in load_public(BUNDLE, manifest["task_ids"]):
                configs = pilot_conditions()
                random.Random(digest([SEED, question.id, "condition-order"])).shuffle(configs)
                for condition in configs:
                    workflow, agents, inputs, partitions = build(question, condition, mock=mock)
                    base: ModelProvider = (
                        MockProvider(single_mock if condition.id == "C0" else mock_response)
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
                        AgentExecutor({"mock" if mock else "real": provider}, schemas()),
                        ToolRegistry(),
                    )
                    print(
                        json.dumps(
                            {
                                "event": "CASE_STARTED",
                                "question": question.id,
                                "condition": condition.id,
                                "calls_used": budget.used,
                            }
                        ),
                        flush=True,
                    )
                    run = await runtime.create(workflow, agents, inputs)
                    run = await runtime.execute(run.id)
                    audit = audit_projection(question, agents, provider)
                    final = next(
                        (
                            artifact
                            for artifact in run.state.artifacts
                            if artifact.id in run.state.final_artifact_ids
                        ),
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
                    # Private labels are opened only after the model has finished this case.
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
                                "calls_used": budget.used,
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
        meta["operational_integrity"] = integral(data)
        checkpoint(target / "results.json", data)
    return target / "results.json"


def audit_projection(
    question: PublicQuestion, agents: dict[str, AgentDefinition], provider: BoundedAuditedProvider
) -> dict[str, int]:
    violations = {"raw_projection": 0, "private_inputs": 0, "out_of_scope_ids": 0}
    all_ids = {s.id for s in question.sentences}
    expected = {s.id: s for s in question.sentences}
    for call in provider.calls:
        context = AgentContext.model_validate(call.request["context"])
        agent = agents[call.agent_id]
        raw_ids = {item.id for item in context.knowledge}
        violations["raw_projection"] += int(raw_ids != set(agent.context.knowledge_ids))
        violations["private_inputs"] += int(
            bool(context.inputs) or context.task != question.question
        )
        for item in context.knowledge:
            if item.id not in expected:
                violations["raw_projection"] += 1
                continue
            sentence = expected[item.id]
            content = json.loads(item.content)
            violations["raw_projection"] += int(
                content
                != {
                    "title": sentence.title,
                    "sentence_index": sentence.sentence_index,
                    "text": sentence.text,
                }
            )
        for value in (call.request, call.response):
            serialized = json.dumps(value)
            violations["out_of_scope_ids"] += sum(
                eid in serialized for eid in all_ids - context.evidence_scope()
            )
    return violations


def analyze(input_path: Path, output: Path) -> Path:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if not integral(data) or not data["metadata"]["operational_integrity"]:
        raise ValueError("Only complete 18-run/54-call cohorts may be analyzed")
    manifest = verify_bundle(BUNDLE)
    if data["metadata"]["dataset_sha256"] != manifest["sha256"]:
        raise ValueError("Analysis dataset differs from executed cohort")
    if output.exists():
        raise ValueError("Analysis destination exists; no overwrite")
    gold = [
        PrivateGold.model_validate_json(
            (BUNDLE / "gold" / f"{qid}.json").read_text(encoding="utf-8")
        )
        for qid in data["metadata"]["task_ids"]
    ]
    summaries = {}
    for condition in controls()["conditions"]:
        predictions: dict[str, Any] = {"answer": {}, "sp": {}}
        for record in data["records"]:
            if record["condition"] == condition:
                for key in predictions:
                    predictions[key].update(record["predictions"][key])
        summaries[condition] = score(predictions, gold)
        exclusive(output / f"predictions-{condition}.json", predictions)
    from epistemic.analysis import paired_inference

    indexed = {(r["question_id"], r["condition"]): r for r in data["records"]}
    paired = paired_inference(
        [
            indexed[qid, "C3"]["metrics"]["f1"] - indexed[qid, "C2"]["metrics"]["f1"]
            for qid in data["metadata"]["task_ids"]
        ]
    )
    report = {
        "metadata": data["metadata"],
        "input_sha256": file_sha256(input_path),
        "summaries": summaries,
        "primary_C3_minus_C2_answer_f1": paired,
        "caveat": (
            "Six publicly length-limited dev questions, not full official benchmark or leaderboard"
        ),
    }
    exclusive(output / "analysis.json", report)
    lines = [
        "# " + data["metadata"]["interpretation"],
        "",
        "Official HotpotQA metrics (0–1), six dev questions per condition.",
        "",
        "| Condition | Answer EM | Answer F1 | Support F1 | Joint F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for condition, values in summaries.items():
        lines.append(
            f"| {condition} | {values['em']:.3f} | {values['f1']:.3f} "
            f"| {values['sp_f1']:.3f} | {values['joint_f1']:.3f} |"
        )
    lines.extend(["", report["caveat"], "", "Mock scores are not model capability measurements."])
    output.joinpath("summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output / "analysis.json"
