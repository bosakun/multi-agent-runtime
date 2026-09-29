"""Non-research mock workflow and closed-handle SQLite smoke; never uses environment provider."""

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from app.core.models import Status, WorkflowInput
from app.service import RuntimeService, Settings


async def smoke(repository: Path) -> dict[str, Any]:
    with TemporaryDirectory(prefix="runtime-host-smoke-") as directory:
        database = Path(directory) / "runtime.sqlite"
        service = RuntimeService(
            Settings(database_url="sqlite+aiosqlite:///" + database.as_posix(), provider="mock")
        )
        try:
            await service.initialize()
            raw = await asyncio.to_thread(
                (repository / "examples" / "investigation.json").read_text, encoding="utf-8"
            )
            task = WorkflowInput.model_validate(json.loads(raw))
            run_id = await service.create_run("investigation", task)
            run = await service.orchestrator.execute(run_id)
            result = {
                "provider": "mock",
                "research": False,
                "generation_calls": 0,
                "status": run.status.value,
                "mock_calls": run.usage().model_calls,
            }
        finally:
            await service.close()
        # On Windows a lingering open database handle prevents this rename/removal.
        renamed = database.with_name("closed.sqlite")
        database.rename(renamed)
        renamed.unlink()
        result["sqlite_closed_handle_check"] = "passed"
        result["passed"] = run.status == Status.SUCCEEDED
        return result
