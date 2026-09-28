"""Immutable content seal and model binding, verified before any paid dispatch."""

from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from epistemic.benchmark_audit import quality_audit
from epistemic.benchmark_v2 import PILOT_IDS, SEED, VERSION
from epistemic.models import ModelSettings
from epistemic.paths import REPO, ROOT, digest, read_json, write_json

FREEZE_PATH = ROOT / "freezes/benchmark-2.0.0-protocol-2.2.json"
CONTROL_DOCUMENTS = [
    "v2-design-amendment.md",
    "experiment-freeze.md",
    "real-pilot-plan.md",
    "benchmark-taxonomy.md",
    "benchmark-audit.md",
    "metric-audit.md",
    "research-plan.md",
    "methodology.md",
    "limitations.md",
    "protocol-2.1-amendment.md",
    "protocol-2.2-amendment.md",
    "qwen3-14b-operational-failure.md",
]


def frozen_files() -> dict[str, str]:
    paths = [
        p
        for directory, pattern in [
            (ROOT / "src", "*.py"),
            (REPO / "app", "*.py"),
            (ROOT / "prompts", "*"),
            (ROOT / "configs", "*.json"),
            (ROOT / "benchmarks/v2", "*.json"),
        ]
        for p in directory.rglob(pattern)
        if p.is_file()
    ]
    paths.extend(ROOT / "docs" / name for name in CONTROL_DOCUMENTS)
    paths.extend([ROOT / "run.py", REPO / "uv.lock", REPO / "pyproject.toml"])
    return {str(p.relative_to(REPO)): digest(p.read_text()) for p in sorted(paths)}


def seal(path: Path = FREEZE_PATH) -> dict[str, Any]:
    if path.exists():
        raise ValueError(
            "Freeze already exists; use a new declared protocol/version, not overwrite"
        )
    report = quality_audit()
    if not report["passed"]:
        raise ValueError("Benchmark audit failed")
    payload = {
        "benchmark_version": VERSION,
        "protocol_version": "pilot-2.2",
        "execution_profiles": {
            "standard": {"worker_concurrency": 3, "timeout_seconds": 90},
            "local_ollama": {
                "worker_concurrency": 1,
                "model_concurrency": 1,
                "timeout_seconds": 300,
            },
        },
        "metrics_version": "2.0.0",
        "task_ids": PILOT_IDS,
        "conditions": ["C2", "C3"],
        "seed": SEED,
        "repetitions": 1,
        "planned_calls": 48,
        "default_budget": 60,
        "model_binding": "Required separately before first paid call; no model silently selected",
        "files": frozen_files(),
    }
    payload["freeze_sha256"] = digest(payload)
    write_json(path, payload)
    return payload


def verify(path: Path = FREEZE_PATH) -> dict[str, Any]:
    payload: dict[str, Any] = read_json(path)
    content = {k: v for k, v in payload.items() if k != "freeze_sha256"}
    if digest(content) != payload["freeze_sha256"] or frozen_files() != payload["files"]:
        raise ValueError(
            "Frozen content changed; do not run until a declared new freeze is reviewed"
        )
    if (
        payload["benchmark_version"] != VERSION
        or payload.get("protocol_version") != "pilot-2.2"
        or payload["task_ids"] != PILOT_IDS
        or payload["conditions"] != ["C2", "C3"]
    ):
        raise ValueError("Unexpected frozen pilot protocol")
    return payload


def validate_endpoint(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.hostname:
        raise ValueError("Endpoint must not contain credentials, query parameters or fragments")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    ):
        raise ValueError("Use HTTPS except for an explicit local provider")
    return endpoint.rstrip("/") + "/"


def bind_model(
    path: Path,
    model: str,
    endpoint: str,
    freeze_path: Path = FREEZE_PATH,
    *,
    execution_profile: str = "standard",
    campaign: Path | None = None,
) -> dict[str, Any]:
    frozen = verify(freeze_path)
    if path.exists():
        raise ValueError("Model binding already exists; do not overwrite")
    if not model.strip() or "mock" in model.lower():
        raise ValueError("Specify a real model ID; no default paid model is selected")
    settings = ModelSettings.model_validate(
        {
            "provider": "real",
            "model": model,
            "execution_profile": execution_profile,
            "timeout_seconds": 300 if execution_profile == "local_ollama" else 90,
        }
    )
    validate_execution_endpoint(settings, endpoint)
    if settings.execution_profile == "local_ollama":
        if campaign is None or campaign.exists():
            raise ValueError("Local Ollama binding requires a new, nonexistent --campaign path")
        if path.resolve().parent != campaign.resolve():
            raise ValueError("Local binding must be written at its new campaign root")
    payload = {
        "benchmark_version": VERSION,
        "protocol_version": "pilot-2.2",
        "campaign_path": str(campaign.resolve()) if campaign is not None else None,
        "freeze_sha256": frozen["freeze_sha256"],
        "settings": settings.model_dump(),
        "endpoint": validate_endpoint(endpoint),
        "seed": SEED,
        "task_ids": PILOT_IDS,
        "conditions": ["C2", "C3"],
        "repetitions": 1,
        "planned_calls": 48,
    }
    payload["binding_sha256"] = digest(payload)
    write_json(path, payload)
    return payload


def validate_execution_endpoint(settings: ModelSettings, endpoint: str) -> None:
    """Keep local resource accommodations specific to the loopback Ollama endpoint."""
    parsed = urlsplit(validate_endpoint(endpoint))
    local = parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port == 11434
    if settings.execution_profile == "local_ollama":
        if not local or parsed.path.rstrip("/") != "/v1":
            raise ValueError("Local Ollama profile requires loopback port 11434 /v1 endpoint")
    elif local:
        raise ValueError("Local Ollama endpoint requires the local_ollama execution profile")


def validate_local_campaign(binding: dict[str, Any], campaign: Path, path: Path) -> None:
    """Refuse reuse before creating any budget, phase, or result artifact."""
    root = campaign.resolve()
    binding_file = path.resolve()
    if binding.get("campaign_path") != str(root):
        raise ValueError("Local Ollama requires the new campaign named in its binding")
    if binding_file.parent != root:
        raise ValueError("Local binding must be at the new campaign root")
    if any(p.is_file() and p.resolve() != binding_file for p in root.rglob("*")):
        raise ValueError("Local campaign already contains artifacts; choose a new campaign")


def validate_binding(
    path: Path, settings: ModelSettings, endpoint: str, seed: int, freeze_path: Path = FREEZE_PATH
) -> dict[str, Any]:
    frozen = verify(freeze_path)
    validate_execution_endpoint(settings, endpoint)
    binding: dict[str, Any] = read_json(path)
    content = {k: v for k, v in binding.items() if k != "binding_sha256"}
    if (
        digest(content) != binding["binding_sha256"]
        or binding["freeze_sha256"] != frozen["freeze_sha256"]
    ):
        raise ValueError("Model binding does not match verified freeze")
    if (
        binding["settings"] != settings.model_dump()
        or binding["endpoint"] != validate_endpoint(endpoint)
        or binding["seed"] != seed
    ):
        raise ValueError("Generation settings/endpoint/seed differ from the pre-run binding")
    if (
        binding["task_ids"] != PILOT_IDS
        or binding.get("protocol_version") != "pilot-2.2"
        or binding["conditions"] != ["C2", "C3"]
        or binding["repetitions"] != 1
    ):
        raise ValueError("Binding changed the frozen pilot selection")
    return binding
