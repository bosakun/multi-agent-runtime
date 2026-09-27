"""Composition root; infrastructure is injected into the runtime."""

import os
from dataclasses import dataclass

import httpx

from app.agents.executor import AgentExecutor
from app.core.models import WorkflowInput
from app.llm.mock_provider import MockProvider
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelProvider
from app.observability.logging import configure_logging
from app.orchestration.orchestrator import Observer, Orchestrator
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository
from app.tools.gateway import ToolRegistry
from demos.catalog import Mode, catalog, configure, schema_registry
from demos.mock import respond
from demos.tools import register_tools


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite+aiosqlite:///runtime.db"
    provider: str = "mock"
    model: str = "deterministic-v1"
    base_url: str = "https://api.openai.com/v1/"
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///runtime.db"),
            provider=os.getenv("MODEL_PROVIDER", "mock"),
            model=os.getenv("MODEL_NAME", "deterministic-v1"),
            base_url=os.getenv("MODEL_BASE_URL", "https://api.openai.com/v1/"),
            api_key=os.getenv("MODEL_API_KEY", ""),
        )


class RuntimeService:
    def __init__(
        self,
        settings: Settings,
        *,
        provider: ModelProvider | None = None,
        observer: Observer | None = None,
    ) -> None:
        self.settings = settings
        self.repository = SQLRepository(settings.database_url)
        self.client: httpx.AsyncClient | None = None
        if provider is None:
            if settings.provider == "mock":
                provider = MockProvider(respond)
            elif settings.provider == "openai":
                if not settings.api_key or settings.model == "deterministic-v1":
                    raise ValueError("Set MODEL_API_KEY and MODEL_NAME for the openai provider")
                self.client = httpx.AsyncClient(
                    base_url=settings.base_url.rstrip("/") + "/", timeout=60, follow_redirects=False
                )
                provider = OpenAICompatibleProvider(self.client, settings.api_key)
            else:
                raise ValueError("Unknown MODEL_PROVIDER")
        self.tools = ToolRegistry()
        register_tools(self.tools)
        self.orchestrator = Orchestrator(
            self.repository,
            ContextBuilder(self.repository),
            AgentExecutor({settings.provider: provider}, schema_registry()),
            self.tools,
            observer,
        )

    async def initialize(self) -> None:
        configure_logging()
        await self.repository.initialize()
        entries = catalog()
        await self.repository.register(
            [agent for _, agents in entries.values() for agent in agents.values()],
            [workflow for workflow, _ in entries.values()],
        )

    async def create_run(
        self,
        workflow_id: str,
        task: WorkflowInput,
        mode: Mode = "isolated",
        *,
        approval: bool = False,
    ) -> str:
        workflow, agents = configure(workflow_id, task, mode, approval=approval)
        for agent in agents.values():
            agent.model.provider = self.settings.provider
            agent.model.model = self.settings.model
        run = await self.orchestrator.create(workflow, agents, task)
        return run.id

    async def close(self) -> None:
        await self.orchestrator.shutdown()
        if self.client:
            await self.client.aclose()
        await self.repository.close()
