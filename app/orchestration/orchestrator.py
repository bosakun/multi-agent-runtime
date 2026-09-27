"""Single-writer orchestration with detached workers and durable checkpoints."""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime

from pydantic import JsonValue

from app.agents.executor import AgentExecutor, evidence_ids
from app.core.errors import RuntimeFault
from app.core.models import (
    AgentDefinition,
    AgentResult,
    AgentRun,
    Artifact,
    ArtifactRef,
    Event,
    MessageEnvelope,
    Run,
    SafeError,
    Status,
    Usage,
    WorkflowInput,
    WorkflowState,
    now,
)
from app.observability.logging import log_event
from app.orchestration.router import publish, route
from app.orchestration.workflow import Node, WorkflowDefinition
from app.policies.context import ContextPolicy, context_categories
from app.repositories.base import Repository
from app.tools.gateway import ToolRegistry

Observer = Callable[[str, str | None, dict[str, JsonValue]], None]
Trace = list[tuple[str, dict[str, JsonValue], datetime]]


class Orchestrator:
    def __init__(
        self,
        repository: Repository,
        context: ContextPolicy,
        executor: AgentExecutor,
        tools: ToolRegistry,
        observer: Observer | None = None,
    ) -> None:
        self.repository = repository
        self._context = context
        self._executor = executor
        self._tools = tools
        self._observer = observer
        self._active: dict[str, asyncio.Task[Run]] = {}

    def _notify(self, kind: str, node: str | None, data: dict[str, JsonValue]) -> None:
        if self._observer:
            try:
                self._observer(kind, node, data)
            except Exception:
                # Diagnostics cannot change scheduling or leak observer exception content.
                logging.getLogger(__name__).warning('{"event":"observer_failed"}')

    def _event(
        self,
        run: Run,
        pending: list[Event],
        kind: str,
        node: str | None = None,
        data: dict[str, JsonValue] | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        run.event_count += 1
        pending.append(
            Event(
                run_id=run.id,
                sequence=run.event_count,
                kind=kind,
                node_id=node,
                data=data or {},
                created_at=occurred_at or now(),
            )
        )

    async def _checkpoint(self, run: Run, pending: list[Event]) -> None:
        run.updated_at = now()
        await self.repository.save(run, pending, run.revision)
        for event in pending:
            log_event(event)
        pending.clear()

    async def create(
        self, workflow: WorkflowDefinition, agents: dict[str, AgentDefinition], task: WorkflowInput
    ) -> Run:
        workflow = WorkflowDefinition.model_validate(workflow.model_dump())
        used_ids = {node.agent_id for node in workflow.nodes if node.agent_id is not None}
        if not used_ids.issubset(agents):
            raise RuntimeFault("unknown_agent")
        selected = {key: agents[key].model_copy(deep=True) for key in sorted(used_ids)}
        for key, agent in selected.items():
            if key != agent.id or not set(agent.publish_to).issubset(selected):
                raise RuntimeFault("invalid_agent_registration")
            self._executor.validate_definition(agent)
            for tool in agent.tools.allowed:
                self._tools.get(tool)
            for recipient in agent.publish_to:
                if agent.id not in selected[recipient].context.artifact_producers:
                    raise RuntimeFault("invalid_publication_policy")
        if any(key != value.id for key, value in task.knowledge.items()):
            raise RuntimeFault("knowledge_id_mismatch")
        run = Run(
            workflow_id=workflow.id,
            workflow=workflow.model_dump(mode="json"),
            agents=selected,
            state=WorkflowState(
                task=task.model_copy(deep=True),
                nodes={n.id: Status.PENDING for n in workflow.nodes},
            ),
        )
        pending: list[Event] = []
        self._event(
            run, pending, "RUN_CREATED", data={"workflow": workflow.id, "mode": workflow.mode}
        )
        await self._checkpoint(run, pending)
        return run

    async def execute(self, run_id: str) -> Run:
        if run_id in self._active:
            raise RuntimeFault("run_already_active")
        task = asyncio.create_task(self._execute(run_id))
        self._active[run_id] = task
        try:
            return await task
        finally:
            self._active.pop(run_id, None)

    async def _execute(self, run_id: str) -> Run:
        run = await self.repository.get(run_id)
        if run.status not in {Status.PENDING, Status.RUNNING, Status.PAUSED}:
            return run
        workflow = WorkflowDefinition.model_validate(run.workflow)
        pending: list[Event] = []
        if run.status == Status.RUNNING:
            # No external effects are assumed exactly once after an interrupted checkpoint.
            for node_id, status in run.state.nodes.items():
                if status == Status.RUNNING:
                    run.state.nodes[node_id] = Status.PENDING
            self._event(run, pending, "RUN_RECOVERED")
        for node in workflow.nodes:
            if run.state.nodes[node.id] == Status.PAUSED and node.id in run.state.approvals:
                run.state.nodes[node.id] = (
                    Status.SUCCEEDED if run.state.approvals[node.id] else Status.SKIPPED
                )
                self._event(
                    run,
                    pending,
                    "HUMAN_DECISION_APPLIED",
                    node.id,
                    {"approved": run.state.approvals[node.id]},
                )
        run.status = Status.RUNNING
        self._event(run, pending, "RUN_STARTED")
        await self._checkpoint(run, pending)
        workers: list[asyncio.Task[tuple[AgentRun, Trace]]] = []
        try:
            while True:
                ready: list[Node] = []
                progressed = False
                for node in workflow.nodes:
                    if run.state.nodes[node.id] != Status.PENDING:
                        continue
                    decision = workflow.decision(node, run.state)
                    if decision == "skip":
                        run.state.nodes[node.id] = Status.SKIPPED
                        self._event(run, pending, "NODE_SKIPPED", node.id)
                        progressed = True
                    elif decision == "ready":
                        if node.kind == "approval":
                            run.state.nodes[node.id] = Status.PAUSED
                            self._event(run, pending, "HUMAN_APPROVAL_REQUIRED", node.id)
                            self._notify("HUMAN_APPROVAL_REQUIRED", node.id, {})
                            progressed = True
                        else:
                            ready.append(node)
                batch = ready[: workflow.max_parallel]
                if batch:
                    for node in batch:
                        run.state.nodes[node.id] = Status.RUNNING
                        self._event(run, pending, "AGENT_SCHEDULED", node.id)
                    await self._checkpoint(run, pending)
                    workers = [asyncio.create_task(self._run_agent(run, node)) for node in batch]
                    results = await asyncio.gather(*workers)
                    workers = []
                    for node, (agent_run, trace) in zip(batch, results, strict=True):
                        for kind, data, timestamp in trace:
                            self._event(run, pending, kind, node.id, data, timestamp)
                        run.state.agent_runs.append(agent_run)
                        run.state.nodes[node.id] = agent_run.status
                        if agent_run.status == Status.SUCCEEDED:
                            self._collect(run, node, agent_run, pending)
                    self._event(run, pending, "STATE_UPDATED")
                    await self._checkpoint(run, pending)
                    continue
                if progressed:
                    await self._checkpoint(run, pending)
                    continue
                if Status.PAUSED in run.state.nodes.values():
                    run.status = Status.PAUSED
                    self._event(run, pending, "RUN_PAUSED")
                else:
                    failed = Status.FAILED in run.state.nodes.values()
                    succeeded = Status.SUCCEEDED in run.state.nodes.values()
                    run.status = (
                        (Status.PARTIAL if succeeded else Status.FAILED)
                        if failed
                        else Status.SUCCEEDED
                    )
                    self._event(run, pending, "RUN_COMPLETED", data={"status": run.status})
                await self._checkpoint(run, pending)
                return run
        except asyncio.CancelledError:
            for worker in workers:
                if not worker.done():
                    worker.cancel()
            if workers:
                cancelled_results = await asyncio.gather(*workers, return_exceptions=True)
                for outcome in cancelled_results:
                    if isinstance(outcome, BaseException):
                        continue
                    record, trace = outcome
                    for kind, data, timestamp in trace:
                        self._event(run, pending, kind, record.node_id, data, timestamp)
                    run.state.agent_runs.append(record)
                    run.state.nodes[record.node_id] = record.status
                    if record.status == Status.SUCCEEDED:
                        node = next(n for n in workflow.nodes if n.id == record.node_id)
                        self._collect(run, node, record, pending)
            for node_id, status in run.state.nodes.items():
                if status in {Status.RUNNING, Status.PENDING, Status.PAUSED}:
                    run.state.nodes[node_id] = Status.CANCELLED
            run.status = Status.CANCELLED
            self._event(run, pending, "RUN_CANCELLED")
            await self._checkpoint(run, pending)
            return run

    async def _run_agent(self, run: Run, node: Node) -> tuple[AgentRun, Trace]:
        assert node.agent_id is not None
        agent = run.agents[node.agent_id]
        record = AgentRun(node_id=node.id, agent_id=agent.id, model=agent.model.model)
        trace: Trace = []
        started = time.perf_counter()
        usage = Usage()

        def observe(kind: str, data: dict[str, JsonValue]) -> None:
            trace.append((kind, data, now()))
            self._notify(kind, node.id, data)

        try:
            context = await self._context.build_context(agent=agent, state=run.state, run_id=run.id)
            record.context_categories = context_categories(context)
            record.context_artifact_ids = [a.id for a in context.artifacts]
            observe(
                "CONTEXT_BUILT",
                {
                    "categories": list(record.context_categories),
                    "artifact_ids": list(record.context_artifact_ids),
                },
            )
            gateway = self._tools.bind(agent.tools, observe)
            for attempt in range(1, agent.execution.max_attempts + 1):
                record.attempts = attempt
                observe(
                    "AGENT_STARTED",
                    {"agent": agent.id, "attempt": attempt, "model": agent.model.model},
                )
                try:
                    async with asyncio.timeout(agent.execution.timeout_seconds):
                        result = await self._executor.execute(
                            agent, context.model_copy(deep=True), gateway, usage
                        )
                    record.result = result
                    record.status = Status.SUCCEEDED
                    break
                except TimeoutError:
                    failure = RuntimeFault("agent_timeout", retryable=True)
                except RuntimeFault as exc:
                    failure = exc
                except Exception:
                    failure = RuntimeFault("agent_internal_error")
                observe("AGENT_ATTEMPT_FAILED", {"code": failure.code, "attempt": attempt})
                if not failure.retryable or attempt == agent.execution.max_attempts:
                    raise failure
                observe("RETRY_SCHEDULED", {"attempt": attempt + 1})
                await asyncio.sleep(agent.execution.retry_delay_seconds * attempt)
        except asyncio.CancelledError:
            record.status = Status.CANCELLED
            record.result = AgentResult(
                status=Status.CANCELLED, usage=usage, error=SafeError(code="agent_cancelled")
            )
        except RuntimeFault as exc:
            record.status = Status.FAILED
            record.result = AgentResult(
                status=Status.FAILED,
                usage=usage,
                error=SafeError(code=exc.code, retryable=exc.retryable),
            )
        except Exception:
            record.status = Status.FAILED
            record.result = AgentResult(
                status=Status.FAILED, usage=usage, error=SafeError(code="context_error")
            )
        record.latency_ms = (time.perf_counter() - started) * 1000
        observe(
            {Status.SUCCEEDED: "AGENT_COMPLETED", Status.CANCELLED: "AGENT_CANCELLED"}.get(
                record.status, "AGENT_FAILED"
            ),
            {
                "latency_ms": round(record.latency_ms, 2),
                "attempts": record.attempts,
                "code": record.result.error.code if record.result and record.result.error else None,
                "usage": usage.model_dump(mode="json"),
            },
        )
        return record, trace

    def _collect(self, run: Run, node: Node, record: AgentRun, pending: list[Event]) -> None:
        assert record.result is not None and record.result.output is not None
        agent = run.agents[record.agent_id]
        version = (
            max(
                (
                    a.version
                    for a in run.state.artifacts
                    if a.producer == agent.id and a.name == node.id
                ),
                default=0,
            )
            + 1
        )
        artifact = Artifact(
            name=node.id,
            version=version,
            producer=agent.id,
            node_id=node.id,
            schema_id=agent.output_schema,
            payload=record.result.output,
            readers=agent.publish_to,
            evidence_ids=sorted(evidence_ids(record.result.output)),
        )
        publish(run.state, artifact)
        self._event(
            run,
            pending,
            "ARTIFACT_CREATED",
            node.id,
            {"artifact_id": artifact.id, "version": version, "producer": agent.id},
        )
        if agent.publish_to:
            message = MessageEnvelope(
                sender=agent.id,
                recipients=agent.publish_to,
                artifacts=[ArtifactRef(id=artifact.id, version=version)],
            )
            route(message, run.state, run.agents)
            self._event(
                run,
                pending,
                "MESSAGE_SENT",
                node.id,
                {
                    "message_id": message.id,
                    "sender": agent.id,
                    "recipients": list(message.recipients),
                    "artifact_id": artifact.id,
                },
            )
        if node.final:
            run.state.final_artifact_ids.append(artifact.id)

    async def approve(self, run_id: str, node_id: str, approved: bool) -> Run:
        if run_id in self._active:
            raise RuntimeFault("run_already_active")
        run = await self.repository.get(run_id)
        if run.status != Status.PAUSED or run.state.nodes.get(node_id) != Status.PAUSED:
            raise RuntimeFault("node_not_awaiting_approval")
        if node_id in run.state.approvals:
            raise RuntimeFault("approval_already_recorded")
        run.state.approvals[node_id] = approved
        pending: list[Event] = []
        self._event(run, pending, "HUMAN_DECISION_RECORDED", node_id, {"approved": approved})
        await self._checkpoint(run, pending)
        return run

    async def cancel(self, run_id: str) -> Run:
        if run_id in self._active:
            task = self._active[run_id]
            task.cancel()
            try:
                return await task
            except asyncio.CancelledError:
                pass
        run = await self.repository.get(run_id)
        if run.status in {Status.PENDING, Status.RUNNING, Status.PAUSED}:
            run.status = Status.CANCELLED
            for node_id, status in run.state.nodes.items():
                if status in {Status.PENDING, Status.RUNNING, Status.PAUSED}:
                    run.state.nodes[node_id] = Status.CANCELLED
            pending: list[Event] = []
            self._event(run, pending, "RUN_CANCELLED")
            await self._checkpoint(run, pending)
        return run

    async def shutdown(self) -> None:
        for run_id in list(self._active):
            await self.cancel(run_id)
