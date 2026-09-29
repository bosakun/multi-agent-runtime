"""Offline workload comparison based on saved agent inputs, never hidden gold."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.llm.provider import ModelRequest

ROOT = Path(__file__).resolve().parents[1]
FAILED_JOURNAL = ROOT / (
    "runs/qwen3-14b-protocol23/pilot/call-journal/"
    "0017_e14b05fe11754953a75d6010dc002060_worker_0.json"
)
REFERENCE_REQUEST = ROOT / "operational_recovery/fixtures/failed-worker.json"


def request_digest(request: ModelRequest) -> str:
    """Bind the entire input, instruction, schema and model configuration, not its size."""
    return hashlib.sha256(request.model_dump_json().encode()).hexdigest()


def load_saved_request(path: Path) -> ModelRequest:
    """Read the dispatched agent-only context; never reconstruct it from global state."""
    data = json.loads(path.read_text())
    return ModelRequest.model_validate(data["request"])


def complexity(context: dict[str, Any]) -> dict[str, int]:
    """Structural descriptors, not a tokenizer or predictor of required model tokens."""
    inputs = context["inputs"]
    rules = inputs.get("inference_rules", []) + inputs.get("decision_rules", [])
    return {
        "context_characters": len(json.dumps(context, separators=(",", ":"), ensure_ascii=False)),
        "knowledge_items": len(context["knowledge"]),
        "artifacts": len(context["artifacts"]),
        "reporting_fields": len(inputs.get("reporting_fields", [])),
        "inference_rules": len(inputs.get("inference_rules", [])),
        "decision_rules": len(inputs.get("decision_rules", [])),
        "premise_occurrences": sum(len(rule["premises"]) for rule in rules),
    }


def audit() -> dict[str, Any]:
    """Make the previous diagnostic's coverage gap mechanically inspectable."""
    source = FAILED_JOURNAL if FAILED_JOURNAL.exists() else REFERENCE_REQUEST
    request = load_saved_request(source)
    fixtures = json.loads((ROOT / "diagnostics/token-budget-v1/inputs.json").read_text())[
        "fixtures"
    ]
    failed = complexity(request.context.model_dump(mode="json"))
    comparisons = []
    for fixture in fixtures:
        descriptor = complexity(fixture["context"])
        comparisons.append(
            {
                "fixture": fixture["id"],
                "structure": descriptor,
                "below_failed_workload": [key for key in failed if descriptor[key] < failed[key]],
                "same_saved_request": False,
            }
        )
    return {
        "kind": "offline_workload_audit_not_model_performance",
        "source": str(source.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "request_sha256": request_digest(request),
        "failed_workload": failed,
        "synthetic_fixtures": comparisons,
        "generation_calls": 0,
        "readiness": "not_demonstrated",
        "reason": "Synthetic success did not exercise the failed request or its rule structure.",
        "caution": "Neither character counts nor rule counts establish the model's failure cause.",
    }
