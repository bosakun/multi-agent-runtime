"""Fresh 206-reservation campaign, immutable ancestors and explicit two-worker reuse."""

import json
import os
import random
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any

import httpx
from epistemic.conditions import configurations
from epistemic.models import CallRecord
from epistemic.paths import ROOT, digest
from epistemic.runner import timestamp
from external_benchmarks import runner as pilot
from external_benchmarks.conditions import build
from external_benchmarks.dataset import SEED, load_public, supporting_pairs
from external_benchmarks.models import FinalAnswer, PrivateGold
from external_benchmarks.provenance import file_sha256
from external_benchmarks.scoring import score
from hotpot_main import runner as main
from native_pilot.pilot26 import EXPECTED_DIGEST, host_probe
from operational_diagnostics.budget_experiment import exclusive
from operational_recovery.pilot24 import read_signed, signed
from prospective_pilot.budget import ClosedCallBudget
from pydantic import JsonValue

from app.agents.executor import AgentExecutor
from app.core.models import Event, Run, Status
from app.llm.mock_provider import MockProvider
from app.orchestration.orchestrator import Orchestrator
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository
from app.tools.gateway import ToolRegistry
from hotpot_recovery.provider import AppendOnlyAuditedProvider, ExclusiveNativeProvider

CAMPAIGN = ROOT / "runs/hotpotqa-protocol32-qwen3-14b-windows"
FREEZE = ROOT / "freezes/hotpotqa-dev-distractor-protocol-3.2.json"
MOCK = ROOT.parents[1] / "reports/hotpotqa-recovery-mock"
FAILED_QID = "5adc0c2b55429947ff1738db"
REUSED = {"worker_1", "worker_2"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def copy_new(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(source.read_bytes())
    if file_sha256(source) != file_sha256(destination):
        raise ValueError("Immutable source copy differs")


def controls() -> dict[str, Any]:
    return {
        **main.controls(),
        "protocol_version": "hotpotqa-3.2",
        "phase": "operational_recovery",
        "planned_runs": 61,
        "planned_calls": 206,
        "hard_call_limit": 206,
        "cumulative_calls": 510,
        "cumulative_reservations": 511,
        "prior_reservations": 305,
        "prior_native_responses": 304,
        "restored_workers": sorted(REUSED),
        "failed_question": FAILED_QID,
        "failed_condition": "C1",
        "journal_strategy": "exclusive_append_only_snapshots_and_single_final_write",
        "authorization": "User explicitly approved minimum recovery, ceiling 511",
    }


def sources() -> dict[str, str]:
    paths = list((ROOT / "hotpot_recovery").glob("*.py")) + [
        ROOT / "hotpot_resume.py",
        ROOT / "docs/protocol-3.2-hotpotqa-recovery.md",
        ROOT / "tests/test_hotpot_recovery.py",
        ROOT.parents[1] / "scripts/audit_hotpot_recovery_completion.py",
        ROOT.parents[1] / "scripts/audit_hotpot_completion.py",
    ]
    return {
        **main.sources(),
        **{p.relative_to(ROOT.parents[1]).as_posix(): file_sha256(p) for p in paths},
    }


def fingerprint(mock: bool) -> str:
    return digest({"files": sources(), "controls": controls(), "mock": mock})


def prior_files() -> dict[str, str]:
    return {
        str(p.resolve()): file_sha256(p)
        for campaign in [pilot.CAMPAIGN, main.CAMPAIGN]
        for p in sorted(campaign.rglob("*"))
        if p.is_file()
    }


def prior() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    main.verify_binding()
    manifest = main.verify_data()
    base = load(pilot.CAMPAIGN / "pilot/results.json")
    previous = load(main.CAMPAIGN / "additional/results.json")
    meta = previous["metadata"]
    normal = [r for r in previous["records"] if r["status"] == "succeeded"]
    partial = [r for r in previous["records"] if r["status"] != "succeeded"]
    if (
        meta["executed_runs"] != 72
        or meta["model_calls"] != 251
        or not meta["finished_at"]
        or meta["stopped_reason"] != "runtime/schema/transport/access failure"
        or meta["fingerprint"] != main.fingerprint(False)
        or meta["dataset_sha256"] != manifest["sha256"]
        or main.ledger_used(main.CAMPAIGN / "budget.sqlite") != 251
        or len(normal) != 71
        or len(partial) != 1
        or (partial[0]["question_id"], partial[0]["condition"]) != (FAILED_QID, "C1")
        or partial[0]["status"] != "partial"
        or partial[0]["calls"] != 3
        or partial[0]["errors"] != ["agent_internal_error"]
        or any(r["errors"] or any(r["audit"].values()) for r in normal)
        or len({(r["question_id"], r["condition"]) for r in previous["records"]}) != 72
    ):
        raise ValueError("Prior terminal failure/prefix changed")
    return base, previous, manifest


def work_grid() -> list[tuple[str, str]]:
    base, previous, manifest = prior()
    done = {
        (r["question_id"], r["condition"])
        for r in base["records"] + previous["records"]
        if r["status"] == "succeeded"
    }
    result: list[tuple[str, str]] = []
    for qid in manifest["task_ids"]:
        configs = list(configurations())
        random.Random(digest([SEED, qid, "condition-order"])).shuffle(configs)
        result.extend((qid, c.id) for c in configs if (qid, c.id) not in done)
    if len(done) != 89 or len(result) != 61 or result[0] != (FAILED_QID, "C1"):
        raise ValueError("Recovery grid drift")
    if (
        sum(2 if (qid, c) == (FAILED_QID, "C1") else 1 if c == "C0" else 4 for qid, c in result)
        != 206
    ):
        raise ValueError("Recovery is not exactly 206 new reservations")
    return result


def source_run() -> Run:
    _, previous, _ = prior()
    record = next(r for r in previous["records"] if r["status"] == "partial")
    db_path = main.CAMPAIGN / "additional/runtime.sqlite"
    with closing(sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        row = db.execute("SELECT payload FROM runs WHERE id=?", (record["run_id"],)).fetchone()
    if row is None:
        raise ValueError("Missing source run")
    run = Run.model_validate_json(row[0])
    if run.status != Status.PARTIAL or run.state.nodes != {
        "worker_0": Status.FAILED,
        "worker_1": Status.SUCCEEDED,
        "worker_2": Status.SUCCEEDED,
        "synthesizer": Status.SKIPPED,
    }:
        raise ValueError("Source node status drift")
    return run


def reuse_calls() -> list[tuple[Path, CallRecord]]:
    result = []
    root = main.CAMPAIGN / "additional/call-journal" / FAILED_QID / "C1"
    calls = [(p, CallRecord.model_validate(load(p))) for p in sorted(root.glob("*.json"))]
    failed = [c for _, c in calls if c.error]
    if (
        len(calls) != 3
        or len(failed) != 1
        or failed[0].agent_id != "worker_0"
        or (failed[0].error != "PermissionError" or failed[0].response is not None)
    ):
        raise ValueError("Failed reservation history changed")
    for path, call in calls:
        if call.agent_id in REUSED:
            if call.error or not call.response or not call.backend_request:
                raise ValueError("Cannot reuse unsuccessful worker")
            result.append((path, call))
    if {c.agent_id for _, c in result} != REUSED:
        raise ValueError("Missing two successful workers")
    return result


async def restore(run: Run, repository: SQLRepository, *, mock: bool) -> list[CallRecord]:
    old = source_run()
    if old.state.task != run.state.task or old.workflow != run.workflow:
        raise ValueError("Recovered public input/workflow drift")
    for key, definition in run.agents.items():
        original = old.agents[key].model_copy(deep=True)
        if mock:
            original.model.provider = "mock"
        if original != definition:
            raise ValueError("Recovered role/access/control drift")
    calls = [c for _, c in reuse_calls()]
    successful = [a for a in old.state.agent_runs if a.agent_id in REUSED]
    artifacts = [a for a in old.state.artifacts if a.producer in REUSED]
    messages = [m for m in old.state.messages if m.sender in REUSED]
    if len(successful) != 2 or len(artifacts) != 2 or len(messages) != 2:
        raise ValueError("Source artifact/result/message inventory drift")
    for call in calls:
        agent = next(a for a in successful if a.agent_id == call.agent_id)
        artifact = next(a for a in artifacts if a.producer == call.agent_id)
        if (
            agent.status != Status.SUCCEEDED
            or agent.attempts != 1
            or not agent.result
            or agent.result.error
            or not call.response
            or agent.result.output != call.response["output"]
            or artifact.payload != agent.result.output
            or artifact.readers != ["synthesizer"]
        ):
            raise ValueError("Reuse output provenance invalid")
        run.state.nodes[call.agent_id] = Status.SUCCEEDED
    run.state.agent_runs = [a.model_copy(deep=True) for a in successful]
    run.state.artifacts = [a.model_copy(deep=True) for a in artifacts]
    run.state.messages = [m.model_copy(deep=True) for m in messages]
    run.event_count += 1
    restored_ids: list[JsonValue] = [key for key in sorted(REUSED)]
    event = Event(
        run_id=run.id,
        sequence=run.event_count,
        kind="IMMUTABLE_WORKERS_RESTORED",
        data={"source_run_id": old.id, "agents": restored_ids, "new_model_calls": 0},
    )
    await repository.save(run, [event], run.revision)
    return calls


class RecoveryOrchestrator(Orchestrator):
    def _collect(self, run: Any, node: Any, record: Any, pending: Any) -> None:
        super()._collect(run, node, record, pending)
        # Restoration must not change the ordinary worker-order synthesizer projection.
        run.state.artifacts.sort(key=lambda a: a.node_id)
        run.state.messages.sort(key=lambda m: m.sender)


def integral(data: dict[str, Any]) -> bool:
    meta, records = data["metadata"], data["records"]
    return (
        len(records) == meta["executed_runs"] == 61
        and meta["model_calls"] == 206
        and not meta["stopped_reason"]
        and {(r["question_id"], r["condition"]) for r in records} == set(work_grid())
        and sum(r["new_calls"] for r in records) == 206
        and sum(r["reused_calls"] for r in records) == 2
        and all(
            r["status"] == "succeeded"
            and not r["errors"]
            and not any(r["audit"].values())
            and r["calls"] == (1 if r["condition"] == "C0" else 4)
            for r in records
        )
    )


async def bind() -> None:
    if CAMPAIGN.exists() or FREEZE.exists():
        raise ValueError("Require fresh recovery campaign and freeze")
    prior()
    gate = load(MOCK / "results.json")
    if (
        not integral(gate)
        or not gate["metadata"]["operational_integrity"]
        or gate["metadata"]["fingerprint"] != fingerprint(True)
        or main.ledger_used(MOCK / "budget.sqlite") != 206
    ):
        raise ValueError("Current-source complete 206-call Mock gate required")
    host = await host_probe()
    freeze = signed(
        {
            **controls(),
            "files": sources(),
            "prior_files": prior_files(),
            "dataset_sha256": main.verify_data()["sha256"],
            "work_grid": work_grid(),
            "mock_sha256": file_sha256(MOCK / "results.json"),
        }
    )
    exclusive(FREEZE, freeze)
    exclusive(
        CAMPAIGN / "binding.json",
        signed(
            {
                **controls(),
                "freeze_sha256": freeze["sha256"],
                "campaign": str(CAMPAIGN.resolve()),
                "backend_version": host["ollama"]["version"],
                "host": host,
            }
        ),
    )


def verify_binding() -> dict[str, Any]:
    prior()
    freeze, binding = read_signed(FREEZE), read_signed(CAMPAIGN / "binding.json")
    if (
        any(v.get(k) != value for v in (freeze, binding) for k, value in controls().items())
        or freeze["files"] != sources()
        or freeze["prior_files"] != prior_files()
        or freeze["dataset_sha256"] != main.verify_data()["sha256"]
        or freeze["work_grid"] != [list(cell) for cell in work_grid()]
        or freeze["mock_sha256"] != file_sha256(MOCK / "results.json")
        or binding["freeze_sha256"] != freeze["sha256"]
        or binding["campaign"] != str(CAMPAIGN.resolve())
    ):
        raise ValueError("Recovery source/data/ancestor/binding drift")
    return binding


async def execute(*, mock: bool = False, transport: httpx.AsyncBaseTransport | None = None) -> Path:
    base_data, previous, manifest = prior()
    grid = work_grid()
    binding = None if mock else verify_binding()
    if int(os.environ.get("MAX_MODEL_CALLS", "206")) < 206:
        raise ValueError("Entire 206-call recovery must fit budget")
    target = MOCK if mock else CAMPAIGN / "recovery"
    if target.exists() or (
        not mock and sorted(p.name for p in CAMPAIGN.iterdir()) != ["binding.json"]
    ):
        raise ValueError("Recovery consumed; no retry/resume/overwrite")
    host = None if mock else await host_probe()
    if not mock:
        assert host is not None and binding is not None
        if (
            host["ollama"]["version"] != binding["backend_version"]
            or host["ollama"]["digest"] != EXPECTED_DIGEST
        ):
            raise ValueError("Host/model drift")
    target.mkdir(parents=True, exist_ok=False)
    if host:
        exclusive(target / "backend.json", host)
    budget_path = target / "budget.sqlite" if mock else CAMPAIGN / "budget.sqlite"
    budget = ClosedCallBudget(budget_path, 206)
    meta = {
        **controls(),
        "experiment_id": uuid.uuid4().hex,
        "started_at": timestamp(),
        "provider": "mock" if mock else "real",
        "fingerprint": fingerprint(mock),
        "dataset_sha256": manifest["sha256"],
        "task_ids": manifest["task_ids"],
        "pilot_task_ids": manifest["pilot_task_ids"],
        "model_binding": binding,
        "executed_runs": 0,
        "model_calls": 0,
        "stopped_reason": None,
        "prior_result_hashes": {
            str(p): file_sha256(p)
            for p in [
                pilot.CAMPAIGN / "pilot/results.json",
                main.CAMPAIGN / "additional/results.json",
            ]
        },
        "interpretation": "MOCK RECOVERY PLUMBING WITH REAL PREFIX; NOT PERFORMANCE"
        if mock
        else "REAL HOTPOTQA OPERATIONAL RECOVERY",
    }
    records: list[dict[str, Any]] = []
    data = {"metadata": meta, "records": records}
    exclusive(target / "manifest.json", meta)
    repository = SQLRepository(
        "sqlite+aiosqlite:///" + (target / "runtime.sqlite").resolve().as_posix()
    )
    try:
        await repository.initialize()
        questions = {q.id: q for q in load_public(main.BUNDLE, manifest["task_ids"])}
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:11434/",
            timeout=1200,
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        ) as client:
            for qid, condition_id in grid:
                question = questions[qid]
                condition = next(c for c in configurations() if c.id == condition_id)
                workflow, agents, inputs, partitions = build(question, condition, mock=mock)
                native = (
                    MockProvider(pilot.single_mock if condition_id == "C0" else pilot.mock_response)
                    if mock
                    else ExclusiveNativeProvider(client, target / "http-observations")
                )
                journal = target / "call-journal" / qid / condition_id
                provider = AppendOnlyAuditedProvider(
                    native, budget, journal, max_concurrency=1, history=target / "journal-history"
                )
                client.event_hooks["request"] = [] if mock else [provider.audit_http_request]
                recovered = (qid, condition_id) == (FAILED_QID, "C1")
                runtime_type = RecoveryOrchestrator if recovered else Orchestrator
                runtime = runtime_type(
                    repository,
                    ContextBuilder(repository),
                    AgentExecutor({"mock" if mock else "real": provider}, pilot.schemas()),
                    ToolRegistry(),
                )
                print(
                    json.dumps(
                        {
                            "event": "CASE_STARTED",
                            "question": qid,
                            "condition": condition_id,
                            "new_reservations": budget.used,
                            "total_reservations": 305 + budget.used,
                        }
                    ),
                    flush=True,
                )
                run = await runtime.create(workflow, agents, inputs)
                restored = await restore(run, repository, mock=mock) if recovered else []
                reuse_provenance = []
                if recovered:
                    for path, call in reuse_calls():
                        destination = journal / ("reused_" + path.name)
                        copy_new(path, destination)
                        if file_sha256(destination) != file_sha256(path):
                            raise ValueError("Reuse copy is not byte-identical")
                        observation = (
                            main.CAMPAIGN
                            / "additional/http-observations"
                            / f"{call.run_id}_{call.agent_id}.json"
                        )
                        obs_copy = target / "http-observations" / observation.name
                        copy_new(observation, obs_copy)
                        if file_sha256(obs_copy) != file_sha256(observation):
                            raise ValueError("Reuse observation differs")
                        reuse_provenance.append(
                            {
                                "journal": str(path),
                                "journal_sha256": file_sha256(path),
                                "copy": str(destination),
                                "observation": str(observation),
                                "observation_copy": str(obs_copy),
                            }
                        )
                run = await runtime.execute(run.id)
                provider.finalize()
                new_calls = len(provider.calls)
                provider.calls.extend(restored)
                audit = pilot.audit_projection(question, agents, provider)
                final = next(
                    (a for a in run.state.artifacts if a.id in run.state.final_artifact_ids), None
                )
                answer = FinalAnswer.model_validate(final.payload) if final else None
                predictions = {
                    "answer": {qid: answer.answer if answer else ""},
                    "sp": {qid: supporting_pairs(question, answer.evidence_ids) if answer else []},
                }
                gold = PrivateGold.model_validate_json(
                    (main.BUNDLE / "gold" / f"{qid}.json").read_text(encoding="utf-8")
                )
                errors = [
                    a.result.error.code for a in run.state.agent_runs if a.result and a.result.error
                ]
                record = {
                    "question_id": qid,
                    "condition": condition_id,
                    "run_id": run.id,
                    "status": run.status.value,
                    "errors": errors,
                    "calls": len(provider.calls),
                    "new_calls": new_calls,
                    "reused_calls": len(restored),
                    "audit": audit,
                    "predictions": predictions,
                    "metrics": score(predictions, [gold]),
                    "output": answer.model_dump(mode="json") if answer else None,
                    "partitions": partitions,
                    "usage": run.usage().model_dump(),
                    "reuse_provenance": reuse_provenance,
                }
                records.append(record)
                exclusive(target / "records" / f"{qid}_{condition_id}.json", record)
                meta.update(executed_runs=len(records), model_calls=budget.used)
                if record["status"] != "succeeded" or errors or any(audit.values()):
                    meta["stopped_reason"] = "runtime/schema/transport/access failure"
                exclusive(target / "progress" / f"{len(records):04}.json", data)
                print(
                    json.dumps(
                        {
                            "event": "CASE_COMPLETED",
                            "question": qid,
                            "condition": condition_id,
                            "status": record["status"],
                            "new_reservations": budget.used,
                            "total_reservations": 305 + budget.used,
                        }
                    ),
                    flush=True,
                )
                if meta["stopped_reason"]:
                    break
    except BaseException as exc:
        meta["stopped_reason"] = type(exc).__name__
        raise
    finally:
        await repository.close()
        meta.update(executed_runs=len(records), model_calls=budget.used, finished_at=timestamp())
        if meta["fingerprint"] != fingerprint(mock):
            meta["stopped_reason"] = "source drift during recovery"
        meta["operational_integrity"] = integral(data)
        exclusive(target / "results.json", data)
    return target / "results.json"
