from concurrent.futures import ThreadPoolExecutor

import pytest
from epistemic.benchmark import load_task, partition
from epistemic.conditions import build_condition, configurations, schemas
from epistemic.metrics import audit, evaluate
from epistemic.mock import respond
from epistemic.models import CallRecord, ModelSettings
from epistemic.paths import read_json
from epistemic.provider import AuditedProvider, BudgetExceeded, CallBudget
from epistemic.runner import execute_campaign, make_plan, pilot_valid

from app.agents.executor import AgentExecutor
from app.core.models import Run
from app.llm.mock_provider import MockProvider
from app.orchestration.orchestrator import Orchestrator
from app.policies.context import ContextBuilder
from app.repositories.sql import SQLRepository
from app.tools.gateway import ToolRegistry


def test_budget_durable_and_cross_instance_atomic(tmp_path):
    path = tmp_path / "budget.sqlite"

    def attempt(_):
        try:
            CallBudget(path, 7).reserve()
            return 1
        except BudgetExceeded:
            return 0

    CallBudget(path, 7)
    with ThreadPoolExecutor(max_workers=4) as executor:
        assert sum(executor.map(attempt, range(20))) == 7
    assert CallBudget(path, 7).used == 7


def test_plan_respects_whole_block_budget():
    pilot = make_plan("pilot", 1, 180)
    main = make_plan("main", 2, 180 - pilot["approximate_model_calls"])
    assert pilot["runs"] == 10 and main["runs"] == 40
    assert pilot["approximate_model_calls"] + main["approximate_model_calls"] == 170
    assert make_plan("full", 2, 16)["runs"] == 0
    assert make_plan("full", 2, 34)["runs"] == 10


@pytest.mark.parametrize("config", configurations(), ids=lambda c: c.id)
async def test_real_runtime_e2e_all_conditions(tmp_path, config):
    task, gold = load_task("a04")
    workflow, agents, inputs, _ = build_condition(
        task, config, partition(task, gold, 3), 3, ModelSettings()
    )
    base = MockProvider(respond)
    provider = AuditedProvider(base, CallBudget(tmp_path / "calls.sqlite", 17))
    repo = SQLRepository("sqlite+aiosqlite:///:memory:")
    await repo.initialize()
    try:
        runtime = Orchestrator(
            repo, ContextBuilder(repo), AgentExecutor({"mock": provider}, schemas()), ToolRegistry()
        )
        created = await runtime.create(workflow, agents, inputs)
        run = await runtime.execute(created.id)
        scores, diagnostics = evaluate(run, gold)
        assert scores["task_success"] == 1
        assert scores["gold_claim_coverage"] == 1
        assert not diagnostics["missing_claims"]
        assert not any(audit(task, gold, provider.calls, run).values())
        assert len(provider.calls) == (1 if config.id == "C0" else 4)
        if config.id != "C0":
            assert base.max_active == 3
            synth = next(c for c in provider.calls if c.agent_id == "synthesizer")
            assert synth.request["context"]["knowledge"] == []
            assert len(synth.request["context"]["artifacts"]) == 3
        restored = Run.model_validate_json(run.model_dump_json())
        assert evaluate(restored, gold) == (scores, diagnostics)
        assert any(e.kind == "AGENT_COMPLETED" for e in await repo.events(run.id))
    finally:
        await repo.close()


async def test_audit_catches_rejected_raw_output_and_gold(tmp_path):
    task, gold = load_task("b01")
    config = configurations()[3]
    workflow, agents, inputs, assignment = build_condition(
        task, config, partition(task, gold, 5), 5, ModelSettings()
    )
    repo = SQLRepository("sqlite+aiosqlite:///:memory:")
    await repo.initialize()
    try:
        runtime = Orchestrator(
            repo,
            ContextBuilder(repo),
            AgentExecutor({"mock": MockProvider(respond)}, schemas()),
            ToolRegistry(),
        )
        run = await runtime.create(workflow, agents, inputs)
        context = await ContextBuilder(repo).build_context(
            agent=agents["worker_0"], state=run.state, run_id=run.id
        )
        from app.llm.provider import ModelRequest

        request = ModelRequest(
            agent_id="worker_0",
            instruction=agents["worker_0"].instruction,
            context=context,
            config=agents["worker_0"].model,
            output_schema={},
        )
        forbidden = next(d for d in task.evidence if d.id not in assignment.partitions["worker_0"])
        call = CallRecord(
            run_id=run.id,
            agent_id="worker_0",
            request=request.model_dump(),
            response={
                "invalid_output": forbidden.content,
                "id": forbidden.id,
                "annotation": gold.hidden_annotation,
            },
        )
        results = audit(task, gold, [call], run)
        assert results["result_leaks"] >= 2 and results["gold_leaks"] == 1
        # An unauthorized context must not authorize itself in the leakage detector.
        request.context.knowledge.append(forbidden)
        call.request = request.model_dump()
        assert audit(task, gold, [call], run)["context_leaks"] >= 2
    finally:
        await repo.close()


async def test_failed_provider_consumes_budget_and_retains_failure(tmp_path):
    def fail(request):
        raise ValueError("not safe to log exception message")

    task, gold = load_task("a01")
    workflow, agents, inputs, _ = build_condition(
        task, configurations()[0], partition(task, gold, 1), 1, ModelSettings()
    )
    provider = AuditedProvider(MockProvider(fail), CallBudget(tmp_path / "budget.sqlite", 1))
    repo = SQLRepository("sqlite+aiosqlite:///:memory:")
    await repo.initialize()
    try:
        runtime = Orchestrator(
            repo, ContextBuilder(repo), AgentExecutor({"mock": provider}, schemas()), ToolRegistry()
        )
        run = await runtime.execute((await runtime.create(workflow, agents, inputs)).id)
        assert evaluate(run, gold)[0]["task_success"] == 0
        assert evaluate(run, gold)[0]["gold_claim_coverage"] == 0
        assert provider.budget.used == 1
        assert provider.calls[0].error == "ValueError"
        assert "not safe" not in provider.calls[0].model_dump_json()
    finally:
        await repo.close()


async def test_campaign_pilot_serialization_gate_and_analysis(tmp_path):
    from epistemic.analysis import analyze
    from epistemic.figures import generate

    settings = ModelSettings()
    result = await execute_campaign(tmp_path / "campaign", "pilot", 1, settings, 7, 34)
    payload = read_json(result)
    assert len(payload["records"]) == 10
    assert payload["metadata"]["budget_used_after"] == 34
    fingerprint = payload["metadata"]["protocol_fingerprint"]
    assert pilot_valid(payload["records"], fingerprint)
    assert not pilot_valid(payload["records"][:-1], fingerprint)
    assert not pilot_valid(payload["records"], "changed")
    report = analyze(result, tmp_path / "analysis")
    generate(report, tmp_path / "figures")
    assert len(list((tmp_path / "figures").glob("*.svg"))) == 7
    assert "MOCK VALIDATION" in (tmp_path / "figures/figure2_performance.svg").read_text()
    with pytest.raises(ValueError, match="already exists"):
        await execute_campaign(tmp_path / "campaign", "pilot", 1, settings, 7, 34)


async def test_no_credentials_no_real_run(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="no provider credentials"):
        await execute_campaign(
            tmp_path, "pilot", 1, ModelSettings(provider="real", model="example"), 1, 180
        )
    assert not list(tmp_path.iterdir())
