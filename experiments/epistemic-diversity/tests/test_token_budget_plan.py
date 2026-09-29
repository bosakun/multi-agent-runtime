"""Offline validation of a proposed plan, not an executable real-model experiment."""

import json
import random
from pathlib import Path

import pytest
from epistemic.freeze import verify
from epistemic.models import ModelSettings, TaskInstructions, WorkerOutput

from app.core.models import AgentContext, ModelConfig

ROOT = Path(__file__).resolve().parents[1]
PLAN_ROOT = ROOT / "diagnostics/token-budget-v1"


def read(name):
    return json.loads((PLAN_ROOT / name).read_text())


def test_planned_budget_and_single_factor_manipulation():
    plan = read("plan.json")
    assert plan["generation_limits"] == [2048, 4096]
    assert plan["planned_calls"] == plan["hard_call_limit"] == len(plan["schedule"]) == 6
    assert (
        plan["maximum_generated_tokens_if_limits_enforced"]
        == sum(cell["max_output_tokens"] for cell in plan["schedule"])
        == 18432
    )
    assert plan["maximum_generation_wait_seconds"] == plan["timeout_seconds"] * 6 == 3600
    assert plan["repetitions_per_cell"] == plan["max_attempts_per_cell"] == 1
    assert plan["worker_concurrency"] == plan["model_concurrency"] == 1
    assert plan["temperature"] == 0
    assert plan["thinking"] == "model_default; no override sent"
    assert plan["token_limit_parameter"] == "max_tokens"
    assert plan["tools"] == []
    assert plan["model"] == "qwen3:14b"


def test_fixed_order_reproducible_and_balanced_without_outcomes():
    plan = read("plan.json")
    fixtures = [fixture["id"] for fixture in read("inputs.json")["fixtures"]]
    first_limits = [2048, 4096, 2048]
    rng = random.Random(plan["ordering_seed"])
    rng.shuffle(fixtures)
    rng.shuffle(first_limits)
    expected = [
        (fixture, limit)
        for fixture, first in zip(fixtures, first_limits, strict=True)
        for limit in (first, 6144 - first)
    ]
    assert [(c["fixture_id"], c["max_output_tokens"]) for c in plan["schedule"]] == expected
    assert len({c["cell_id"] for c in plan["schedule"]}) == 6
    assert len(set(expected)) == 6


def test_synthetic_fixtures_validate_and_have_no_benchmark_identifiers():
    inputs = read("inputs.json")
    fixtures = inputs["fixtures"]
    assert len(fixtures) == len({f["id"] for f in fixtures}) == 3
    evidence_ids = set()
    for fixture in fixtures:
        context = AgentContext.model_validate(fixture["context"])
        TaskInstructions.model_validate(context.inputs)
        assert context.messages == []
        assert context.private_memory == context.shared_memory == context.long_term_memory == {}
        if fixture["prompt_kind"] == "worker":
            assert not context.artifacts
        else:
            assert not context.knowledge
            assert len(context.artifacts) == 3
            for artifact in context.artifacts:
                WorkerOutput.model_validate(artifact.payload)
                assert artifact.readers == ["synthesizer"]
        evidence_ids.update(context.evidence_scope())
    text = json.dumps(inputs)
    assert all(evidence.startswith("diag-") for evidence in evidence_ids)
    assert not any(marker in text for marker in ("CANARY_", "GOLD_", "v2-", "gold_answer"))


def test_new_budget_does_not_relax_current_pilot_or_reuse_campaign():
    frozen = verify()
    plan = read("plan.json")
    assert frozen["freeze_sha256"] == plan["historical_freeze_sha256"]
    assert frozen["generation_controls"]["max_output_tokens"] == 2048
    with pytest.raises(ValueError, match="output limit 2048"):
        ModelSettings(execution_profile="local_ollama", timeout_seconds=600, max_output_tokens=4096)
    assert ModelConfig(max_output_tokens=4096).max_output_tokens == 4096
    assert plan["future_campaign"] == "runs/qwen3-14b-token-budget-diag-v1"
    assert plan["future_binding"] == plan["future_campaign"] + "/binding.json"
    assert plan["future_seal"] == "diagnostics/token-budget-v1/seal.json"
    assert "planning_only" in plan["status"]


def test_prompt_schema_references_and_explicit_stop_scope():
    plan = read("plan.json")
    for reference in plan["prompt_refs"].values():
        assert (ROOT / reference.split("#")[0]).is_file()
    assert set(plan["schema_refs"]) == {"worker.v1", "final.v1"}
    assert plan["expected_diagnostic_failure"] == ["provider_output_truncated"]
    assert "timeout" in plan["stop_on"]
    assert "non_length_schema_or_envelope_failure" in plan["stop_on"]
    assert "retry" in plan["forbidden"]
    assert "automatic_pilot_launch" in plan["forbidden"]
    assert "real_call_without_explicit_launch_approval" in plan["forbidden"]
