"""Prevent endless citation-array expansion without introducing gold-derived limits."""

from typing import Any

import httpx
from native_pilot.provider import NativeAuditedProvider, NativeProvider
from prospective_pilot.contract import scoped_schema
from pydantic import JsonValue

from app.core.errors import RuntimeFault
from app.core.models import AgentContext
from app.llm.provider import ModelRequest, ModelResponse


def bounded_schema(schema: dict[str, JsonValue], context: AgentContext) -> dict[str, JsonValue]:
    result = scoped_schema(schema, context)
    limit = len(context.evidence_scope())

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            properties = value.get("properties", {})
            if isinstance(properties, dict) and "evidence_ids" in properties:
                properties["evidence_ids"]["maxItems"] = limit
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return result


def validate_citation_lengths(value: Any, limit: int) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_ids" and isinstance(child, list) and len(child) > limit:
                raise RuntimeFault("citation_array_limit_exceeded")
            validate_citation_lengths(child, limit)
    elif isinstance(value, list):
        for child in value:
            validate_citation_lengths(child, limit)


class BoundedProvider(NativeProvider):
    async def generate(self, request: ModelRequest) -> ModelResponse:
        response = await super().generate(request)
        validate_citation_lengths(response.output, len(request.context.evidence_scope()))
        return response


class BoundedAuditedProvider(NativeAuditedProvider):
    async def _generate(self, request: ModelRequest) -> ModelResponse:
        effective = request.model_copy(deep=True)
        effective.output_schema = bounded_schema(request.output_schema, request.context)
        return await super()._generate(effective)

    async def audit_http_request(self, request: httpx.Request) -> None:
        # Verify cardinality in addition to inherited exact native wire/scope audit.
        import json

        body = json.loads(request.content)
        context = AgentContext.model_validate_json(body["messages"][1]["content"])
        records = [
            r for r in self.calls if r.run_id == context.run_id and r.agent_id == context.agent_id
        ]
        if len(records) != 1:
            raise ValueError("No unique bounded-citation journal")
        effective = ModelRequest.model_validate(records[0].request)
        if effective.output_schema != bounded_schema(effective.output_schema, context):
            raise ValueError("Citation cardinality differs from authorized context")
        await super().audit_http_request(request)
        record = records[0]
        assert record.backend_request is not None
        record.backend_request["citation_contract"] = "agent_context_enum_bounded_v2"
        record.backend_request["citation_max_items"] = len(context.evidence_scope())
        self._checkpoint(record)
