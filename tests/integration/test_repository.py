import os

import pytest

from app.core.errors import ConflictError
from app.core.models import Event
from app.repositories.sql import SQLRepository
from app.service import RuntimeService, Settings


async def test_snapshot_replay_and_stale_writer_rollback(service, investigation_input):
    run_id = await service.create_run("investigation", investigation_input)
    initial = await service.repository.get(run_id)
    stale = initial.model_copy(deep=True)
    await service.orchestrator.execute(run_id)
    history = await service.repository.events(run_id)
    stale.event_count += 1
    event = Event(run_id=run_id, sequence=stale.event_count, kind="STALE_EVENT")
    with pytest.raises(ConflictError):
        await service.repository.save(stale, [event], stale.revision)
    assert len(await service.repository.events(run_id)) == len(history)
    replay = await service.repository.replay(run_id, 1)
    assert replay == initial
    assert replay.state.artifacts == []


async def test_missing_records(service):
    with pytest.raises(KeyError):
        await service.repository.get("missing")
    with pytest.raises(KeyError):
        await service.repository.replay("missing", 1)


@pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"), reason="Set TEST_POSTGRES_URL for PostgreSQL integration"
)
async def test_postgres_round_trip(investigation_input):
    service = RuntimeService(Settings(database_url=os.environ["TEST_POSTGRES_URL"]))
    await service.initialize()
    try:
        run_id = await service.create_run("investigation", investigation_input)
        run = await service.orchestrator.execute(run_id)
        assert run.status == "succeeded"
        assert (
            await service.repository.get(run_id)
        ).state.final_artifact_ids == run.state.final_artifact_ids
        assert await service.repository.events(run_id)
    finally:
        await service.close()


async def test_memory_persists_across_connections(tmp_path):
    url = f"sqlite+aiosqlite:///{tmp_path / 'memory.db'}"
    first = SQLRepository(url)
    await first.initialize()
    await first.write("long_term", "agent_a", "fact", {"value": "remember"})
    await first.close()
    second = SQLRepository(url)
    try:
        assert await second.read("long_term", "agent_a", ["fact"]) == {
            "fact": {"value": "remember"}
        }
        assert await second.read("long_term", "agent_b", ["fact"]) == {}
    finally:
        await second.close()
