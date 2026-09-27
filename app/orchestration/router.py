"""Explicit publication is the only agent-to-agent data channel."""

from app.core.errors import RuntimeFault
from app.core.models import AgentDefinition, Artifact, MessageEnvelope, WorkflowState


def publish(state: WorkflowState, artifact: Artifact) -> None:
    previous = [
        a for a in state.artifacts if a.producer == artifact.producer and a.name == artifact.name
    ]
    expected = max((a.version for a in previous), default=0) + 1
    if artifact.version != expected or any(a.id == artifact.id for a in state.artifacts):
        raise RuntimeFault("invalid_artifact_version")
    state.artifacts.append(artifact.model_copy(deep=True))


def route(
    message: MessageEnvelope, state: WorkflowState, agents: dict[str, AgentDefinition]
) -> None:
    if message.sender not in agents or len(set(message.recipients)) != len(message.recipients):
        raise RuntimeFault("invalid_message_sender_or_recipients")
    sender = agents[message.sender]
    artifacts = {(a.id, a.version): a for a in state.artifacts}
    for recipient in message.recipients:
        if recipient not in agents or recipient not in sender.publish_to:
            raise RuntimeFault("unauthorized_message_recipient")
        for ref in message.artifacts:
            artifact = artifacts.get((ref.id, ref.version))
            if (
                artifact is None
                or artifact.producer != sender.id
                or recipient not in artifact.readers
                or sender.id not in agents[recipient].context.artifact_producers
            ):
                raise RuntimeFault("unauthorized_artifact_reference")
    state.messages.append(message.model_copy(deep=True))
