"""Read-only demo capability: inspect submitted code without executing it."""

import ast

from pydantic import BaseModel, Field

from app.core.models import Model
from app.tools.gateway import ToolDefinition, ToolRegistry


class ScanInput(Model):
    code: str = Field(max_length=50_000)


class ScanOutput(Model):
    syntax_valid: bool
    dynamic_calls: list[str]


async def scan_python(arguments: BaseModel) -> BaseModel:
    parsed = ScanInput.model_validate(arguments)
    try:
        tree = ast.parse(parsed.code)
    except SyntaxError:
        return ScanOutput(syntax_valid=False, dynamic_calls=[])
    calls = sorted(
        {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"eval", "exec", "compile"}
        }
    )
    return ScanOutput(syntax_valid=True, dynamic_calls=calls)


def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            "scan_python",
            "Statically inspect supplied Python text for dynamic execution calls.",
            ScanInput,
            ScanOutput,
            scan_python,
        )
    )
