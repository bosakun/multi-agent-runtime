"""Single-attempt diagnostic executor, tested offline; no research-run integration."""

import asyncio
import time
from pathlib import Path
from typing import Any

import httpx
from epistemic.models import FinalOutput, WorkerOutput
from pydantic import ValidationError

from app.core.errors import RuntimeFault
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelRequest
from operational_recovery.observer import AnswerRecorder, exclusive_json
from operational_recovery.workload import ROOT, request_digest


def reserve_directory(destination: Path) -> None:
    """Reserve a fresh directory without touching existing campaigns or seals."""
    resolved = destination.resolve()
    for name in ("runs", "freezes", "benchmarks", "diagnostics"):
        if resolved.is_relative_to((ROOT / name).resolve()):
            raise ValueError("Historical artifacts are protected")
    destination.mkdir(parents=True, exist_ok=False)


async def observe_once(
    request: ModelRequest,
    destination: Path,
    *,
    transport: httpx.MockTransport,
    timeout_seconds: float = 600,
) -> dict[str, Any]:
    """Use the unchanged adapter on an exact saved request, with a fake HTTP response.

    This entry point deliberately cannot generate with a real backend. A future
    real reproduction needs its own approved plan; an old campaign is never resumed.
    The added observation hook executes before the frozen provider raises on length.
    """
    if not isinstance(transport, httpx.MockTransport):
        raise ValueError("Only explicit fake HTTP transport is authorized here")
    if timeout_seconds <= 0:
        raise ValueError("Deadline must be positive")
    if request.tools or request.exchanges:
        raise ValueError("No tools or exchanges are supported by this diagnostic")
    reserve_directory(destination)
    exclusive_json(
        destination / "attempt.json",
        {
            "kind": "fake_http_only_not_real_model",
            "request_sha256": request_digest(request),
            "model": request.config.model,
            "generation_limit": request.config.max_output_tokens,
            "token_limit_parameter": "max_tokens",
            "temperature": request.config.temperature,
            "thinking": "model_default",
            "timeout_seconds": timeout_seconds,
            "reserved_attempts": 1,
        },
    )
    recorder = AnswerRecorder(destination / "response.json")
    result: dict[str, Any] = {
        "kind": "fake_http_only_not_real_model",
        "status": "failed",
        "error": None,
        "fake_attempts": 1,
        "real_model_calls": 0,
        "output": None,
        "observation": None,
    }
    started = time.perf_counter()
    try:
        async with (
            httpx.AsyncClient(
                base_url="http://fake.invalid/v1/",
                transport=transport,
                timeout=timeout_seconds,
                event_hooks={"response": [recorder]},
            ) as client,
            asyncio.timeout(timeout_seconds),
        ):
            provider = OpenAICompatibleProvider(client, "fake", token_limit_parameter="max_tokens")
            response = await provider.generate(request)
            schema = FinalOutput if request.agent_id == "synthesizer" else WorkerOutput
            schema.model_validate(response.output)
            result["status"] = "schema_valid"
            # Keep the guarded observer as the sole final-content persistence path.
    except RuntimeFault as exc:
        result["error"] = exc.code
    except ValidationError:
        result["error"] = "schema_invalid"
    except TimeoutError:
        result["error"] = "deadline_exceeded"
    except asyncio.CancelledError:
        result["error"] = "cancelled"
        raise
    except Exception as exc:
        result["error"] = type(exc).__name__
        raise
    finally:
        result["latency_ms"] = (time.perf_counter() - started) * 1000
        result["observation"] = recorder.observation
        exclusive_json(destination / "result.json", result)
    return result
