"""Sealed six-call synthetic diagnostic. No benchmark evaluation, retries or model text logs."""

import asyncio
import hashlib
import json
import os
import platform
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from epistemic.freeze import verify as verify_research
from epistemic.models import FinalOutput, WorkerOutput
from epistemic.provider import CallBudget
from pydantic import ValidationError

from app.core.errors import RuntimeFault
from app.core.models import AgentContext, ModelConfig
from app.llm.openai_provider import OpenAICompatibleProvider
from app.llm.provider import ModelRequest
from operational_diagnostics.http_metadata import MetadataRecorder

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
PLAN_ROOT = ROOT / "diagnostics/token-budget-v1"


def read(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text())
    if not isinstance(result, dict):
        raise ValueError("Diagnostic artifact must be an object")
    return result


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def checkpoint(path: Path, value: object) -> None:
    """Replace only owned progress files inside a newly allocated campaign."""
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    exclusive(temporary, value)
    temporary.replace(path)


def sources() -> dict[str, str]:
    historical = verify_research()
    paths = {REPO / name for name in historical["files"]}
    paths.update((ROOT / "operational_diagnostics").glob("*.py"))
    paths.update([ROOT / "token_budget.py", PLAN_ROOT / "plan.json", PLAN_ROOT / "inputs.json"])
    paths.add(ROOT / "docs/token-budget-diagnostic-launch.md")
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def verify_seal(path: Path) -> dict[str, Any]:
    payload = read(path)
    if digest({k: v for k, v in payload.items() if k != "sha256"}) != payload["sha256"]:
        raise ValueError("Diagnostic seal hash mismatch")
    if payload["files"] != sources() or payload["plan"] != read(PLAN_ROOT / "plan.json"):
        raise ValueError("Diagnostic source/plan changed after seal")
    return payload


def prepare(seal_path: Path, campaign: Path) -> None:
    """Seal independently and bind a fresh campaign without contacting any model."""
    reject_historical_campaign(campaign)
    if campaign.exists() or seal_path.exists():
        raise ValueError("Existing seal/campaign is immutable; no overwrite or reuse")
    plan = read(PLAN_ROOT / "plan.json")
    payload = {"kind": "synthetic_operational_diagnostic", "plan": plan, "files": sources()}
    payload["sha256"] = digest(payload)
    exclusive(seal_path, payload)
    campaign.mkdir(parents=True, exist_ok=False)
    binding = {
        "kind": "synthetic_operational_diagnostic",
        "seal_sha256": payload["sha256"],
        "campaign_path": str(campaign.resolve()),
        "plan_id": plan["plan_id"],
        "model": plan["model"],
        "endpoint": plan["endpoint"],
        "temperature": plan["temperature"],
        "thinking": plan["thinking"],
        "timeout_seconds": plan["timeout_seconds"],
        "token_limit_parameter": plan["token_limit_parameter"],
        "generation_limits": plan["generation_limits"],
        "schedule": plan["schedule"],
        "ordering_seed": plan["ordering_seed"],
        "hard_call_limit": plan["hard_call_limit"],
        "planned_calls": plan["planned_calls"],
        "worker_concurrency": 1,
        "model_concurrency": 1,
        "authorization": "User approved implementation through real execution: 実モデル実行まで",
    }
    binding["sha256"] = digest(binding)
    exclusive(campaign / "binding.json", binding)


def reject_historical_campaign(campaign: Path) -> None:
    for name in ("qwen3-14b", "qwen3-14b-protocol22", "qwen3-14b-protocol23"):
        old = (ROOT / "runs" / name).resolve()
        if campaign.resolve() == old or campaign.resolve().is_relative_to(old):
            raise ValueError("Historical campaign and descendants are protected")


def verify_binding(seal_path: Path, campaign: Path) -> dict[str, Any]:
    reject_historical_campaign(campaign)
    seal = verify_seal(seal_path)
    binding = read(campaign / "binding.json")
    if digest({k: v for k, v in binding.items() if k != "sha256"}) != binding["sha256"]:
        raise ValueError("Diagnostic binding hash mismatch")
    plan = seal["plan"]
    if binding["seal_sha256"] != seal["sha256"] or binding["campaign_path"] != str(
        campaign.resolve()
    ):
        raise ValueError("Diagnostic binding/seal/campaign mismatch")
    for field in (
        "model",
        "endpoint",
        "temperature",
        "thinking",
        "timeout_seconds",
        "token_limit_parameter",
        "generation_limits",
        "schedule",
        "ordering_seed",
        "hard_call_limit",
        "planned_calls",
        "worker_concurrency",
        "model_concurrency",
    ):
        if binding[field] != plan[field]:
            raise ValueError("Diagnostic binding changed fixed controls")
    return binding


def request_for(cell: dict[str, Any], plan: dict[str, Any]) -> ModelRequest:
    fixtures = read(PLAN_ROOT / "inputs.json")["fixtures"]
    fixture = next(f for f in fixtures if f["id"] == cell["fixture_id"])
    context = AgentContext.model_validate(fixture["context"])
    if fixture["prompt_kind"] == "worker":
        instruction = (ROOT / "prompts/worker_v2.txt").read_text()
        instruction += "\n" + read(ROOT / "prompts/roles_v1.json")["neutral"]
        schema = WorkerOutput.model_json_schema()
    else:
        instruction = (ROOT / "prompts/synthesizer_v2.txt").read_text()
        schema = FinalOutput.model_json_schema()
    return ModelRequest(
        agent_id=context.agent_id,
        instruction=instruction,
        context=context,
        config=ModelConfig(
            provider="real",
            model=plan["model"],
            temperature=plan["temperature"],
            max_output_tokens=cell["max_output_tokens"],
        ),
        output_schema=schema,
    )


async def preflight(
    plan: dict[str, Any], transport: httpx.AsyncBaseTransport | None
) -> dict[str, Any]:
    """Read backend/model metadata only; no warm-up or generation probe."""
    async with httpx.AsyncClient(
        base_url=plan["endpoint"].removesuffix("v1/"),
        timeout=10,
        transport=transport,
        trust_env=False,
        follow_redirects=False,
    ) as client:
        version = await client.get("api/version")
        tags = await client.get("api/tags")
        details = await client.post("api/show", json={"model": plan["model"]})
        for response in (version, tags, details):
            response.raise_for_status()
        matching = [m for m in tags.json()["models"] if m["name"] == plan["model"]]
        if len(matching) != 1:
            raise ValueError("Bound model is not uniquely installed on the local backend")
        return {
            "backend_version": version.json().get("version"),
            "model": plan["model"],
            "model_digest": matching[0].get("digest"),
            "details": details.json().get("details", {}),
            "capabilities": details.json().get("capabilities", []),
            "hardware": {
                "architecture": platform.machine(),
                "os": platform.system(),
                "os_release": platform.release(),
                "logical_cpus": os.cpu_count(),
            },
        }


async def execute_cell(
    cell: dict[str, Any],
    plan: dict[str, Any],
    campaign: Path,
    api_key: str,
    budget: CallBudget,
    transport: httpx.AsyncBaseTransport | None,
    prior_request_hash: str | None = None,
) -> dict[str, Any]:
    request = request_for(cell, plan)
    directory = campaign / "metadata" / cell["cell_id"]
    wire: dict[str, Any] = {}

    async def audit_http(http_request: httpx.Request) -> None:
        body = json.loads(http_request.content)
        limits = {k: body[k] for k in ("max_tokens", "max_completion_tokens") if k in body}
        thinking = [k for k in ("think", "reasoning", "reasoning_effort") if k in body]
        if limits != {"max_tokens": cell["max_output_tokens"]} or thinking:
            raise ValueError("diagnostic_wire_boundary_violation")
        if body["model"] != plan["model"] or body["temperature"] != plan["temperature"]:
            raise ValueError("diagnostic_wire_boundary_violation")
        if body.get("tools") or "seed" in body:
            raise ValueError("diagnostic_wire_boundary_violation")
        canonical = {k: v for k, v in body.items() if k != "max_tokens"}
        wire.update(
            token_limit_fields=limits,
            thinking_fields=thinking,
            request_except_limit_sha256=digest(canonical),
        )
        if prior_request_hash and digest(canonical) != prior_request_hash:
            raise ValueError("diagnostic_paired_request_mismatch")
        checkpoint(journal, record)

    budget.reserve()
    record = {
        **cell,
        "attempts": 1,
        "status": "running",
        "error": None,
        "schema_valid": None,
        "metadata": None,
        "wire": wire,
    }
    journal = campaign / "call-journal" / f"{cell['cell_id']}.json"
    exclusive(journal, record)
    started = time.perf_counter()
    error: str | None = None
    try:
        async with asyncio.timeout(plan["timeout_seconds"]):
            async with httpx.AsyncClient(
                base_url=plan["endpoint"],
                timeout=plan["timeout_seconds"],
                transport=transport,
                trust_env=False,
                follow_redirects=False,
                event_hooks={"request": [audit_http], "response": [MetadataRecorder(directory)]},
            ) as client:
                result = await OpenAICompatibleProvider(
                    client, api_key, token_limit_parameter="max_tokens"
                ).generate(request)
            schema = FinalOutput if request.agent_id == "synthesizer" else WorkerOutput
            schema.model_validate(result.output)
            record.update(status="completed", schema_valid=True)
    except RuntimeFault as exc:
        error = (
            "diagnostic_timeout" if isinstance(exc.__cause__, httpx.TimeoutException) else exc.code
        )
    except (TimeoutError, httpx.TimeoutException):
        error = "diagnostic_timeout"
    except asyncio.CancelledError:
        error = "diagnostic_cancelled"
    except ValidationError:
        error = "diagnostic_schema_invalid"
    except Exception as exc:
        error = f"diagnostic_{type(exc).__name__}"
    record["latency_seconds"] = time.perf_counter() - started
    metadata_files = list(directory.glob("*.json"))
    try:
        observed = read(metadata_files[0]) if len(metadata_files) == 1 else None
    except Exception:
        observed = None
        error = "diagnostic_observer_persistence_failure"
    record["metadata"] = observed
    if error is None or error == "provider_output_truncated":
        if not observed or observed["input_tokens"] is None or observed["generated_tokens"] is None:
            error = "diagnostic_missing_required_metadata"
        elif observed["generated_tokens"] > cell["max_output_tokens"]:
            error = "diagnostic_backend_limit_violation"
        elif observed["finish_reason"] != ("length" if error else "stop"):
            error = "diagnostic_unexpected_finish_reason"
    record["error"] = error
    if error:
        record["status"] = "length_terminated" if error == "provider_output_truncated" else "failed"
    checkpoint(journal, record)
    return record


def fresh_binding(seal_path: Path, campaign: Path) -> dict[str, Any]:
    binding = verify_binding(seal_path, campaign)
    if any(p.is_file() and p.name != "binding.json" for p in campaign.rglob("*")):
        raise ValueError("Campaign already consumed; retries/resume/overwrites are forbidden")
    return binding


def git_metadata() -> dict[str, Any]:
    return {
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO)),
    }


async def run_campaign(
    seal_path: Path,
    campaign: Path,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> Path:
    binding = await asyncio.to_thread(fresh_binding, seal_path, campaign)
    plan = read(PLAN_ROOT / "plan.json")
    limit = min(int(os.environ.get("MAX_MODEL_CALLS", "6")), binding["hard_call_limit"])
    if limit < plan["planned_calls"]:
        raise ValueError("Remaining budget cannot fit all six planned calls")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY required; use the local ollama compatibility placeholder")
    for variable, expected in (("MODEL_NAME", plan["model"]), ("MODEL_BASE_URL", plan["endpoint"])):
        actual = os.environ.get(variable)
        if actual and actual.rstrip("/") != expected.rstrip("/"):
            raise ValueError("Environment differs from the bound model/endpoint")
    budget = CallBudget(campaign / "budget.sqlite", limit)
    report: dict[str, Any] = {
        "kind": "synthetic_operational_diagnostic; not C2/C3 research",
        "started_at": datetime.now(UTC).isoformat(),
        "binding_sha256": binding["sha256"],
        "seal_sha256": binding["seal_sha256"],
        "planned_calls": 6,
        **await asyncio.to_thread(git_metadata),
        "records": [{**cell, "status": "unexecuted"} for cell in plan["schedule"]],
        "stopped_reason": None,
        "budget_used_after": 0,
    }
    destination = campaign / "results.json"
    exclusive(destination, report)
    try:
        backend = await preflight(plan, transport)
        exclusive(campaign / "backend.json", backend)
    except Exception as exc:
        report["stopped_reason"] = f"diagnostic_preflight_{type(exc).__name__}"
        report["finished_at"] = datetime.now(UTC).isoformat()
        checkpoint(destination, report)
        return destination
    for index, cell in enumerate(plan["schedule"]):
        print(
            f"[START] {cell['cell_id']} {cell['fixture_id']} "
            f"max_tokens={cell['max_output_tokens']}",
            flush=True,
        )
        prior = next(
            (r for r in report["records"][:index] if r["fixture_id"] == cell["fixture_id"]), None
        )
        prior_hash = prior["wire"].get("request_except_limit_sha256") if prior else None
        record = await execute_cell(cell, plan, campaign, api_key, budget, transport, prior_hash)
        report["records"][index] = record
        report["budget_used_after"] = budget.used
        report["executed_calls"] = index + 1
        print(
            f"[DONE] {cell['cell_id']} {record['status']} {record['latency_seconds']:.2f}s",
            flush=True,
        )
        if record["status"] == "failed":
            report["stopped_reason"] = record["error"]
        checkpoint(destination, report)
        if report["stopped_reason"]:
            break
    report["finished_at"] = datetime.now(UTC).isoformat()
    checkpoint(destination, report)
    return destination
