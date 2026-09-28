"""Durable cross-process call budget and boundary audit (synthetic data only)."""

import sqlite3
import time
from pathlib import Path

from app.llm.provider import ModelProvider, ModelRequest, ModelResponse
from epistemic.models import CallRecord
from epistemic.paths import write_json


class BudgetExceeded(RuntimeError):
    pass


class CallBudget:
    """Reserve before dispatch; crashed/failed attempts are never refunded."""

    def __init__(self, path: Path, limit: int) -> None:
        if limit < 1:
            raise ValueError("Call limit must be positive")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.limit = limit
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY, used INTEGER)")
            db.execute("INSERT OR IGNORE INTO budget VALUES (1, 0)")

    @property
    def used(self) -> int:
        with sqlite3.connect(self.path) as db:
            return int(db.execute("SELECT used FROM budget WHERE id=1").fetchone()[0])

    def reserve(self) -> None:
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            used = int(db.execute("SELECT used FROM budget WHERE id=1").fetchone()[0])
            if used >= self.limit:
                raise BudgetExceeded("Model-call budget exhausted")
            db.execute("UPDATE budget SET used=used+1 WHERE id=1")


class AuditedProvider:
    def __init__(
        self, provider: ModelProvider, budget: CallBudget, journal: Path | None = None
    ) -> None:
        self.provider = provider
        self.budget = budget
        self.calls: list[CallRecord] = []
        self.journal = journal

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.budget.reserve()
        record = CallRecord(
            run_id=request.context.run_id,
            agent_id=request.agent_id,
            request=request.model_dump(mode="json"),
        )
        self.calls.append(record)
        journal_path = (
            (self.journal / f"{len(self.calls):04}_{record.run_id}_{record.agent_id}.json")
            if self.journal
            else None
        )
        if journal_path:
            write_json(journal_path, record.model_dump(mode="json"))
        started = time.perf_counter()
        try:
            response = await self.provider.generate(request)
            record.response = response.model_dump(mode="json")
            return response
        except BaseException as exc:
            # Exception text may include HTTP credentials or sensitive server bodies.
            record.error = type(exc).__name__
            raise
        finally:
            record.latency_ms = (time.perf_counter() - started) * 1000
            if journal_path:
                write_json(journal_path, record.model_dump(mode="json"))
