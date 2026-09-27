import asyncio

import pytest

from app.core.errors import ConflictError, RuntimeFault
from app.core.models import Artifact, ArtifactRef, Event, MessageEnvelope, Status, WorkflowState
from app.orchestration.router import route
from demos.catalog import configure


async def test_duplicate_execution_is_rejected(service, provider, investigation_input):
    provider.delay_seconds = 0.05
    run_id = await service.create_run("investigation", investigation_input)
    first = asyncio.create_task(service.orchestrator.execute(run_id))
    await asyncio.sleep(0)
    with pytest.raises(RuntimeFault, match="run_already_active"):
        await service.orchestrator.execute(run_id)
    assert (await first).status == Status.SUCCEEDED


async def test_concurrent_checkpoint_has_one_winner(service, investigation_input):
    run_id = await service.create_run("investigation", investigation_input)
    first = await service.repository.get(run_id)
    second = first.model_copy(deep=True)
    outcomes = await asyncio.gather(
        service.repository.save(first, [], first.revision),
        service.repository.save(second, [], second.revision),
        return_exceptions=True,
    )
    assert sum(isinstance(value, ConflictError) for value in outcomes) == 1
    assert (await service.repository.get(run_id)).revision == 2


async def test_gap_in_events_rejected_atomically(service, investigation_input):
    run_id = await service.create_run("investigation", investigation_input)
    run = await service.repository.get(run_id)
    run.event_count += 10
    event = Event(run_id=run_id, sequence=run.event_count, kind="invalid_gap")
    with pytest.raises(ValueError, match="contiguous"):
        await service.repository.save(run, [event], run.revision)
    assert (await service.repository.get(run_id)).revision == 1
    assert len(await service.repository.events(run_id)) == 1


async def test_exhausted_retry_records_failure_usage(service, provider, investigation_input):
    provider.scripts["investigator_a"].extend([RuntimeFault("overloaded", retryable=True)] * 2)
    run_id = await service.create_run("investigation", investigation_input)
    run = await service.orchestrator.execute(run_id)
    failed = next(a for a in run.state.agent_runs if a.agent_id == "investigator_a")
    assert failed.attempts == 2 and failed.result.usage.model_calls == 2
    assert failed.result.error.code == "overloaded"
    assert run.status == Status.PARTIAL


async def test_model_configuration_and_concurrency_are_per_agent(
    service, provider, investigation_input
):
    workflow, agents = configure("investigation", investigation_input)
    workflow.max_parallel = 1
    agents["investigator_a"].model.model = "model-a"
    agents["investigator_b"].model.model = "model-b"
    agents["investigator_a"].model.input_cost_per_million = 2
    run = await service.orchestrator.create(workflow, agents, investigation_input)
    run = await service.orchestrator.execute(run.id)
    assert provider.max_active == 1
    assert provider.requests[0].config.model == "model-a"
    assert provider.requests[1].config.model == "model-b"
    assert run.usage().cost_usd > 0


async def test_message_cannot_reference_other_producers_artifact(investigation_input):
    _, agents = configure("investigation", investigation_input)
    artifact = Artifact(
        name="note",
        version=1,
        producer="investigator_b",
        node_id="b",
        schema_id="findings",
        payload={},
        readers=["reviewer"],
    )
    state = WorkflowState(task=investigation_input, nodes={}, artifacts=[artifact])
    forged = MessageEnvelope(
        sender="investigator_a",
        recipients=["reviewer"],
        artifacts=[ArtifactRef(id=artifact.id, version=1)],
    )
    with pytest.raises(RuntimeFault, match="unauthorized_artifact_reference"):
        route(forged, state, agents)
    assert not state.messages


async def test_pause_without_decision_never_runs_final(service, investigation_input):
    run_id = await service.create_run("investigation", investigation_input, approval=True)
    first = await service.orchestrator.execute(run_id)
    second = await service.orchestrator.execute(run_id)
    assert first.status == second.status == Status.PAUSED
    assert len(first.state.agent_runs) == len(second.state.agent_runs) == 5
    assert not second.state.final_artifact_ids


async def test_cancel_pending_run_never_calls_provider(service, provider, investigation_input):
    run_id = await service.create_run("investigation", investigation_input)
    assert (await service.orchestrator.cancel(run_id)).status == Status.CANCELLED
    assert (await service.orchestrator.execute(run_id)).status == Status.CANCELLED
    assert not provider.requests
