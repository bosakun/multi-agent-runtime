"""Agent-bound authority, argument schemas, budgets and timeouts."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pydantic import BaseModel, JsonValue, ValidationError

from app.core.errors import RuntimeFault
from app.core.models import ToolAccess

ToolHandler = Callable[[BaseModel], Awaitable[BaseModel]]
ToolObserver = Callable[[str, dict[str, JsonValue]], None]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError("Duplicate tool")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise RuntimeFault("unknown_tool") from exc

    def bind(self, policy: ToolAccess, observer: ToolObserver) -> "ToolGateway":
        return ToolGateway({name: self.get(name) for name in policy.allowed}, policy, observer)


class ToolGateway:
    def __init__(
        self, tools: dict[str, ToolDefinition], policy: ToolAccess, observer: ToolObserver
    ) -> None:
        self._tools = tools
        self._policy = policy.model_copy(deep=True)
        self._observer = observer
        self._calls = 0

    def descriptions(self) -> list[dict[str, JsonValue]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema.model_json_schema(),
            }
            for tool in self._tools.values()
        ]

    async def invoke(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if name not in self._tools:
            self._observer("TOOL_DENIED", {"code": "tool_not_allowed"})
            raise RuntimeFault("tool_not_allowed")
        if self._calls >= self._policy.max_calls:
            raise RuntimeFault("tool_budget_exceeded")
        self._calls += 1
        tool = self._tools[name]
        try:
            parsed = tool.input_schema.model_validate(arguments)
        except ValidationError as exc:
            raise RuntimeFault("invalid_tool_arguments") from exc
        self._observer("TOOL_STARTED", {"tool": name})
        try:
            async with asyncio.timeout(self._policy.timeout_seconds):
                value = await tool.handler(parsed)
            output = tool.output_schema.model_validate(value).model_dump(mode="json")
        except TimeoutError as exc:
            self._observer("TOOL_FAILED", {"tool": name, "code": "tool_timeout"})
            raise RuntimeFault("tool_timeout") from exc
        except Exception as exc:
            self._observer("TOOL_FAILED", {"tool": name, "code": "tool_error"})
            raise RuntimeFault("tool_error") from exc
        self._observer("TOOL_COMPLETED", {"tool": name})
        return output
