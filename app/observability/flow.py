"""Operator-facing execution and information-flow views."""

import json

from app.core.models import Run
from app.orchestration.workflow import WorkflowDefinition


def mermaid(run: Run) -> str:
    workflow = WorkflowDefinition.model_validate(run.workflow)
    lines = ["flowchart TD"]
    node_ids = {node.id: f"n{index}" for index, node in enumerate(workflow.nodes)}
    for node in workflow.nodes:
        lines.append(f'  {node_ids[node.id]}["{node.id}: {run.state.nodes[node.id]}"]')
    for edge in workflow.edges:
        label = "conditional" if edge.condition else "depends on"
        lines.append(f"  {node_ids[edge.source]} -->|{label}| {node_ids[edge.target]}")
    for index, record in enumerate(run.state.agent_runs):
        # Labels originate in trusted policy IDs, escaped for Mermaid syntax.
        categories = (
            ", ".join(record.context_categories)
            .replace('"', "'")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        lines.append(f'  c{index}["context: {categories}"] -.-> {node_ids[record.node_id]}')
    for index, artifact in enumerate(run.state.artifacts):
        lines.append(f'  a{index}[("{artifact.name} v{artifact.version}")]')
        lines.append(f"  {node_ids[artifact.node_id]} --> a{index}")
        for record in run.state.agent_runs:
            if artifact.id in record.context_artifact_ids:
                lines.append(f"  a{index} --> {node_ids[record.node_id]}")
    return "\n".join(lines)


def inspect_run(run: Run, *, content: bool = False) -> str:
    lines = [f"Run {run.id} | {run.workflow_id} | {run.status} | revision {run.revision}", "Task"]
    for record in run.state.agent_runs:
        lines.extend(
            [
                f" ├─→ {record.agent_id} [{record.status}] model={record.model}",
                " │   context: " + ", ".join(record.context_categories),
                f" │   latency={record.latency_ms:.1f}ms retries={max(0, record.attempts - 1)}",
            ]
        )
        if record.result and record.result.error:
            lines.append(f" │   error: {record.result.error.code}")
    lines.append("Artifacts:")
    for artifact in run.state.artifacts:
        lines.append(
            f"  {artifact.id} {artifact.name} v{artifact.version}: {artifact.producer} "
            f"→ {', '.join(artifact.readers) or 'operator'}"
        )
        if content:
            lines.append(json.dumps(artifact.payload, ensure_ascii=False))
    lines.append("Messages:")
    for message in run.state.messages:
        lines.append(
            f"  {message.sender} → {', '.join(message.recipients)}: "
            f"{', '.join(ref.id for ref in message.artifacts)}"
        )
    lines.append("Usage: " + run.usage().model_dump_json())
    return "\n".join(lines)


def run_summary(run: Run) -> dict[str, object]:
    return {
        "id": run.id,
        "workflow": run.workflow_id,
        "status": run.status,
        "revision": run.revision,
        "nodes": run.state.nodes,
        "agent_runs": [a.model_dump(mode="json") for a in run.state.agent_runs],
        "usage": run.usage().model_dump(mode="json"),
        "final_results": [
            a.model_dump(mode="json")
            for a in run.state.artifacts
            if a.id in run.state.final_artifact_ids
        ],
        "pending_approvals": [key for key, status in run.state.nodes.items() if status == "paused"],
    }
