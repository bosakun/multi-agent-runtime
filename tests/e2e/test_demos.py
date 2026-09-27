import asyncio
from pathlib import Path

import pytest

from app.core.models import Status, WorkflowInput
from app.evaluation.runner import compare
from app.observability.flow import inspect_run, mermaid
from demos.schemas import FinalReport


@pytest.mark.parametrize("workflow,calls", [("investigation", 6), ("software_review", 6)])
@pytest.mark.parametrize("mode", ["single", "shared", "isolated"])
async def test_demo_modes(service, provider, workflow, calls, mode):
    task = WorkflowInput.model_validate_json(
        await asyncio.to_thread(Path(f"examples/{workflow}.json").read_text)
    )
    run_id = await service.create_run(workflow, task, mode)
    run = await service.orchestrator.execute(run_id)
    assert run.status == Status.SUCCEEDED
    single_calls = 2 if workflow == "software_review" else 1
    assert run.usage().model_calls == (single_calls if mode == "single" else calls)
    final = next(a for a in run.state.artifacts if a.id in run.state.final_artifact_ids)
    report = FinalReport.model_validate(final.payload)
    assert report.findings and report.decision == "needs_review"
    if workflow == "software_review":
        events = await service.repository.events(run_id)
        tool_events = [e for e in events if e.kind == "TOOL_COMPLETED"]
        assert len(tool_events) == 1
        assert tool_events[0].node_id == ("single" if mode == "single" else "security")
    if mode == "isolated":
        final_request = provider.requests[-1]
        assert not final_request.context.knowledge and not final_request.context.inputs
    assert "context:" in inspect_run(run)
    assert "artifact:" in mermaid(run) if mode != "single" else "flowchart TD" in mermaid(run)


@pytest.mark.parametrize("workflow", ["investigation", "software_review"])
async def test_evaluation_fixtures(workflow):
    report = await compare(
        workflow, Path(f"examples/{workflow}.json"), Path(f"examples/{workflow}.case.json")
    )
    rows = {row["mode"]: row for row in report["results"]}
    assert all(row["task_success"] for row in rows.values())
    assert rows["isolated"]["information_leakage"] == 0
    assert rows["shared"]["information_leakage"] > 0
    assert rows["single"]["model_calls"] == (2 if workflow == "software_review" else 1)
    assert rows["isolated"]["extra_raw_context_categories"] == 0
