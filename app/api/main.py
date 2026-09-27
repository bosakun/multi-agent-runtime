"""Async run submission; no raw contexts in the default read API."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import ConflictError, RuntimeFault
from app.core.models import Model, Run, WorkflowInput
from app.observability.flow import mermaid, run_summary
from app.service import RuntimeService, Settings
from demos.catalog import Mode, catalog


class CreateRun(Model):
    workflow: str
    input: WorkflowInput
    mode: Mode = "isolated"
    approval: bool = False


class Approval(Model):
    approved: bool


def create_app(service: RuntimeService | None = None) -> FastAPI:
    runtime = service or RuntimeService(Settings.from_env())
    tasks: dict[str, asyncio.Task[Run]] = {}

    def completed(run_id: str, task: asyncio.Task[Run]) -> None:
        tasks.pop(run_id, None)
        if not task.cancelled() and task.exception() is not None:
            logging.getLogger(__name__).error('{"event":"background_execution_failed"}')

    def launch(run_id: str) -> None:
        if run_id in tasks:
            raise RuntimeFault("run_already_active")
        task = asyncio.create_task(runtime.orchestrator.execute(run_id))
        tasks[run_id] = task
        task.add_done_callback(lambda finished: completed(run_id, finished))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await runtime.initialize()
        yield
        await runtime.orchestrator.shutdown()
        if tasks:
            await asyncio.gather(*tasks.values(), return_exceptions=True)
        await runtime.close()

    api = FastAPI(title="Isolated Agent Runtime", version="0.1.0", lifespan=lifespan)

    @api.exception_handler(RuntimeFault)
    async def fault_handler(_: Request, exc: RuntimeFault) -> JSONResponse:
        return JSONResponse(
            status_code=409
            if isinstance(exc, ConflictError) or exc.code == "run_already_active"
            else 400,
            content={"error": exc.code},
        )

    @api.exception_handler(RequestValidationError)
    async def invalid_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI's default echoes invalid inputs; operators may submit private data.
        return JSONResponse(
            status_code=422,
            content={"error": "invalid_request", "fields": [list(e["loc"]) for e in exc.errors()]},
        )

    async def get_run(run_id: str) -> Run:
        try:
            return await runtime.repository.get(run_id)
        except KeyError as exc:
            raise HTTPException(404, "Run not found") from exc

    @api.post("/runs", status_code=202)
    async def create_run(request: CreateRun) -> dict[str, str]:
        if request.workflow not in catalog():
            raise HTTPException(404, "Workflow not found")
        run_id = await runtime.create_run(
            request.workflow, request.input, request.mode, approval=request.approval
        )
        launch(run_id)
        return {"id": run_id, "status": "accepted"}

    @api.get("/runs/{run_id}")
    async def read_run(run_id: str) -> dict[str, object]:
        return run_summary(await get_run(run_id))

    @api.get("/runs/{run_id}/events")
    async def read_events(run_id: str) -> list[dict[str, object]]:
        await get_run(run_id)
        return [event.model_dump(mode="json") for event in await runtime.repository.events(run_id)]

    @api.get("/runs/{run_id}/graph")
    async def read_graph(run_id: str) -> dict[str, str]:
        return {"mermaid": mermaid(await get_run(run_id))}

    @api.post("/runs/{run_id}/approvals/{node_id}")
    async def approve(run_id: str, node_id: str, decision: Approval) -> dict[str, object]:
        await get_run(run_id)
        return run_summary(await runtime.orchestrator.approve(run_id, node_id, decision.approved))

    @api.post("/runs/{run_id}/resume", status_code=202)
    async def resume(run_id: str) -> dict[str, str]:
        await get_run(run_id)
        launch(run_id)
        return {"id": run_id, "status": "accepted"}

    @api.post("/runs/{run_id}/cancel")
    async def cancel(run_id: str) -> dict[str, object]:
        await get_run(run_id)
        return run_summary(await runtime.orchestrator.cancel(run_id))

    @api.get("/agents")
    async def agents() -> list[dict[str, object]]:
        return [
            agent.model_dump(mode="json")
            for _, definitions in catalog().values()
            for agent in definitions.values()
        ]

    @api.get("/workflows")
    async def workflows() -> list[dict[str, object]]:
        return [workflow.model_dump(mode="json") for workflow, _ in catalog().values()]

    return api
