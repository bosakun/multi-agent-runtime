"""Exclusive append-only checkpoints; same bounded native request and parsing controls."""

import hashlib
import uuid
from pathlib import Path
from typing import Any

import httpx
from bounded_pilot.contract import BoundedAuditedProvider, validate_citation_lengths
from epistemic.models import CallRecord
from native_pilot.provider import native_body, parse_native
from operational_diagnostics.budget_experiment import exclusive

from app.core.errors import RuntimeFault
from app.llm.provider import ModelRequest, ModelResponse


class AppendOnlyAuditedProvider(BoundedAuditedProvider):
    def __init__(self, *args: Any, history: Path, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.history = history

    def _checkpoint(self, record: CallRecord) -> None:
        exclusive(self.history / f"{uuid.uuid4().hex}.json", record.model_dump(mode="json"))

    def finalize(self) -> None:
        assert self.journal is not None
        for index, call in enumerate(self.calls, start=1):
            exclusive(
                self.journal / f"{index:04}_{call.run_id}_{call.agent_id}.json",
                call.model_dump(mode="json"),
            )


class ExclusiveNativeProvider:
    def __init__(self, client: httpx.AsyncClient, observations: Path) -> None:
        self.client, self.observations = client, observations

    async def generate(self, request: ModelRequest) -> ModelResponse:
        try:
            response = await self.client.post("/api/chat", json=native_body(request))
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeFault(f"provider_http_{exc.response.status_code}") from exc
        except httpx.TransportError as exc:
            raise RuntimeFault("provider_transport_error") from exc
        try:
            data = response.json()
            message = data.get("message", {})
            thinking, content = message.get("thinking") or "", message.get("content") or ""
            exclusive(
                self.observations / f"{request.context.run_id}_{request.agent_id}.json",
                {
                    "done": data.get("done"),
                    "finish_reason": data.get("done_reason"),
                    "input_tokens": data.get("prompt_eval_count"),
                    "generated_tokens": data.get("eval_count"),
                    "thinking_chars": len(thinking),
                    "final_content_chars": len(content),
                    "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "total_duration_ns": data.get("total_duration"),
                    "load_duration_ns": data.get("load_duration"),
                    "eval_duration_ns": data.get("eval_duration"),
                    "thinking_text_stored": False,
                },
            )
            result = parse_native(data)
            validate_citation_lengths(result.output, len(request.context.evidence_scope()))
            return result
        except (TypeError, ValueError, AttributeError) as exc:
            raise RuntimeFault("malformed_provider_response") from exc
