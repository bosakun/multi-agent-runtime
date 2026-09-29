"""Retain explicit answer JSON before rejection, without logging hidden reasoning."""

import json
import re
from pathlib import Path
from typing import Any

import httpx
from operational_diagnostics.http_metadata import mapping, response_metadata

ANSWER_KEYS = {"claims", "insights", "uncertainty", "conclusion", "decision_summary"}


def answer_prefix(content: str) -> tuple[str | None, str]:
    """Fail closed for prose, inline thinking, and unexpected top-level fields.

    Only a schema-shaped final-answer prefix is retained. A partial JSON value
    is evidence, not a repaired answer. Separated reasoning fields are never read
    here. This is restricted to the project's synthetic, non-PII diagnostics.
    """
    if len(content) > 131072:
        return None, "oversized_content_withheld"
    # Include escaped markers/keys, since output may be a partially encoded JSON string.
    normalized = re.sub(r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match[1], 16)), content)
    if re.search(r"think|reasoning|analysis|scratchpad", normalized, re.IGNORECASE):
        return None, "possible_reasoning_withheld"
    text = content.strip()
    if not text.startswith("{"):
        return None, "non_json_content_withheld"
    decoder = json.JSONDecoder()
    offset = 1
    seen: set[str] = set()
    while True:
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset == len(text):
            return (content, "partial_answer") if seen else (None, "no_answer_field")
        if text[offset] == "}":
            if text[offset + 1 :].strip():
                return None, "trailing_content_withheld"
            return content, "complete_json_candidate"
        try:
            key, offset = decoder.raw_decode(text, offset)
        except ValueError:
            # Incomplete keys could be an unexpected reasoning field: do not retain them.
            return None, "unrecognized_field_withheld"
        if not isinstance(key, str) or key not in ANSWER_KEYS or key in seen:
            return None, "unrecognized_field_withheld"
        seen.add(key)
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset == len(text):
            return content, "partial_answer"
        if text[offset] != ":":
            return None, "malformed_field_withheld"
        offset += 1
        while offset < len(text) and text[offset].isspace():
            offset += 1
        try:
            _, offset = decoder.raw_decode(text, offset)
        except ValueError:
            return content, "partial_answer"
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset < len(text) and text[offset] == ",":
            offset += 1
        elif offset < len(text) and text[offset] != "}":
            return None, "malformed_field_withheld"


def exclusive_json(path: Path, value: object) -> None:
    """Exclusive creation avoids replacing any prior diagnostic evidence."""
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


class AnswerRecorder:
    """One-call HTTP hook. No headers, request text, error bodies or reasoning text."""

    def __init__(self, destination: Path) -> None:
        self.destination = destination
        self.observation: dict[str, Any] | None = None

    async def __call__(self, response: httpx.Response) -> None:
        metadata = await response_metadata(response)
        value = metadata.model_dump()
        value.update(final_answer_prefix=None, answer_capture="no_content")
        if response.is_success:
            try:
                data = mapping(response.json())
            except (ValueError, UnicodeError):
                data = {}
            choices = data.get("choices")
            choice = mapping(choices[0]) if isinstance(choices, list) and choices else {}
            message = mapping(choice.get("message"))
            content = message.get("content")
            if message.get("refusal"):
                value["answer_capture"] = "refusal_withheld"
            elif isinstance(content, str) and content:
                prefix, capture = answer_prefix(content)
                value.update(final_answer_prefix=prefix, answer_capture=capture)
        else:
            value["answer_capture"] = "http_error_body_withheld"
        # Never infer a reasoning token count from characters or subtract unlike units.
        value["interpretation"] = (
            "length_termination; not a timeout; allocation cause unknown"
            if metadata.finish_reason == "length"
            else "response_observed; not proof of schema or task success"
        )
        exclusive_json(self.destination, value)
        self.observation = value
