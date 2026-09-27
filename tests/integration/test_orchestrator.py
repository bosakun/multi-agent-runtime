import asyncio

import pytest

from app.core.errors import RuntimeFault
from app.core.models import Status
from app.llm.provider import ModelResponse
from app.orchestration.workflow import Condition, Edge, Node, WorkflowDefinition
from app.service import RuntimeService, Settings
from demos.catalog import configure


async def test_parallel_execution_and_ordered_events(service, provider, investigation_input):
    run_id = await service.create_run("investigation", investigation_input)
    run = await service.orchestrator.execute(run_id)
    assert run.status == Status.SUCCEEDED
    assert provider.max_active >= 2
    assert len(run.state.final_artifact_ids) == 1
    events = await service.repository.events(run_id)
    assert [e.sequence for e in events] == list(range(1, len(events) + 1))
    assert {e.kind for e in events} >= {
        "RUN_STARTED",
        "CONTEXT_BUILT",
        "MESSAGE_SENT",
        "ARTIFACT_CREATED",
        "STATE_UPDATED",
        "RUN_COMPLETED",
    }
    assert len(run.state.messages) == 5
    starts = [
        e.created_at
        for e in events
        if e.kind == "AGENT_STARTED" and e.node_id.startswith("investigator_")
    ]
    finishes = [
        e.created_at
        for e in events
        if e.kind == "AGENT_COMPLETED" and e.node_id.startswith("investigator_")
    ]
    assert max(starts) < min(finishes)


@pytest.mark.parametrize(
    "failure", [RuntimeFault("temporary", retryable=True), ModelResponse(output={"bad": True})]
)
async def test_retry_transient_and_malformed(service, provider, investigation_input, failure):
    provider.scripts["investigator_a"].append(failure)
    run_id = await service.create_run("investigation", investigation_input)
    run = await service.orchestrator.execute(run_id)
    record = next(a for a in run.state.agent_runs if a.agent_id == "investigator_a")
    assert record.status == Status.SUCCEEDED and record.attempts == 2
    assert run.usage().model_calls == 7
    assert "RETRY_SCHEDULED" in {e.kind for e in await service.repository.events(run_id)}


async def test_failure_does_not_destroy_independent_branches(
    service, provider, investigation_input
):
    provider.scripts["investigator_a"].append(RuntimeFault("permanent"))
    run_id = await service.create_run("investigation", investigation_input)
    run = await service.orchestrator.execute(run_id)
    assert run.status == Status.PARTIAL
    assert run.state.nodes["investigator_b"] == Status.SUCCEEDED
    assert run.state.nodes["reviewer"] == Status.SKIPPED
    assert run.state.nodes["synthesizer"] == Status.SKIPPED


async def test_partial_join_can_continue(service, provider, investigation_input):
    workflow, agents = configure("investigation", investigation_input)
    next(n for n in workflow.nodes if n.id == "reviewer").allow_failed_dependencies = True
    provider.scripts["investigator_a"].append(RuntimeFault("permanent"))
    run = await service.orchestrator.create(workflow, agents, investigation_input)
    run = await service.orchestrator.execute(run.id)
    assert run.status == Status.PARTIAL
    assert run.state.nodes["synthesizer"] == Status.SUCCEEDED


async def test_branch_skip_and_join(service, investigation_input):
    _, original = configure("investigation", investigation_input)
    base = original["investigator_a"]
    agents = {
        key: base.model_copy(update={"id": key, "publish_to": []}, deep=True)
        for key in ["start", "left", "right", "join"]
    }
    workflow = WorkflowDefinition(
        id="branch",
        description="conditional join",
        nodes=[Node(id=key, agent_id=key, final=key == "join") for key in agents],
        edges=[
            Edge(
                source="start",
                target="left",
                condition=Condition(field="uncertainty.confidence", equals=0.8),
            ),
            Edge(
                source="start",
                target="right",
                condition=Condition(field="uncertainty.confidence", equals=0.1),
            ),
            Edge(source="left", target="join"),
            Edge(source="right", target="join"),
        ],
    )
    run = await service.orchestrator.create(workflow, agents, investigation_input)
    run = await service.orchestrator.execute(run.id)
    assert run.state.nodes["right"] == Status.SKIPPED
    assert run.state.nodes["join"] == Status.SUCCEEDED


@pytest.mark.parametrize("approved", [True, False])
async def test_approval_survives_restart(tmp_path, investigation_input, approved):
    settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'resume.db'}")
    first = RuntimeService(settings)
    await first.initialize()
    run_id = await first.create_run("investigation", investigation_input, approval=True)
    paused = await first.orchestrator.execute(run_id)
    assert paused.status == Status.PAUSED
    assert not paused.state.final_artifact_ids
    await first.close()
    second = RuntimeService(settings)
    await second.initialize()
    try:
        await second.orchestrator.approve(run_id, "approval", approved)
        run = await second.orchestrator.execute(run_id)
        assert run.status == Status.SUCCEEDED
        assert run.state.nodes["synthesizer"] == (Status.SUCCEEDED if approved else Status.SKIPPED)
        assert len(run.state.agent_runs) == (6 if approved else 5)
    finally:
        await second.close()


async def test_cancel_running_tasks(service, provider, investigation_input):
    provider.delay_seconds = 5
    run_id = await service.create_run("investigation", investigation_input)
    task = asyncio.create_task(service.orchestrator.execute(run_id))
    async with asyncio.timeout(2):
        while provider.active == 0:  # noqa: ASYNC110 - observing a third-party protocol boundary
            await asyncio.sleep(0.001)
    cancelled = await service.orchestrator.cancel(run_id)
    assert cancelled.status == Status.CANCELLED
    assert (await task).status == Status.CANCELLED
    assert provider.active == 0
    assert (await service.repository.get(run_id)).status == Status.CANCELLED
    assert cancelled.usage().model_calls >= 1
    assert any(a.status == Status.CANCELLED for a in cancelled.state.agent_runs)


async def test_timeout_is_bounded(service, provider, investigation_input):
    workflow, agents = configure("investigation", investigation_input)
    agents["investigator_a"].execution.timeout_seconds = 0.001
    provider.delay_seconds = 0.02
    run = await service.orchestrator.create(workflow, agents, investigation_input)
    run = await service.orchestrator.execute(run.id)
    record = next(a for a in run.state.agent_runs if a.agent_id == "investigator_a")
    assert record.attempts == 2
    assert record.result.error.code == "agent_timeout"


async def test_resume_interrupted_checkpoint(service, investigation_input):
    run_id = await service.create_run("investigation", investigation_input)
    run = await service.repository.get(run_id)
    run.status = Status.RUNNING
    run.state.nodes["investigator_a"] = Status.RUNNING
    await service.repository.save(run, [], run.revision)
    recovered = await service.orchestrator.execute(run_id)
    assert recovered.status == Status.SUCCEEDED
    assert "RUN_RECOVERED" in {e.kind for e in await service.repository.events(run_id)}
