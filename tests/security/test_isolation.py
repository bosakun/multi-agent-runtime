import pytest

from app.core.errors import RuntimeFault
from app.core.models import (
    Artifact,
    ArtifactRef,
    Knowledge,
    MessageEnvelope,
    WorkflowInput,
    WorkflowState,
)
from app.memory.store import agent_namespace
from app.orchestration.router import route
from app.policies.context import ContextBuilder
from demos.catalog import configure


async def test_secret_context_and_result_isolation(service, provider):
    task = WorkflowInput(
        task="Analyze assigned evidence",
        knowledge={
            "evidence_a": Knowledge(id="evidence_a", content="secret.a = apple"),
            "evidence_b": Knowledge(id="evidence_b", content="secret.b = banana"),
            "evidence_c": Knowledge(id="evidence_c", content="secret.c = cherry"),
        },
    )
    run_id = await service.create_run("investigation", task)
    run = await service.orchestrator.execute(run_id)
    contexts = {r.agent_id: r.context.model_dump_json() for r in provider.requests}
    outputs = {a.producer: a.model_dump_json() for a in run.state.artifacts}
    assert "banana" not in contexts["investigator_a"] + outputs["investigator_a"]
    assert "apple" not in contexts["investigator_b"] + outputs["investigator_b"]
    assert "cherry" not in contexts["investigator_a"] + outputs["investigator_a"]
    # Publication explicitly releases structured findings to the reviewer.
    assert "apple" in contexts["reviewer"] and "banana" in contexts["reviewer"]
    assert not next(r.context for r in provider.requests if r.agent_id == "reviewer").knowledge
    for request in provider.requests:
        assert not hasattr(request.context, "state")
        assert not hasattr(request.context, "repository")


async def test_memory_namespaces_and_detached_context(service, investigation_input):
    _, agents = configure("investigation", investigation_input)
    agent = agents["investigator_a"]
    agent.context.private_memory_keys = ["note"]
    agent.context.long_term_memory_keys = ["habit"]
    agent.context.shared_memory_keys = ["public"]
    repo = service.repository
    await repo.write("private", agent_namespace("run", agent.id), "note", {"secret": "apple"})
    await repo.write("private", agent_namespace("run", "investigator_b"), "note", "banana")
    await repo.write("private", agent_namespace("other_run", agent.id), "note", "other run")
    await repo.write("long_term", agent.id, "habit", "persists")
    await repo.write("long_term", "investigator_b", "habit", "hidden")
    await repo.write("shared", "run", "public", "approved")
    await repo.write("shared", "run", "private", "not approved")
    state = WorkflowState(task=investigation_input, nodes={})
    context = await ContextBuilder(repo).build_context(agent=agent, state=state, run_id="run")
    assert context.private_memory == {"note": {"secret": "apple"}}
    assert context.long_term_memory == {"habit": "persists"}
    assert context.shared_memory == {"public": "approved"}
    context.knowledge[0].content = "mutated"
    context.private_memory["note"] = "mutated"
    assert state.task.knowledge["evidence_a"].content != "mutated"
    assert (await repo.read("private", agent_namespace("run", agent.id), ["note"]))["note"] == {
        "secret": "apple"
    }
    next_run = await ContextBuilder(repo).build_context(agent=agent, state=state, run_id="next")
    assert not next_run.private_memory and next_run.long_term_memory["habit"] == "persists"


async def test_artifact_selection_requires_policy_and_acl(service, investigation_input):
    _, agents = configure("investigation", investigation_input)
    state = WorkflowState(task=investigation_input, nodes={})
    artifact = Artifact(
        name="note",
        version=1,
        producer="investigator_a",
        node_id="a",
        schema_id="findings",
        payload={"secret": "apple"},
        readers=[],
    )
    state.artifacts.append(artifact)
    builder = ContextBuilder(service.repository)
    context = await builder.build_context(agent=agents["reviewer"], state=state, run_id="r")
    assert not context.artifacts
    artifact.readers = ["reviewer", "investigator_b"]
    context = await builder.build_context(agent=agents["reviewer"], state=state, run_id="r")
    assert context.artifacts
    context = await builder.build_context(agent=agents["investigator_b"], state=state, run_id="r")
    assert not context.artifacts
    message = MessageEnvelope(
        sender="investigator_a",
        recipients=["investigator_b"],
        artifacts=[ArtifactRef(id=artifact.id, version=1)],
    )
    with pytest.raises(RuntimeFault, match="unauthorized_message_recipient"):
        route(message, state, agents)
    assert not state.messages


async def test_context_budget_rejected(service, investigation_input):
    _, agents = configure("investigation", investigation_input)
    agent = agents["investigator_a"]
    agent.context.max_context_chars = 100
    with pytest.raises(RuntimeFault, match="context_budget_exceeded"):
        await ContextBuilder(service.repository).build_context(
            agent=agent, state=WorkflowState(task=investigation_input, nodes={}), run_id="r"
        )


async def test_events_never_include_raw_documents(service, provider, investigation_input):
    investigation_input.knowledge["evidence_a"].content += "\nPII_SECRET_email@example.test"
    run_id = await service.create_run("investigation", investigation_input)
    await service.orchestrator.execute(run_id)
    events = await service.repository.events(run_id)
    assert "PII_SECRET" not in "".join(e.model_dump_json() for e in events)
    assert "email@example" not in "".join(e.model_dump_json() for e in events)
