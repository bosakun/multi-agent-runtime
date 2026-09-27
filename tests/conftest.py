import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from app.core.models import WorkflowInput
from app.llm.mock_provider import MockProvider
from app.service import RuntimeService, Settings
from demos.mock import respond


@pytest.fixture
def provider() -> MockProvider:
    return MockProvider(respond, capture=True)


@pytest.fixture
async def service(provider: MockProvider) -> AsyncIterator[RuntimeService]:
    runtime = RuntimeService(
        Settings(database_url=os.getenv("TEST_POSTGRES_URL", "sqlite+aiosqlite:///:memory:")),
        provider=provider,
    )
    await runtime.initialize()
    yield runtime
    await runtime.close()


@pytest.fixture
def investigation_input() -> WorkflowInput:
    return WorkflowInput.model_validate_json(Path("examples/investigation.json").read_text())
