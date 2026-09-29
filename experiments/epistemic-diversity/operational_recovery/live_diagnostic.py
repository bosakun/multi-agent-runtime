"""Authorized bounded engineering reproduction, separate from scientific results."""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
from epistemic.freeze import verify
from epistemic.models import FinalOutput, WorkerOutput
from epistemic.provider import CallBudget
from operational_diagnostics.budget_experiment import checkpoint, exclusive, preflight
from pydantic import ValidationError

from app.core.errors import RuntimeFault
from app.llm.openai_provider import OpenAICompatibleProvider
from operational_recovery.observer import AnswerRecorder
from operational_recovery.workload import FAILED_JOURNAL, ROOT, load_saved_request, request_digest

CAMPAIGN = ROOT / "runs/qwen3-14b-recovery-v2"
PLAN = ROOT / "docs/recovery-v2-plan.md"
ENDPOINT = "http://127.0.0.1:11434/v1/"
SYNTHESIZER = ROOT / (
    "runs/qwen3-14b-protocol23/pilot/call-journal/"
    "0008_1252c8300fbe433988b56515964140de_synthesizer.json"
)
SCHEDULE = [(FAILED_JOURNAL, 2048), (FAILED_JOURNAL, 4096), (SYNTHESIZER, 4096)]


def files() -> dict[str, str]:
    """An explicit file list lets a subsequent pilot have a separate immutable seal."""
    base = verify()
    paths = [ROOT.parents[1] / name for name in base["files"]]
    paths += [
        Path(__file__),
        ROOT / "recovery_live.py",
        ROOT / "operational_recovery/observer.py",
        ROOT / "operational_recovery/workload.py",
        *list((ROOT / "operational_diagnostics").glob("*.py")),
        PLAN,
        FAILED_JOURNAL,
        SYNTHESIZER,
    ]
    return {
        str(p.relative_to(ROOT.parents[1])): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(set(paths))
    }


def prepare() -> None:
    if CAMPAIGN.exists():
        raise ValueError("Existing recovery campaign is immutable")
    payload = {
        "kind": "engineering_reproduction_not_research",
        "files": files(),
        "schedule": [
            {"journal": str(p.relative_to(ROOT)), "limit": limit} for p, limit in SCHEDULE
        ],
        "endpoint": ENDPOINT,
        "model": "qwen3:14b",
        "timeout_seconds": 1200,
        "temperature": 0,
        "thinking": "model_default",
        "hard_call_limit": 60,
        "planned_diagnostic_calls": 3,
        "planned_pilot_calls": 48,
        "authorization": "User: 最中にある問題点は改善していって、pilot完走までいきましょう。",
    }
    payload["sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    exclusive(CAMPAIGN / "binding.json", payload)


def verify_binding() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads((CAMPAIGN / "binding.json").read_text())
    body = {k: v for k, v in payload.items() if k != "sha256"}
    if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != payload["sha256"]:
        raise ValueError("Recovery binding hash mismatch")
    if payload["files"] != files():
        raise ValueError("Recovery diagnostic sources changed")
    return payload


async def run(*, transport: httpx.AsyncBaseTransport | None = None) -> Path:
    binding = verify_binding()
    output = CAMPAIGN / "diagnostic"
    if output.exists():
        raise ValueError("Diagnostic already consumed; no replay/resume")
    limit = min(60, int(os.environ.get("MAX_MODEL_CALLS", "60")))
    if limit < 51:
        raise ValueError("Reserve the full 3-call diagnostic plus 48-call pilot budget")
    budget = CallBudget(CAMPAIGN / "budget.sqlite", limit)
    if budget.used:
        raise ValueError("Budget already consumed")
    backend = await preflight(binding, transport)
    exclusive(output / "backend.json", backend)
    records: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "kind": binding["kind"],
        "binding_sha256": binding["sha256"],
        "records": records,
        "budget_used_after": 0,
        "stopped_reason": None,
        "pilot_gate": False,
    }
    checkpoint(output / "results.json", result)
    paired_hash: str | None = None
    for index, (journal, cap) in enumerate(SCHEDULE, 1):
        request = load_saved_request(journal)
        request.config.max_output_tokens = cap
        directory = output / f"cell-{index:02}"
        record: dict[str, Any] = {
            "cell": index,
            "source": str(journal.relative_to(ROOT)),
            "request_sha256": request_digest(request),
            "max_tokens": cap,
            "status": "running",
            "error": None,
            "observation": None,
        }
        exclusive(directory / "attempt.json", record)
        recorder = AnswerRecorder(directory / "response.json")

        async def wire_audit(
            http_request: httpx.Request,
            *,
            cap: int = cap,
            index: int = index,
            record: dict[str, Any] = record,
            directory: Path = directory,
        ) -> None:
            nonlocal paired_hash
            body = json.loads(http_request.content)
            if (
                body["max_tokens"] != cap
                or body["model"] != "qwen3:14b"
                or body["temperature"] != 0
                or {"think", "thinking", "reasoning_effort", "tools", "max_completion_tokens"}
                & body.keys()
            ):
                raise ValueError("Wire controls differ from plan")
            canonical = {k: v for k, v in body.items() if k != "max_tokens"}
            digest = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
            if index == 2 and digest != paired_hash:
                raise ValueError("Diagnostic pair changed input")
            if index == 1:
                paired_hash = digest
            record["wire_except_limit_sha256"] = digest
            exclusive(directory / "wire.json", {"max_tokens": cap, "sha256": digest})

        budget.reserve()
        started = time.perf_counter()
        print(
            json.dumps({"event": "DIAGNOSTIC_START", "cell": index, "max_tokens": cap}), flush=True
        )
        try:
            async with (
                httpx.AsyncClient(
                    base_url=ENDPOINT,
                    timeout=1200,
                    transport=transport,
                    trust_env=False,
                    follow_redirects=False,
                    event_hooks={"request": [wire_audit], "response": [recorder]},
                ) as client,
                asyncio.timeout(1200),
            ):
                response = await OpenAICompatibleProvider(
                    client, "ollama", token_limit_parameter="max_tokens"
                ).generate(request)
                schema = FinalOutput if request.agent_id == "synthesizer" else WorkerOutput
                schema.model_validate(response.output)
                record["status"] = "schema_valid"
        except RuntimeFault as exc:
            record.update(status="failed", error=exc.code)
        except ValidationError:
            record.update(status="failed", error="schema_invalid")
        except TimeoutError:
            record.update(status="failed", error="deadline_exceeded")
        except BaseException as exc:
            record.update(status="failed", error=type(exc).__name__)
            result["stopped_reason"] = type(exc).__name__
            raise
        finally:
            record["latency_seconds"] = time.perf_counter() - started
            record["observation"] = recorder.observation
            observed = recorder.observation
            if not record["error"] and (
                not observed
                or observed["finish_reason"] != "stop"
                or observed["generated_tokens"] is None
                or observed["generated_tokens"] > cap
            ):
                record.update(status="failed", error="invalid_usage_or_finish_reason")
            records.append(record)
            result["budget_used_after"] = budget.used
            checkpoint(directory / "result.json", record)
            checkpoint(output / "results.json", result)
            print(
                json.dumps(
                    {
                        "event": "DIAGNOSTIC_DONE",
                        "cell": index,
                        "status": record["status"],
                        "error": record["error"],
                        "latency_seconds": record["latency_seconds"],
                    }
                ),
                flush=True,
            )
        # Only baseline length termination is a planned diagnostic observation.
        if record["error"] and not (index == 1 and record["error"] == "provider_output_truncated"):
            result["stopped_reason"] = record["error"]
            break
    result["pilot_gate"] = len(records) == 3 and all(
        r["status"] == "schema_valid" for r in records[1:]
    )
    checkpoint(output / "results.json", result)
    return output / "results.json"
