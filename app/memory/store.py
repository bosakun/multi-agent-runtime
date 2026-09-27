"""Memory namespaces are selected by trusted runtime code, never by model output."""

from typing import Literal, Protocol

from pydantic import JsonValue

MemoryScope = Literal["private", "shared", "long_term"]


class MemoryStore(Protocol):
    async def read(
        self, scope: MemoryScope, namespace: str, keys: list[str]
    ) -> dict[str, JsonValue]: ...

    async def write(
        self, scope: MemoryScope, namespace: str, key: str, value: JsonValue
    ) -> None: ...


def agent_namespace(run_id: str, agent_id: str) -> str:
    return f"{run_id}:{agent_id}"
