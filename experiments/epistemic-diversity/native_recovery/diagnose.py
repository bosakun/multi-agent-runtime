"""One separately sealed reproduction; retain visible JSON, never thinking text."""

import asyncio
import hashlib
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1]))
sys.path.insert(0, str(ROOT))

from epistemic.paths import digest  # noqa: E402
from operational_diagnostics.budget_experiment import exclusive  # noqa: E402
from operational_recovery.pilot24 import signed  # noqa: E402
from app.llm.provider import ModelRequest  # noqa: E402
from native_pilot.pilot26 import host_probe, verify_binding  # noqa: E402
from native_pilot.provider import NativeAuditedProvider, NativeProvider, native_body  # noqa: E402
from prospective_pilot.budget import ClosedCallBudget  # noqa: E402

OUTPUT = ROOT / "runs/qwen3-14b-protocol26-truncation-diagnostic"
INPUT = ROOT / (
    "runs/qwen3-14b-protocol26-windows/pilot/call-journal/"
    "0011_54ccbae7d1e54dd88ec643dab90909b7_worker_2.json"
)


async def main() -> None:
    if "--approve-real" not in sys.argv:
        raise ValueError("Explicit real generation approval required")
    if OUTPUT.exists():
        raise ValueError("One-call diagnostic consumed; no overwrite/retry")
    previous = verify_binding()
    host = await host_probe()
    if (
        host["ollama"]["version"] != previous["backend_version"]
        or host["ollama"]["digest"] != previous["model_digest"]
    ):
        raise ValueError("Backend/model drift")
    request = ModelRequest.model_validate(json.loads(INPUT.read_text(encoding="utf-8"))["request"])
    exclusive(OUTPUT / "binding.json", signed({
        "role": "engineering reproduction only, not research result",
        "hard_call_limit": 1,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "previous_binding_sha256": previous["sha256"],
        "wire_controls_sha256": digest(native_body(request)),
        "host": host,
        "capture": "visible message.content, never message.thinking",
    }))
    budget = ClosedCallBudget(OUTPUT / "budget.sqlite", 1)
    result = {"passed": False}

    async def capture(response: httpx.Response) -> None:
        await response.aread()
        if not response.is_success:
            return
        data = response.json()
        message = data.get("message", {})
        content = message.get("content") or ""
        exclusive(OUTPUT / "visible-output.json", {
            "finish_reason": data.get("done_reason"),
            "thinking_chars": len(message.get("thinking") or ""),
            "input_tokens": data.get("prompt_eval_count"),
            "generated_tokens": data.get("eval_count"),
            "content": content,
            "thinking_text_stored": False,
        })

    try:
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:11434/", timeout=1200,
            trust_env=False, follow_redirects=False,
        ) as client:
            provider = NativeAuditedProvider(
                NativeProvider(client, OUTPUT / "observations"),
                budget, OUTPUT / "call-journal", max_concurrency=1,
            )
            client.event_hooks["request"].append(provider.audit_http_request)
            client.event_hooks["response"].append(capture)
            await provider.generate(request)
            result["passed"] = True
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_code"] = getattr(exc, "code", None)
    finally:
        exclusive(OUTPUT / "result.json", signed({**result, "calls_used": budget.used}))
    print(json.dumps(result))


if __name__ == "__main__":
    asyncio.run(main())
