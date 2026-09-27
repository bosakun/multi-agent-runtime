"""SQLite/PostgreSQL adapter with atomic checkpoints and optimistic concurrency."""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from pydantic import JsonValue
from sqlalchemy import JSON, Column, Integer, MetaData, String, Table, insert, select, update
from sqlalchemy.engine import ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from app.core.errors import ConflictError
from app.core.models import AgentDefinition, Event, Run
from app.memory.store import MemoryScope
from app.orchestration.workflow import WorkflowDefinition

metadata = MetaData()
runs = Table(
    "runs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("revision", Integer, nullable=False),
    Column("payload", JSON, nullable=False),
)
events = Table(
    "events",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("sequence", Integer, primary_key=True),
    Column("payload", JSON, nullable=False),
)
snapshots = Table(
    "snapshots",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("revision", Integer, primary_key=True),
    Column("payload", JSON, nullable=False),
)
definitions = Table(
    "definitions",
    metadata,
    Column("kind", String(32), primary_key=True),
    Column("id", String(128), primary_key=True),
    Column("payload", JSON, nullable=False),
)
projections = Table(
    "projections",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("kind", String(32), primary_key=True),
    Column("id", String(128), primary_key=True),
    Column("payload", JSON, nullable=False),
)
memories = Table(
    "memories",
    metadata,
    Column("scope", String(16), primary_key=True),
    Column("namespace", String(160), primary_key=True),
    Column("key", String(128), primary_key=True),
    Column("payload", JSON, nullable=False),
)


class SQLRepository:
    def __init__(self, url: str = "sqlite+aiosqlite:///runtime.db") -> None:
        self.engine: AsyncEngine = create_async_engine(url)
        self._sqlite = self.engine.dialect.name == "sqlite"
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def _connection(self, *, write: bool = False) -> AsyncIterator[AsyncConnection]:
        # In-memory SQLite uses one physical connection. Concurrent logical
        # connections would otherwise roll back each other's transactions.
        if self._sqlite:
            await self._lock.acquire()
        try:
            manager = self.engine.begin() if write else self.engine.connect()
            async with manager as connection:
                yield connection
        finally:
            if self._sqlite:
                self._lock.release()

    async def initialize(self) -> None:
        """Convenient local bootstrap; deployed databases should use Alembic."""
        async with self._connection(write=True) as connection:
            await connection.run_sync(metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()

    async def register(
        self, agents: list[AgentDefinition], workflows: list[WorkflowDefinition]
    ) -> None:
        async with self._connection(write=True) as connection:
            for kind, items in (("agent", agents), ("workflow", workflows)):
                for item in items:
                    where = (definitions.c.kind == kind) & (definitions.c.id == item.id)
                    exists = await connection.scalar(select(definitions.c.id).where(where))
                    payload = item.model_dump(mode="json")
                    if exists is None:
                        await connection.execute(
                            insert(definitions).values(kind=kind, id=item.id, payload=payload)
                        )
                    else:
                        await connection.execute(
                            update(definitions).where(where).values(payload=payload)
                        )

    async def save(self, run: Run, pending: list[Event], expected_revision: int) -> None:
        if run.revision != expected_revision:
            raise ConflictError()
        if [event.sequence for event in pending] != list(
            range(run.event_count - len(pending) + 1, run.event_count + 1)
        ) or any(event.run_id != run.id for event in pending):
            raise ValueError("Invalid event sequence")
        new_revision = expected_revision + 1
        payload = run.model_dump(mode="json")
        payload["revision"] = new_revision
        try:
            async with self._connection(write=True) as connection:
                previous = await connection.scalar(
                    select(runs.c.payload).where(runs.c.id == run.id)
                )
                if previous is not None and previous["revision"] != expected_revision:
                    raise ConflictError()
                previous_count = previous["event_count"] if previous is not None else 0
                if run.event_count != previous_count + len(pending):
                    raise ValueError("Checkpoint must append contiguous events")
                if expected_revision == 0:
                    await connection.execute(
                        insert(runs).values(id=run.id, revision=new_revision, payload=payload)
                    )
                else:
                    result = await connection.execute(
                        update(runs)
                        .where(runs.c.id == run.id, runs.c.revision == expected_revision)
                        .values(revision=new_revision, payload=payload)
                    )
                    if result.rowcount != 1:
                        raise ConflictError()
                await connection.execute(
                    insert(snapshots).values(run_id=run.id, revision=new_revision, payload=payload)
                )
                for event in pending:
                    await connection.execute(
                        insert(events).values(
                            run_id=run.id,
                            sequence=event.sequence,
                            payload=event.model_dump(mode="json"),
                        )
                    )
                records: list[tuple[str, str, dict[str, Any]]] = []
                records.extend(
                    ("artifact", a.id, a.model_dump(mode="json")) for a in run.state.artifacts
                )
                records.extend(
                    ("message", m.id, m.model_dump(mode="json")) for m in run.state.messages
                )
                records.extend(
                    ("agent_run", a.id, a.model_dump(mode="json")) for a in run.state.agent_runs
                )
                records.append(("usage", run.id, run.usage().model_dump(mode="json")))
                for kind, item_id, record in records:
                    where = (
                        (projections.c.run_id == run.id)
                        & (projections.c.kind == kind)
                        & (projections.c.id == item_id)
                    )
                    exists = await connection.scalar(select(projections.c.id).where(where))
                    if exists is None:
                        await connection.execute(
                            insert(projections).values(
                                run_id=run.id, kind=kind, id=item_id, payload=record
                            )
                        )
                    else:
                        await connection.execute(
                            update(projections).where(where).values(payload=record)
                        )
        except IntegrityError as exc:
            raise ConflictError() from exc
        run.revision = new_revision

    async def get(self, run_id: str) -> Run:
        async with self._connection() as connection:
            payload = await connection.scalar(select(runs.c.payload).where(runs.c.id == run_id))
        if payload is None:
            raise KeyError(run_id)
        return Run.model_validate(payload)

    async def events(self, run_id: str) -> list[Event]:
        async with self._connection() as connection:
            rows: ScalarResult[Any] = await connection.scalars(
                select(events.c.payload)
                .where(events.c.run_id == run_id)
                .order_by(events.c.sequence)
            )
            return [Event.model_validate(row) for row in rows]

    async def replay(self, run_id: str, revision: int) -> Run:
        async with self._connection() as connection:
            payload = await connection.scalar(
                select(snapshots.c.payload).where(
                    snapshots.c.run_id == run_id, snapshots.c.revision == revision
                )
            )
        if payload is None:
            raise KeyError((run_id, revision))
        return Run.model_validate(payload)

    async def read(
        self, scope: MemoryScope, namespace: str, keys: list[str]
    ) -> dict[str, JsonValue]:
        if not keys:
            return {}
        async with self._connection() as connection:
            rows = await connection.execute(
                select(memories.c.key, memories.c.payload).where(
                    memories.c.scope == scope,
                    memories.c.namespace == namespace,
                    memories.c.key.in_(keys),
                )
            )
            return {row.key: json.loads(json.dumps(row.payload)) for row in rows}

    async def write(self, scope: MemoryScope, namespace: str, key: str, value: JsonValue) -> None:
        async with self._connection(write=True) as connection:
            where = (
                (memories.c.scope == scope)
                & (memories.c.namespace == namespace)
                & (memories.c.key == key)
            )
            exists = await connection.scalar(select(memories.c.key).where(where))
            if exists is None:
                await connection.execute(
                    insert(memories).values(
                        scope=scope, namespace=namespace, key=key, payload=value
                    )
                )
            else:
                await connection.execute(update(memories).where(where).values(payload=value))
