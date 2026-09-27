import pytest
from pydantic import ValidationError

from app.core.errors import RuntimeFault
from app.core.models import Artifact, MessageEnvelope, Uncertainty, WorkflowInput, WorkflowState
from app.orchestration.router import publish
from app.orchestration.workflow import Condition, Edge, Node, WorkflowDefinition


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_invalid_confidence(confidence):
    with pytest.raises(ValidationError):
        Uncertainty(confidence=confidence)


def test_messages_are_closed_and_structured():
    with pytest.raises(ValidationError):
        MessageEnvelope(sender="a", recipients=[], artifacts=[])
    with pytest.raises(ValidationError):
        MessageEnvelope(sender="a", recipients=["b"], artifacts=[], raw_context="SECRET")


@pytest.mark.parametrize(
    "nodes,edges",
    [
        ([Node(id="a", agent_id="a"), Node(id="a", agent_id="a")], []),
        ([Node(id="a", agent_id="a")], [Edge(source="a", target="missing")]),
        ([Node(id="a", agent_id="a")], [Edge(source="a", target="a")]),
        (
            [Node(id="a", agent_id="a"), Node(id="b", agent_id="b")],
            [Edge(source="a", target="b"), Edge(source="b", target="a")],
        ),
    ],
)
def test_invalid_graph(nodes, edges):
    with pytest.raises(ValidationError):
        WorkflowDefinition(id="bad", description="bad", nodes=nodes, edges=edges)


def test_condition_missing_is_false():
    assert Condition(field="nested.flag", equals=True).matches({"nested": {"flag": True}})
    assert not Condition(field="missing", equals=None).matches({})


def test_artifact_versions_are_append_only():
    state = WorkflowState(task=WorkflowInput(task="t"), nodes={})
    artifact = Artifact(
        name="note",
        version=1,
        producer="a",
        node_id="a",
        schema_id="x",
        payload={"value": 1},
        readers=[],
    )
    publish(state, artifact)
    artifact.payload["value"] = 99
    assert state.artifacts[0].payload["value"] == 1
    with pytest.raises(RuntimeFault, match="invalid_artifact_version"):
        publish(state, artifact)
    second = artifact.model_copy(update={"id": "second", "version": 2})
    publish(state, second)
    assert [a.version for a in state.artifacts] == [1, 2]
