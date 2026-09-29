"""Project only AgentContext evidence IDs into every citation-array schema."""

import json
from copy import deepcopy
from typing import Any, cast

import httpx
from epistemic.provider import AuditedProvider
from pydantic import JsonValue

from app.core.models import AgentContext
from app.llm.openai_provider import strict_schema
from app.llm.provider import ModelRequest, ModelResponse


def scoped_schema(schema: dict[str, JsonValue], context: AgentContext) -> dict[str, JsonValue]:
    result = deepcopy(schema)
    allowed = sorted(context.evidence_scope())
    fields = 0

    def visit(value: Any) -> None:
        nonlocal fields
        if isinstance(value, dict):
            properties = value.get("properties", {})
            if isinstance(properties, dict) and "evidence_ids" in properties:
                citation = properties["evidence_ids"]
                if not isinstance(citation, dict) or citation.get("type") != "array":
                    raise ValueError("Evidence citations must be an array")
                if citation.get("items", {}).get("type") != "string":
                    raise ValueError("Evidence citations must contain string IDs")
                citation["items"] = {"type": "string", **({"enum": allowed} if allowed else {})}
                if not allowed:
                    citation["maxItems"] = 0
                fields += 1
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    if not fields:
        raise ValueError("Output schema contains no evidence citation fields")
    return result


class ScopedAuditedProvider(AuditedProvider):
    """Journal and transmit the effective schema; retain original runtime rejection."""

    async def _generate(self, request: ModelRequest) -> ModelResponse:
        effective = request.model_copy(deep=True)
        effective.output_schema = scoped_schema(request.output_schema, request.context)
        return await super()._generate(effective)

    async def audit_http_request(self, request: httpx.Request) -> None:
        await super().audit_http_request(request)
        body = json.loads(request.content)
        context = AgentContext.model_validate(json.loads(body["messages"][1]["content"]))
        records = [
            call
            for call in self.calls
            if call.run_id == context.run_id and call.agent_id == context.agent_id
        ]
        if len(records) != 1:
            raise ValueError("No unique citation-contract journal")
        record = records[0]
        schema = cast(dict[str, JsonValue], record.request["output_schema"])
        if schema != scoped_schema(schema, context):
            raise ValueError("Journaled citation contract differs from context scope")
        if body["response_format"]["json_schema"]["schema"] != strict_schema(schema):
            raise ValueError("Serialized citation contract differs from journal")
        if record.backend_request is None:
            raise ValueError("Missing wire audit")
        record.backend_request["allowed_evidence_ids"] = sorted(context.evidence_scope())
        record.backend_request["citation_contract"] = "agent_context_enum_v1"
        self._checkpoint(record)
