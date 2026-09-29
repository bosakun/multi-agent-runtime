"""Extend the sealed non-generating metadata probe with identity and residency checks."""

import asyncio
import re
from typing import Any
from urllib.parse import urlsplit

import httpx
from operational_diagnostics.budget_experiment import preflight as existing_preflight

from host_support.commands import Commands
from host_support.models import Check, Ollama, Residency


def endpoint_root(endpoint: str) -> str:
    """Reject non-local destinations before constructing any HTTP client."""
    try:
        parsed = urlsplit(endpoint)
        valid = (
            parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1"}
            and parsed.port == 11434
            and parsed.path in {"", "/", "/v1", "/v1/"}
            and not (parsed.username or parsed.password or parsed.query or parsed.fragment)
        )
    except ValueError as exc:
        raise ValueError("Invalid local endpoint") from exc
    if not valid:
        raise ValueError(
            "Require http://localhost:11434 or http://127.0.0.1:11434 with optional /v1/"
        )
    return f"http://{parsed.hostname}:11434/"


def digest_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.removeprefix("sha256:")
    return normalized if re.fullmatch(r"[0-9a-f]{64}", normalized) else None


def integer(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


class MetadataTransport(httpx.AsyncBaseTransport):
    """Observe responses already fetched by the existing probe; no duplicate metadata queries."""

    def __init__(self, inner: httpx.AsyncBaseTransport) -> None:
        self.inner = inner
        self.data: dict[str, Any] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self.inner.handle_async_request(request)
        await response.aread()
        if response.is_success and request.url.path in {"/api/version", "/api/tags", "/api/show"}:
            try:
                self.data[request.url.path] = response.json()
            except ValueError:
                pass
        return response

    async def aclose(self) -> None:
        await self.inner.aclose()


def processor_observation(
    text: str | None, model: str
) -> tuple[str | None, int | None, int | None]:
    """Read CPU/GPU percentages ONLY when ollama ps explicitly reports them."""
    for line in (text or "").splitlines():
        parts = re.split(r"\s{2,}", line.strip())
        if not parts or parts[0] != model:
            continue
        for field in parts[1:]:
            match = re.fullmatch(r"(\d+)%/(\d+)% CPU/GPU", field)
            if match and int(match[1]) + int(match[2]) == 100:
                return field, int(match[2]), int(match[1])
            match = re.fullmatch(r"100% (GPU|CPU)", field)
            if match:
                return field, 100 if match[1] == "GPU" else 0, 100 if match[1] == "CPU" else 0
    return None, None, None


def residency(data: object, ps_text: str | None, model: str) -> Residency:
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        processor, gpu, cpu = processor_observation(ps_text, model)
        if gpu is not None:
            return Residency(
                state="full_gpu" if gpu == 100 else "cpu" if gpu == 0 else "partial_gpu",
                source="ollama ps; native residency API unavailable",
                processor=processor,
                gpu_percent=gpu,
                cpu_percent=cpu,
            )
        return Residency(state="unavailable", source="/api/ps unavailable")
    entries = [
        m for m in data["models"] if isinstance(m, dict) and m.get("name", m.get("model")) == model
    ]
    if not entries:
        return Residency(state="not_loaded", source="/api/ps")
    if len(entries) != 1:
        return Residency(state="unavailable", source="ambiguous /api/ps entries")
    entry = entries[0]
    size, vram = integer(entry.get("size")), integer(entry.get("size_vram"))
    fraction = vram / size if size and vram is not None and vram <= size else None
    processor, gpu, cpu = processor_observation(ps_text, model)
    state = "loaded_unknown"
    if gpu is not None:
        state = "full_gpu" if gpu == 100 else "cpu" if gpu == 0 else "partial_gpu"
    elif fraction is not None:
        state = "full_gpu" if fraction == 1 else "cpu" if fraction == 0 else "partial_gpu"
    return Residency.model_validate(
        {
            "state": state,
            "source": "/api/ps + ollama ps" if processor else "/api/ps memory ratio",
            "processor": processor,
            "gpu_percent": gpu,
            "cpu_percent": cpu,
            "size_bytes": size,
            "size_vram_bytes": vram,
            "gpu_memory_fraction": fraction,
            "context_length": integer(entry.get("context_length")),
            "digest": digest_value(entry.get("digest")),
        }
    )


async def inspect_ollama(
    commands: Commands,
    endpoint: str,
    model: str,
    expected_digest: str | None = None,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[Ollama, list[Check]]:
    info = Ollama(model=model)
    checks = [
        Check(
            name="ollama_cli",
            status="pass" if commands.which("ollama") else "fail",
            detail="Ollama CLI availability",
        )
    ]
    try:
        root = endpoint_root(endpoint)
    except ValueError as exc:
        checks.append(Check(name="endpoint", status="fail", detail=str(exc)))
        return info, checks
    info.endpoint = root.rstrip("/")
    checks.append(Check(name="endpoint", status="pass", detail=root + "v1/"))
    if model != "qwen3:14b" or (
        expected_digest is not None and digest_value(expected_digest) is None
    ):
        checks.append(
            Check(
                name="model_identity",
                status="fail",
                detail="Require qwen3:14b and a valid optional full digest",
            )
        )
        return info, checks
    observed = MetadataTransport(transport or httpx.AsyncHTTPTransport(trust_env=False))
    try:
        # Reuse the original metadata/hardware capture rather than fork or edit sealed code.
        base = await existing_preflight({"endpoint": root + "v1/", "model": model}, observed)
        version = base.get("backend_version")
        info.version = version if isinstance(version, str) and version else None
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        checks.append(
            Check(
                name="ollama_native_api",
                status="fail",
                detail="Native metadata API unavailable, malformed, or target model absent",
            )
        )
    else:
        checks.append(
            Check(
                name="ollama_native_api", status="pass", detail="Existing metadata probe succeeded"
            )
        )
    tags = observed.data.get("/api/tags", {})
    models = tags.get("models", []) if isinstance(tags, dict) else []
    models = models if isinstance(models, list) else []
    matching = [m for m in models if isinstance(m, dict) and m.get("name") == model]
    if len(matching) == 1:
        entry = matching[0]
        info.digest = digest_value(entry.get("digest"))
        info.model_size_bytes = integer(entry.get("size"))
        alias_ok = entry.get("model", model) == model
    else:
        alias_ok = False
    identity_ok = bool(
        alias_ok
        and info.digest
        and (expected_digest is None or info.digest == digest_value(expected_digest))
    )
    checks.append(
        Check(
            name="model_identity",
            status="pass" if identity_ok else "fail",
            detail="Exact name/full digest checked; expected digest compared when supplied",
        )
    )
    show = observed.data.get("/api/show", {})
    if isinstance(show, dict):
        details = show.get("details", {})
        quantization = details.get("quantization_level") if isinstance(details, dict) else None
        info.quantization = quantization if isinstance(quantization, str) else None
        model_info = show.get("model_info", {})
        if isinstance(model_info, dict):
            info.model_context_lengths = {
                k: v
                for k, v in model_info.items()
                if k.endswith(".context_length") and type(v) is int and v > 0
            }
    checks.append(
        Check(
            name="ollama_version",
            status="pass" if info.version else "fail",
            detail="Server version availability",
        )
    )
    async with httpx.AsyncClient(
        base_url=root, timeout=10, transport=transport, trust_env=False, follow_redirects=False
    ) as client:
        try:
            response = await client.get("v1/models")
            response.raise_for_status()
            values = response.json()["data"]
            compatible = isinstance(values, list) and any(
                isinstance(m, dict) and m.get("id") == model for m in values
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            compatible = False
        checks.append(
            Check(
                name="openai_models_api",
                status="pass" if compatible else "fail",
                detail="GET /v1/models must expose the exact target ID",
            )
        )
        try:
            response = await client.get("api/ps")
            response.raise_for_status()
            ps_data = response.json()
        except (httpx.HTTPError, ValueError):
            ps_data = None
    ps = await asyncio.to_thread(
        commands.run, ["ollama", "ps"], env={"OLLAMA_HOST": root.rstrip("/")}
    )
    info.residency = residency(ps_data, ps.output, model)
    checks.append(
        Check(
            name="gpu_residency",
            status="pass" if info.residency.state == "full_gpu" else "warning",
            detail=f"Observed {info.residency.state}; API byte ratio is not compute utilization",
        )
    )
    if info.residency.digest and info.digest and info.residency.digest != info.digest:
        checks.append(
            Check(
                name="resident_identity",
                status="fail",
                detail="Loaded model digest differs from installed model",
            )
        )
    return info, checks
