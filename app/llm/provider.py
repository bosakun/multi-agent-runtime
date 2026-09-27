"""Model contracts contain only authorized context."""

from typing import Protocol

from pydantic import Field, JsonValue

from app.core.models import AgentContext, Model, ModelConfig, Usage


class ToolCall(Model):
    id: str
    name: str
    arguments: dict[str, JsonValue]


class ToolExchange(Model):
    call: ToolCall
    result: dict[str, JsonValue]


class ModelRequest(Model):
    agent_id: str
    instruction: str
    context: AgentContext
    config: ModelConfig
    output_schema: dict[str, JsonValue]
    tools: list[dict[str, JsonValue]] = Field(default_factory=list)
    exchanges: list[ToolExchange] = Field(default_factory=list)


class ModelResponse(Model):
    output: dict[str, JsonValue] | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)


class ModelProvider(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse: ...
