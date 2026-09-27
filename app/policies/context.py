"""Deny-by-default information projection."""

from typing import Protocol

from app.core.errors import RuntimeFault
from app.core.models import AgentContext, AgentDefinition, WorkflowState
from app.memory.store import MemoryStore, agent_namespace


class ContextPolicy(Protocol):
    async def build_context(
        self, *, agent: AgentDefinition, state: WorkflowState, run_id: str
    ) -> AgentContext: ...


class ContextBuilder:
    def __init__(self, memory: MemoryStore) -> None:
        self._memory = memory

    async def build_context(
        self, *, agent: AgentDefinition, state: WorkflowState, run_id: str
    ) -> AgentContext:
        policy = agent.context
        artifacts = [
            artifact
            for artifact in state.artifacts
            if artifact.producer in policy.artifact_producers and agent.id in artifact.readers
        ]
        visible_refs = {(a.id, a.version) for a in artifacts}
        messages = [
            message
            for message in state.messages
            if policy.receive_messages
            and agent.id in message.recipients
            and all((ref.id, ref.version) in visible_refs for ref in message.artifacts)
        ]
        context = AgentContext(
            agent_id=agent.id,
            run_id=run_id,
            task=state.task.task if policy.include_task else None,
            inputs={
                key: state.task.inputs[key] for key in policy.input_keys if key in state.task.inputs
            },
            knowledge=[
                state.task.knowledge[key]
                for key in policy.knowledge_ids
                if key in state.task.knowledge
            ],
            artifacts=artifacts,
            messages=messages,
            private_memory=await self._memory.read(
                "private", agent_namespace(run_id, agent.id), policy.private_memory_keys
            ),
            shared_memory=await self._memory.read("shared", run_id, policy.shared_memory_keys),
            long_term_memory=await self._memory.read(
                "long_term", agent.id, policy.long_term_memory_keys
            ),
        )
        # Round-trip severs all mutable references to authoritative state and memory.
        serialized = context.model_dump_json()
        if len(serialized) > policy.max_context_chars:
            raise RuntimeFault("context_budget_exceeded")
        return AgentContext.model_validate_json(serialized)


def context_categories(context: AgentContext) -> list[str]:
    categories = ["task"] if context.task is not None else []
    categories.extend(f"input:{key}" for key in sorted(context.inputs))
    categories.extend(f"knowledge:{item.id}" for item in context.knowledge)
    categories.extend(f"artifact:{item.producer}:v{item.version}" for item in context.artifacts)
    for name in ("private_memory", "shared_memory", "long_term_memory"):
        if getattr(context, name):
            categories.append(name)
    if context.messages:
        categories.append("messages")
    return categories
