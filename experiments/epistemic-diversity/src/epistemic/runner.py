"""Compose the existing runtime; annotations stay on the evaluator side."""

import json
import os
import random
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.agents.executor import AgentExecutor
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelProvider
from app.orchestration.orchestrator import Orchestrator
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository
from app.tools.gateway import ToolRegistry
from epistemic.benchmark import load_task, partition, selected_tasks
from epistemic.benchmark_v2 import VERSION, partition_stats
from epistemic.conditions import build_condition, configurations, schemas
from epistemic.freeze import FREEZE_PATH, validate_binding, validate_endpoint, verify
from epistemic.metrics import audit, evaluate
from epistemic.mock import respond
from epistemic.models import ConditionConfig, ModelSettings
from epistemic.paths import REPO, ROOT, digest, write_json
from epistemic.provider import AuditedProvider, CallBudget
from epistemic.review import human_review


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def source_info() -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()

    paths = [
        p
        for folder in (
            ROOT / "src",
            ROOT / "prompts",
            ROOT / "configs",
            ROOT / "benchmarks",
            REPO / "app",
        )
        for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ]
    hashes = {str(p.relative_to(REPO)): digest(p.read_text()) for p in sorted(paths)}
    return {
        "git_commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "source_sha256": digest(hashes),
        "file_hashes": hashes,
    }


def protocol_fingerprint(settings: ModelSettings) -> str:
    return digest({"settings": settings.model_dump(), "source": source_info()["source_sha256"]})


def make_plan(
    phase: str, repetitions: int, remaining: int, version: str = "1.0.0"
) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("Repetitions must be positive")
    tasks = selected_tasks(phase, version)
    if phase == "pilot" and repetitions != 1:
        raise ValueError("Pilot is fixed at one repetition")
    # Repetition-major selection preserves a broad first pass before another repetition.
    requested = [(task, repetition) for repetition in range(repetitions) for task in tasks]
    conditions = (
        ["C2", "C3"]
        if version == VERSION and phase == "pilot"
        else [c.id for c in configurations()]
    )
    calls_per_block = sum(1 if condition == "C0" else 4 for condition in conditions)
    selected = requested[: max(0, remaining // calls_per_block)]
    return {
        "phase": phase,
        "conditions": conditions,
        "benchmark_version": version,
        "requested_tasks": tasks,
        "requested_repetitions": repetitions,
        "blocks": selected,
        "omitted_blocks": requested[len(selected) :],
        "runs": len(selected) * len(conditions),
        "approximate_model_calls": len(selected) * calls_per_block,
        "remaining_budget": remaining,
    }


def pilot_valid(records: list[dict[str, Any]], fingerprint: str) -> bool:
    required = {(task, c.id) for task in selected_tasks("pilot") for c in configurations()}
    found = {(r["task_id"], r["condition"]) for r in records}
    return (
        found == required
        and len(records) == len(required)
        and all(
            r["protocol_fingerprint"] == fingerprint
            and r["status"] == "succeeded"
            and not r["metrics"]["context_leaks"]
            and not r["metrics"]["result_leaks"]
            and not r["metrics"]["gold_leaks"]
            and not r["errors"]
            for r in records
        )
    )


async def run_case(
    repository: SQLRepository,
    provider: AuditedProvider,
    settings: ModelSettings,
    task_id: str,
    config: ConditionConfig,
    seed: int,
    repetition: int,
    experiment_id: str,
    metadata: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    task, gold = load_task(task_id)
    workflow, agents, inputs, assignment = build_condition(
        task,
        config,
        partition(task, gold, seed),
        seed,
        settings,
    )
    runtime = Orchestrator(
        repository,
        ContextBuilder(repository),
        AgentExecutor({settings.provider: provider}, schemas()),
        ToolRegistry(),
    )
    started_at = timestamp()
    started = time.perf_counter()
    call_offset = len(provider.calls)
    run = await runtime.create(workflow, agents, inputs)
    run = await runtime.execute(run.id)
    latency = (time.perf_counter() - started) * 1000
    calls = provider.calls[call_offset:]
    metrics, diagnostics = evaluate(run, gold)
    metrics.update(audit(task, gold, calls, run))
    metrics["raw_exposure_outside_partition"] = (
        None
        if config.id == "C0"
        else sum(
            len(set(agent.context.knowledge_ids) - set(assignment.partitions[key]))
            for key, agent in agents.items()
            if key.startswith("worker_")
        )
    )
    usage = run.usage()
    metrics.update(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.input_tokens + usage.output_tokens,
        model_calls=len(calls),
        latency_ms=latency,
        cost_usd=None,
    )
    errors = [a.result.error.code for a in run.state.agent_runs if a.result and a.result.error]
    errors.extend(call.error for call in calls if call.error)
    final = [a.payload for a in run.state.artifacts if a.id in run.state.final_artifact_ids]
    record = {
        "experiment_id": experiment_id,
        "run_id": run.id,
        "timestamp": started_at,
        "condition": config.id,
        "task_id": task.id,
        "family": task.family,
        "template": task.template,
        "seed": seed,
        "repetition": repetition,
        "model_settings": settings.model_dump(),
        "assignment": assignment.model_dump(),
        "protocol_fingerprint": metadata["protocol_fingerprint"],
        "git_commit": metadata["source"]["git_commit"],
        "source_sha256": metadata["source"]["source_sha256"],
        "source_dirty": metadata["source"]["dirty"],
        "prompt_version": "v1",
        "benchmark_version": task.benchmark_version,
        "metrics_version": "2.0.0",
        "difficulty": task.difficulty,
        "dependency_depth": task.dependency_depth,
        "benchmark_sha256": digest([task.model_dump(), gold.model_dump()]),
        "status": run.status.value,
        "output": final,
        "metrics": metrics,
        "usage_kind": "character-quarter estimate"
        if settings.provider == "mock"
        else "provider-reported; failures may be unreported",
        "errors": errors,
        "diagnostics": diagnostics,
        "trace_file": f"traces/{run.id}.json",
        "human_review": {
            "task": task.question,
            "gold": gold.model_dump(mode="json"),
            "workers": [
                a.model_dump(mode="json")
                for a in run.state.artifacts
                if a.producer.startswith("worker_")
            ],
        },
        "partition_diagnostics": partition_stats(gold, assignment.partitions)
        if task.benchmark_version == VERSION
        else {},
    }
    record["prompt_version"] = "v2" if task.benchmark_version == VERSION else "v1"
    write_json(
        output_dir / "traces" / f"{run.id}.json",
        {
            "run": run.model_dump(mode="json"),
            "events": [e.model_dump(mode="json") for e in await repository.events(run.id)],
            "calls": [c.model_dump(mode="json") for c in calls],
        },
    )
    write_json(output_dir / "records" / f"{run.id}.json", record)
    return record


async def execute_campaign(
    campaign: Path,
    phase: str,
    repetitions: int,
    settings: ModelSettings,
    seed: int,
    limit: int,
    version: str = "1.0.0",
    binding_path: Path | None = None,
    freeze_path: Path = FREEZE_PATH,
) -> Path:
    """Run whole paired blocks; persist every attempted case and never overwrite a phase."""
    if settings.provider == "real" and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "Real-model experiment pending because no provider credentials were available."
        )
    if settings.provider == "real" and "mock" in settings.model.lower():
        raise ValueError("Real runs require an explicit --model")
    output_dir = campaign / phase
    if output_dir.exists():
        raise ValueError("Phase already exists; preserve it and choose a new campaign/phase")
    endpoint = validate_endpoint(os.environ.get("MODEL_BASE_URL", "https://api.openai.com/v1/"))
    fingerprint = protocol_fingerprint(settings)
    binding: dict[str, Any] | None = None
    if settings.provider == "real":
        if phase != "pilot" or version != VERSION or repetitions != 1:
            raise ValueError("Only the frozen v2 real pilot is enabled; main/full are disabled")
        if binding_path is None:
            raise ValueError("A pre-run --binding is required for real pilot")
        binding = validate_binding(binding_path, settings, endpoint, seed, freeze_path)
    frozen = verify(freeze_path) if version == VERSION else None
    budget = CallBudget(campaign / "budget.sqlite", limit)
    plan = make_plan(phase, repetitions, limit - budget.used, version)
    print(json.dumps({"event": "PLAN", **plan}), flush=True)
    if settings.provider == "real" and plan["omitted_blocks"]:
        raise ValueError("Budget cannot fit the fixed 48-call pilot; do not silently shrink it")
    if not plan["blocks"]:
        raise ValueError("Budget cannot fit a complete five-condition block")
    output_dir.mkdir(parents=True)
    metadata: dict[str, Any] = {
        "experiment_id": uuid.uuid4().hex,
        "timestamp": timestamp(),
        "phase": phase,
        "provider": settings.provider,
        "settings": settings.model_dump(),
        "seed": seed,
        "benchmark_version": version,
        "metrics_version": "2.0.0",
        "freeze_sha256": frozen["freeze_sha256"] if frozen else None,
        "model_binding": binding,
        "endpoint": endpoint if settings.provider == "real" else "offline-mock",
        "protocol_fingerprint": fingerprint,
        "source": source_info(),
        "plan": plan,
        "budget_limit": limit,
        "budget_used_before": budget.used,
        "prompts": {p.name: p.read_text() for p in (ROOT / "prompts").iterdir()},
        "interpretation": "MOCK VALIDATION — NOT LLM RESULTS"
        if settings.provider == "mock"
        else "REAL MODEL EXPERIMENT",
    }
    write_json(output_dir / "manifest.json", metadata)
    records: list[dict[str, Any]] = []
    repository = SQLRepository(f"sqlite+aiosqlite:///{(output_dir / 'runtime.sqlite').resolve()}")
    await repository.initialize()
    try:
        async with httpx.AsyncClient(
            base_url=endpoint,
            timeout=settings.timeout_seconds,
        ) as client:
            base: ModelProvider = (
                MockProvider(respond)
                if settings.provider == "mock"
                else OpenAICompatibleProvider(client, os.environ["OPENAI_API_KEY"])
            )
            provider = AuditedProvider(base, budget, output_dir / "call-journal")
            stop = False
            for task_id, repetition in plan["blocks"]:
                if stop:
                    break
                configs = [c for c in configurations() if c.id in plan["conditions"]]
                case_seed = seed + repetition
                random.Random(digest([task_id, case_seed, "condition-order"])).shuffle(configs)
                for config in configs:
                    record = await run_case(
                        repository,
                        provider,
                        settings,
                        task_id,
                        config,
                        case_seed,
                        repetition,
                        metadata["experiment_id"],
                        metadata,
                        output_dir,
                    )
                    records.append(record)
                    write_json(
                        output_dir / "results.json", {"metadata": metadata, "records": records}
                    )
                    print(
                        json.dumps(
                            {
                                "event": "CASE_COMPLETED",
                                "task": task_id,
                                "condition": config.id,
                                "repetition": repetition,
                                "status": record["status"],
                            }
                        ),
                        flush=True,
                    )
                    if settings.provider == "real" and (
                        record["errors"]
                        or record["status"] != "succeeded"
                        or any(
                            record["metrics"][key]
                            for key in ["context_leaks", "result_leaks", "gold_leaks"]
                        )
                    ):
                        metadata["stopped_reason"] = (
                            "runtime/schema/transport/boundary failure; "
                            "retain all attempted records"
                        )
                        stop = True
                        break
    finally:
        await repository.close()
        metadata["budget_used_after"] = budget.used
        metadata["finished_at"] = timestamp()
        metadata["executed_runs"] = len(records)
        write_json(output_dir / "results.json", {"metadata": metadata, "records": records})
        human_review(
            {"metadata": metadata, "records": records}, output_dir / "pilot-human-review.md"
        )
    return output_dir / "results.json"
