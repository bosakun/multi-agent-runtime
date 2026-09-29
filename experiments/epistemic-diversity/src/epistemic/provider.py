"""Durable cross-process call budget and boundary audit (synthetic data only)."""

import asyncio
import json
import sqlite3
import time
from pathlib import Path

import httpx

from app.llm.openai_provider import TokenLimitParameter
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
        self,
        provider: ModelProvider,
        budget: CallBudget,
        journal: Path | None = None,
        *,
        max_concurrency: int | None = None,
        token_limit_parameter: TokenLimitParameter | None = None,
    ) -> None:
        self.provider = provider
        self.budget = budget
        self.calls: list[CallRecord] = []
        self.journal = journal
        self._semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else None
        self._token_limit_parameter = token_limit_parameter

    async def audit_http_request(self, request: httpx.Request) -> None:
        """Verify/journal serialized limit fields before HTTP transport sees the request."""
        body = json.loads(request.content)
        context = json.loads(body["messages"][1]["content"])
        records = [
            call
            for call in self.calls
            if call.run_id == context["run_id"]
            and call.agent_id == context["agent_id"]
            and call.backend_request is None
        ]
        if len(records) != 1 or self._token_limit_parameter is None:
            raise ValueError("HTTP request has no unique reserved call/explicit limit strategy")
        record = records[0]
        parameter = self._token_limit_parameter
        limits = {key: body[key] for key in ("max_tokens", "max_completion_tokens") if key in body}
        record.backend_request = {
            "token_limit_parameter": parameter,
            "token_limit_fields": limits,
            "thinking_fields": [
                key for key in ("think", "reasoning", "reasoning_effort") if key in body
            ],
        }
        self._checkpoint(record)
        config = record.request["config"]
        if not isinstance(config, dict) or limits != {parameter: config["max_output_tokens"]}:
            raise ValueError("Serialized token limit differs from the declared strategy/limit")
        if record.backend_request["thinking_fields"]:
            raise ValueError("Protocol must preserve model-default thinking without override")

    def _checkpoint(self, record: CallRecord) -> None:
        if self.journal is not None:
            index = self.calls.index(record) + 1
            write_json(
                self.journal / f"{index:04}_{record.run_id}_{record.agent_id}.json",
                record.model_dump(mode="json"),
            )

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if self._semaphore is not None:
            async with self._semaphore:
                return await self._generate(request)
        return await self._generate(request)

    async def _generate(self, request: ModelRequest) -> ModelResponse:
        self.budget.reserve()
        record = CallRecord(
            run_id=request.context.run_id,
            agent_id=request.agent_id,
            request=request.model_dump(mode="json"),
        )
        self.calls.append(record)
        self._checkpoint(record)
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
            self._checkpoint(record)
