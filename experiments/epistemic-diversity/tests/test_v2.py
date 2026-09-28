import json
from collections import Counter

import pytest
from epistemic.analysis import aggregate
from epistemic.benchmark import load_task, partition, selected_tasks
from epistemic.benchmark_audit import consequences, quality_audit
from epistemic.benchmark_v2 import FAMILIES, PILOT_IDS, SEED, VERSION, build_v2, partition_stats
from epistemic.conditions import build_condition, configurations
from epistemic.freeze import bind_model, seal, validate_binding, validate_endpoint, verify
from epistemic.metrics import collective_gain, marginal_support
from epistemic.mock import respond
from epistemic.models import Gold, GoldClaim, ModelSettings, PublicTask
from epistemic.paths import ROOT, read_json, write_json
from epistemic.provider import AuditedProvider, CallBudget
from epistemic.runner import execute_campaign, make_plan, run_case

from app.core.models import WorkflowState
from app.llm.mock_provider import MockProvider
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository


def test_all_families_difficulty_and_static_audit():
    report = quality_audit()
    assert report["passed"], report["errors"]
    assert set(report["families"]) == set(FAMILIES)
    assert report["tasks"] == 30
    assert report["difficulty_counts"] == {"easy": 10, "medium": 10, "hard": 10}
    assert report["structural_signatures"] >= 10
    assert all(e["minimum_decision_documents"] >= 3 for e in report["entries"])


def test_pilot_fixed_diverse_and_budgeted():
    assert selected_tasks("pilot", VERSION) == PILOT_IDS
    tasks = [load_task(t)[0] for t in PILOT_IDS]
    assert len({t.family for t in tasks}) == 6
    assert Counter(t.difficulty for t in tasks) == {"easy": 2, "medium": 2, "hard": 2}
    plan = make_plan("pilot", 1, 60, VERSION)
    assert plan["conditions"] == ["C2", "C3"]
    assert plan["runs"] == 12 and plan["approximate_model_calls"] == 48
    assert not plan["omitted_blocks"]
    assert make_plan("full", 1, 600, VERSION)["approximate_model_calls"] == 510


@pytest.mark.parametrize("task_id", selected_tasks("full", VERSION))
def test_partition_serialization_and_answer_not_in_public_metadata(task_id):
    task, gold = load_task(task_id)
    assert PublicTask.model_validate_json(task.model_dump_json()) == task
    assert Gold.model_validate_json(gold.model_dump_json()) == gold
    assert task.benchmark_version == gold.benchmark_version == VERSION
    assert gold.hidden_annotation not in task.model_dump_json()
    assert not any(
        key in task.model_dump_json() for key in ["supporting_sets", "required_unknowns"]
    )
    groups = partition(task, gold, SEED)
    assert groups == partition(task, gold, SEED)
    assert groups != partition(task, gold, SEED + 1)
    assert partition_stats(gold, groups)["max_decision_support_share"] <= 2 / 3
    assert not consequences(task, set())[1]
    for document in task.evidence:
        assert not consequences(task, {document.id})[1]


async def test_v2_contexts_exclude_annotations_and_other_partitions():
    repo = SQLRepository("sqlite+aiosqlite:///:memory:")
    await repo.initialize()
    try:
        for task_id in selected_tasks("full", VERSION):
            task, gold = load_task(task_id)
            for config in configurations():
                groups = partition(task, gold, SEED)
                _, agents, inputs, roles = build_condition(
                    task, config, groups, SEED, ModelSettings()
                )
                for agent in agents.values():
                    context = await ContextBuilder(repo).build_context(
                        agent=agent, state=WorkflowState(task=inputs, nodes={}), run_id="v2-test"
                    )
                    raw = context.model_dump_json()
                    assert gold.hidden_annotation not in raw
                    assert "required_unknowns" not in raw and "evidence_importance" not in raw
                    assert {d.id for d in context.knowledge} == set(agent.context.knowledge_ids)
                    for document in task.evidence:
                        if document.id not in agent.context.knowledge_ids:
                            assert document.id not in raw
                            assert document.content.split("CANARY_")[1] not in raw
                if config.id == "C4":
                    shared_roles = build_condition(
                        task, configurations()[2], groups, SEED, ModelSettings()
                    )[3]
                    assert roles.roles == shared_roles.roles
    finally:
        await repo.close()


def test_v2_role_partition_randomization():
    maps = set()
    for task_id in PILOT_IDS:
        task, gold = load_task(task_id)
        for seed in range(5):
            result = build_condition(
                task, configurations()[4], partition(task, gold, seed), seed, ModelSettings()
            )[3]
            assert (
                result
                == build_condition(
                    task, configurations()[4], partition(task, gold, seed), seed, ModelSettings()
                )[3]
            )
            maps.add(json.dumps(result.roles, sort_keys=True))
    assert len(maps) == 6


def test_public_candidate_order_is_common_seeded_and_not_gold_first():
    positions = Counter()
    for task_id in selected_tasks("full", VERSION):
        task, gold = load_task(task_id)
        original = task.instructions.model_dump()
        input_views = [
            build_condition(task, c, partition(task, gold, SEED), SEED, ModelSettings())[2].inputs
            for c in configurations()
        ]
        assert all(view == input_views[0] for view in input_views)
        assert task.instructions.model_dump() == original  # no mutation of canonical files
        choices = input_views[0]["decision_rules"]
        positions[
            next(i for i, c in enumerate(choices) if c["choice"] == gold.expected_conclusion)
        ] += 1
    assert positions == {0: 16, 1: 14}
    task, gold = load_task(PILOT_IDS[0])
    views = {
        json.dumps(
            build_condition(
                task, configurations()[2], partition(task, gold, s), s, ModelSettings()
            )[2].inputs,
            sort_keys=True,
        )
        for s in range(10)
    }
    assert len(views) > 1


def test_collective_and_marginal_are_useful_not_lexical():
    assert collective_gain([{"a"}, {"b", "noise"}], {"a", "b"}) == 0.5
    assert collective_gain([{"a", "b"}] * 3, {"a", "b"}) == 0
    gold = [
        GoldClaim(subject="x", value="yes", supporting_sets=[["a"]]),
        GoldClaim(subject="y", value="yes", supporting_sets=[["b", "c"]]),
    ]
    drops = marginal_support([{"a"}, {"b"}, {"c"}], {"x=yes", "y=yes"}, gold)
    assert [m["drop"] for m in drops] == [0.5, 0.5, 0.5]  # not an additive Shapley attribution
    assert [
        m["drop"]
        for m in marginal_support([{"a", "b", "c"}, set(), set()], {"x=yes", "y=yes"}, gold)
    ] == [1, 0, 0]
    assert [
        m["drop"] for m in marginal_support([{"a", "b", "c"}] * 3, {"x=yes", "y=yes"}, gold)
    ] == [0, 0, 0]


@pytest.mark.parametrize("task_id", PILOT_IDS)
async def test_v2_e2e_record_and_uncertainty(tmp_path, task_id):
    repo = SQLRepository("sqlite+aiosqlite:///:memory:")
    await repo.initialize()
    provider = AuditedProvider(MockProvider(respond), CallBudget(tmp_path / "budget.sqlite", 8))
    metadata = {
        "protocol_fingerprint": "test",
        "source": {"git_commit": "test-commit", "source_sha256": "test-source", "dirty": True},
    }
    try:
        for config in configurations()[2:4]:
            record = await run_case(
                repo,
                provider,
                ModelSettings(),
                task_id,
                config,
                SEED,
                0,
                "test-experiment",
                metadata,
                tmp_path,
            )
            assert record["benchmark_version"] == VERSION
            assert record["git_commit"] == "test-commit"
            assert record["metrics"]["task_success"] == 1, record
            assert record["metrics"]["gold_leaks"] == record["metrics"]["context_leaks"] == 0
            if "missing" in task_id:
                assert record["output"][0]["conclusion"] == "undetermined"
                assert record["output"][0]["uncertainty"]["unknowns"] == ["item_mass"]
            assert read_json(tmp_path / "records" / f"{record['run_id']}.json") == record
    finally:
        await repo.close()


def test_v2_rebuild_preserves_version_and_exact_dataset(tmp_path):
    write_json(
        tmp_path / "benchmarks/v2/specifications.json",
        read_json(ROOT / "benchmarks/v2/specifications.json"),
    )
    build_v2(tmp_path)
    for folder in ["public", "gold"]:
        for path in (ROOT / "benchmarks/v2" / folder).glob("*.json"):
            assert read_json(path) == read_json(tmp_path / "benchmarks/v2" / folder / path.name)


def test_freeze_tamper_and_model_binding(tmp_path, monkeypatch):
    import epistemic.freeze as freezing

    monkeypatch.setattr(freezing, "frozen_files", lambda: {"test": "digest-v1"})
    frozen = tmp_path / "freeze.json"
    seal(frozen)
    with pytest.raises(ValueError, match="already exists"):
        seal(frozen)
    binding = tmp_path / "binding.json"
    bind_model(binding, "test-provider-model", "https://example.invalid/v1", frozen)
    validate_binding(
        binding,
        ModelSettings(provider="real", model="test-provider-model"),
        "https://example.invalid/v1/",
        SEED,
        frozen,
    )
    with pytest.raises(ValueError, match="settings/endpoint/seed"):
        validate_binding(
            binding,
            ModelSettings(provider="real", model="changed"),
            "https://example.invalid/v1/",
            SEED,
            frozen,
        )
    monkeypatch.setattr(freezing, "frozen_files", lambda: {"test": "modified"})
    with pytest.raises(ValueError, match="Frozen content changed"):
        verify(frozen)


@pytest.mark.parametrize(
    "endpoint", ["http://example.com/v1", "https://secret@host/v1", "https://host/v1?key=secret"]
)
def test_secret_unsafe_endpoint_rejected(endpoint):
    with pytest.raises(ValueError):
        validate_endpoint(endpoint)


async def test_real_main_disabled_before_network(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-not-real")
    with pytest.raises(ValueError, match="main/full are disabled"):
        await execute_campaign(
            tmp_path,
            "main",
            1,
            ModelSettings(provider="real", model="test-model"),
            SEED,
            60,
            VERSION,
        )
    assert not list(tmp_path.iterdir())


def test_family_cluster_analysis_and_mixed_version_rejection():
    records = [
        {
            "task_id": f"{family}-{i}",
            "family": family,
            "condition": c,
            "repetition": 0,
            "benchmark_version": VERSION,
            "metrics": {
                "task_success": int(c == "C3"),
                "gold_claim_coverage": int(c == "C3"),
                "worker_evidence_coverage": int(c == "C3"),
            },
        }
        for family in ["a", "b"]
        for i in range(3)
        for c in ["C2", "C3"]
    ]
    report = aggregate(records, ["C2", "C3"])
    assert not report["incomplete_blocks"]
    assert len(report["primary"]) == 2
    assert report["primary"][0]["n_units"] == 2
    assert report["primary"][0]["n_tasks"] == 6
    assert report["primary"][0]["resampling_unit"] == "family"
    assert report["binary_secondary"][0]["p"] is None
    records[0]["benchmark_version"] = "1.0.0"
    with pytest.raises(ValueError, match="Do not pool"):
        aggregate(records)
