import json

import pytest
from epistemic.benchmark import load_task, partition, selected_tasks
from epistemic.conditions import build_condition, configurations
from epistemic.models import ModelSettings
from epistemic.paths import ROOT

from app.core.models import WorkflowState
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository


def test_dataset_integrity_and_balance():
    tasks = selected_tasks("full")
    assert len(tasks) == 24 and len(set(tasks)) == 24
    assert not set(selected_tasks("pilot")) & set(selected_tasks("main"))
    for task_id in tasks:
        task, gold = load_task(task_id)
        assert gold.hidden_annotation not in task.model_dump_json()
        assert "supporting_sets" not in task.model_dump_json()
        groups = partition(task, gold, 42)
        assert set().union(*map(set, groups.values())) == {d.id for d in task.evidence}
        assert sum(map(len, groups.values())) == 9
        for ids in groups.values():
            assert len(set(ids) & set(gold.relevant_evidence_ids)) == 2
            assert len(set(ids) & set(gold.distractor_ids)) == 1
        assert partition(task, gold, 42) == groups
        assert len({rule.choice for rule in task.instructions.decision_rules}) == 4


def test_condition_controls_and_randomization():
    task, gold = load_task("a01")
    configs = configurations()
    assert [c.id for c in configs] == ["C0", "C1", "C2", "C3", "C4"]
    policies = [
        build_condition(task, c, partition(task, gold, 42), 42, ModelSettings()) for c in configs
    ]
    for i in range(1, 5):
        workflow, agents, _, assignment = policies[i]
        assert len(assignment.roles) == 3
        assert workflow.max_parallel == 3
        assert all(not agent.tools.allowed for agent in agents.values())
        assert agents["synthesizer"].context.knowledge_ids == []
        assert agents["synthesizer"].instruction == policies[1][1]["synthesizer"].instruction
        for worker in assignment.roles:
            assert not agents[worker].context.artifact_producers
            assert agents[worker].model == policies[1][1][worker].model
    assert policies[1][1]["worker_0"].instruction == policies[3][1]["worker_0"].instruction
    assert len({a.instruction for k, a in policies[1][1].items() if k.startswith("worker")}) == 1
    assert policies[2][3].roles == policies[4][3].roles
    maps = {
        json.dumps(
            build_condition(task, configs[4], partition(task, gold, s), s, ModelSettings())[
                3
            ].roles,
            sort_keys=True,
        )
        for s in range(20)
    }
    assert len(maps) > 1


@pytest.mark.parametrize("config", configurations(), ids=lambda c: c.id)
async def test_actual_context_isolation(config):
    task, gold = load_task("b04")
    groups = partition(task, gold, 21)
    _, agents, inputs, _ = build_condition(task, config, groups, 21, ModelSettings())
    repo = SQLRepository("sqlite+aiosqlite:///:memory:")
    await repo.initialize()
    try:
        for key, agent in agents.items():
            context = await ContextBuilder(repo).build_context(
                agent=agent, state=WorkflowState(task=inputs, nodes={}), run_id="isolation-test"
            )
            text = context.model_dump_json()
            assert gold.hidden_annotation not in text
            assert not any(k in text for k in ["expected_conclusion", "supporting_sets"])
            if key == "synthesizer":
                assert not context.knowledge
            elif config.separated_evidence:
                assert {d.id for d in context.knowledge} == set(groups[key])
                for document in task.evidence:
                    if document.id not in groups[key]:
                        assert document.id not in text
                        assert document.content.split("Source routing marker: ")[1] not in text
            # Mutating a returned context must never mutate authoritative state.
            context.inputs.clear()
            assert inputs.inputs
    finally:
        await repo.close()


def test_dependency_direction_and_mock_no_gold_access():
    repo = ROOT.parents[1]
    for path in (repo / "app").rglob("*.py"):
        assert "from epistemic" not in path.read_text()
        assert "import epistemic" not in path.read_text()
    source = (ROOT / "src/epistemic/mock.py").read_text()
    assert "load_task" not in source and "read_json" not in source


def test_generated_files_are_reproducible(tmp_path, monkeypatch):
    from epistemic import benchmark
    from epistemic.paths import read_json, write_json

    original = benchmark.ROOT
    write_json(
        tmp_path / "benchmarks/specifications.json",
        read_json(original / "benchmarks/specifications.json"),
    )
    monkeypatch.setattr(benchmark, "ROOT", tmp_path)
    benchmark.build_benchmark()
    for path in (original / "benchmarks").rglob("*.json"):
        if "v2" in path.parts:
            continue
        assert read_json(path) == read_json(tmp_path / path.relative_to(original))
