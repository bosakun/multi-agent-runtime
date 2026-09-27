"""Compare runtime configurations without claiming mock intelligence gains."""

import asyncio
import time
from pathlib import Path

from pydantic import Field

from app.core.models import Model, Run, Status, WorkflowInput
from app.llm.mock_provider import MockProvider
from app.llm.provider import ModelRequest
from app.service import RuntimeService, Settings
from demos.catalog import Mode, configure
from demos.mock import respond
from demos.schemas import FinalReport


class ExpectedClaim(Model):
    subject: str
    value: str
    evidence_ids: list[str] = Field(default_factory=list)


class EvaluationCase(Model):
    expected_claims: list[ExpectedClaim]
    expected_conflicts: list[str] = Field(default_factory=list)
    forbidden_markers: dict[str, list[str]] = Field(default_factory=dict)


def score(
    run: Run, case: EvaluationCase, requests: list[ModelRequest], latency_ms: float
) -> dict[str, object]:
    finals = [a for a in run.state.artifacts if a.id in run.state.final_artifact_ids]
    report = FinalReport.model_validate(finals[-1].payload) if finals else None
    expected = {(c.subject, c.value): set(c.evidence_ids) for c in case.expected_claims}
    observed = {(f.subject, f.value) for f in report.findings} if report else set()
    unsupported = (
        sum(
            (f.subject, f.value) not in expected
            or not set(f.evidence_ids).issubset(expected.get((f.subject, f.value), set()))
            or bool(expected.get((f.subject, f.value)))
            and not f.evidence_ids
            for f in report.findings
        )
        if report
        else 0
    )
    found_conflicts = {c.subject for c in report.conflicts} if report else set()
    missing_conflicts = set(case.expected_conflicts) - found_conflicts
    leakage = 0
    for request in requests:
        context = request.context.model_dump_json()
        results = "\n".join(
            a.model_dump_json() for a in run.state.artifacts if a.producer == request.agent_id
        )
        leakage += sum(
            marker in context or marker in results
            for marker in case.forbidden_markers.get(request.agent_id, [])
        )
    coverage = len(observed & expected.keys()) / len(expected) if expected else 1.0
    usage = run.usage()
    failures = sum(a.status == Status.FAILED for a in run.state.agent_runs)
    return {
        "run_id": run.id,
        "mode": run.workflow["mode"],
        "provider": "mock",
        "task_success": bool(report)
        and coverage == 1
        and not unsupported
        and not missing_conflicts
        and not failures,
        "completeness": coverage,
        "contradictions": len(found_conflicts),
        "missed_conflicts": len(missing_conflicts),
        "unsupported_claims": unsupported,
        "information_leakage": leakage,
        "agent_failures": failures,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "model_calls": usage.model_calls,
        "cost_estimate_usd": usage.cost_usd,
        "latency_ms": round(latency_ms, 2),
    }


async def compare(workflow: str, input_path: Path, case_path: Path) -> dict[str, object]:
    task = WorkflowInput.model_validate_json(await asyncio.to_thread(input_path.read_text))
    case = EvaluationCase.model_validate_json(await asyncio.to_thread(case_path.read_text))
    rows: list[dict[str, object]] = []
    for mode in ("single", "shared", "isolated"):
        selected_mode: Mode = mode
        provider = MockProvider(respond, capture=True)
        service = RuntimeService(
            Settings(database_url="sqlite+aiosqlite:///:memory:"), provider=provider
        )
        await service.initialize()
        try:
            started = time.perf_counter()
            run_id = await service.create_run(workflow, task, selected_mode)
            run = await service.orchestrator.execute(run_id)
            row = score(run, case, provider.requests, (time.perf_counter() - started) * 1000)
            _, isolated_agents = configure(workflow, task)
            row["extra_raw_context_categories"] = sum(
                len(
                    set(request.context.inputs)
                    - set(isolated_agents[request.agent_id].context.input_keys)
                )
                + len(
                    {k.id for k in request.context.knowledge}
                    - set(isolated_agents[request.agent_id].context.knowledge_ids)
                )
                for request in provider.requests
                if request.agent_id in isolated_agents
            )
            rows.append(row)
        finally:
            await service.close()
    return {
        "workflow": workflow,
        "methodology": (
            "Deterministic fixture rules, exact claim/evidence matching. "
            "Tokens are character-count estimates. Leakage counts fixture canaries relative "
            "to isolated policy, even in the intentionally shared baseline. "
            "Single-agent scope intentionally includes all inputs. "
            "Latency includes SQLite checkpoints. No real-model quality or cost claim."
        ),
        "results": rows,
    }
