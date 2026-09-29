"""Prospective HTTP response observer: metadata only, never model text or reasoning."""

import json
import re
import uuid
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict


class ResponseMetadata(BaseModel):
    """Missing measurements remain null; this is not an agent result or quality score."""

    model_config = ConfigDict(extra="forbid")
    http_status: int
    parse_status: str
    finish_reason: str | None = None
    input_tokens: int | None = None
    generated_tokens: int | None = None
    total_tokens: int | None = None
    reasoning_tokens: int | None = None
    final_content_characters: int | None = None
    reasoning_characters: int | None = None
    final_content_json_object: bool | None = None
    run_id: str | None = None
    agent_id: str | None = None
    declared_generation_limit: int | None = None
    token_limit_parameter: str | None = None


def count(value: Any) -> int | None:
    """Do not invent zero, coerce strings, or accept booleans as token counts."""
    return value if type(value) is int and value >= 0 else None


def mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


async def response_metadata(response: httpx.Response) -> ResponseMetadata:
    """Observe before provider parsing rejects a truncated/refused/malformed response."""
    await response.aread()
    metadata = ResponseMetadata(http_status=response.status_code, parse_status="invalid_json")
    try:
        data = response.json()
    except (ValueError, UnicodeError):
        return metadata
    if not isinstance(data, dict):
        metadata.parse_status = "invalid_envelope"
        return metadata
    usage = mapping(data.get("usage"))
    metadata.input_tokens = count(usage.get("prompt_tokens"))
    metadata.generated_tokens = count(usage.get("completion_tokens"))
    metadata.total_tokens = count(usage.get("total_tokens"))
    details = mapping(usage.get("completion_tokens_details"))
    metadata.reasoning_tokens = count(details.get("reasoning_tokens"))
    choices = data.get("choices")
    choice = mapping(choices[0]) if isinstance(choices, list) and choices else {}
    metadata.parse_status = "envelope_observed" if choice else "missing_choice"
    reason = choice.get("finish_reason")
    if isinstance(reason, str):
        metadata.finish_reason = (
            reason if reason in {"stop", "length", "tool_calls", "content_filter"} else "other"
        )
    message = mapping(choice.get("message"))
    content = message.get("content")
    if isinstance(content, str):
        metadata.final_content_characters = len(content)
        try:
            metadata.final_content_json_object = isinstance(json.loads(content), dict)
        except (ValueError, RecursionError):
            metadata.final_content_json_object = False
    # Backends use different names; never double-count or persist either text field.
    reasoning = message.get("reasoning")
    if not isinstance(reasoning, str):
        reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str):
        metadata.reasoning_characters = len(reasoning)
    return metadata


class MetadataRecorder:
    """Opt-in response hook for a FUTURE reviewed protocol, not the current pilot.

    It does not change requests, accept truncation, retry, or return fallback outputs.
    Files are exclusive-create sidecars; errors propagate rather than silently losing audit data.
    """

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    async def __call__(self, response: httpx.Response) -> None:
        metadata = await response_metadata(response)
        try:
            request = mapping(json.loads(response.request.content))
            messages = request.get("messages")
            if isinstance(messages, list) and len(messages) > 1:
                context = mapping(json.loads(mapping(messages[1]).get("content", "{}")))
                run_id, agent_id = context.get("run_id"), context.get("agent_id")
                if isinstance(run_id, str) and re.fullmatch(r"[a-f0-9]{32}", run_id):
                    metadata.run_id = run_id
                if isinstance(agent_id, str) and re.fullmatch(r"worker_\d+|synthesizer", agent_id):
                    metadata.agent_id = agent_id
            limits = [k for k in ("max_tokens", "max_completion_tokens") if k in request]
            if len(limits) == 1:
                metadata.token_limit_parameter = limits[0]
                metadata.declared_generation_limit = count(request[limits[0]])
        except (ValueError, TypeError, UnicodeError):
            # Nonstandard request envelopes are unknown, not a reason to log raw bodies.
            pass
        self.directory.mkdir(parents=True, exist_ok=True)
        destination = self.directory / f"{uuid.uuid4().hex}.json"
        with destination.open("x", encoding="utf-8") as handle:
            handle.write(metadata.model_dump_json(indent=2) + "\n")
