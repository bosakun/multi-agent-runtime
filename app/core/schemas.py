"""Trusted application schema registration."""

from pydantic import BaseModel

from app.core.errors import RuntimeFault


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[str, type[BaseModel]] = {}

    def register(self, name: str, schema: type[BaseModel]) -> None:
        if name in self._schemas:
            raise ValueError(f"Duplicate schema: {name}")
        self._schemas[name] = schema

    def get(self, name: str) -> type[BaseModel]:
        try:
            return self._schemas[name]
        except KeyError as exc:
            raise RuntimeFault("unknown_schema") from exc
