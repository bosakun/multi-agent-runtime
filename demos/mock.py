"""Transparent fixture rules, not a claim of model reasoning quality."""

import json
import re
from collections import defaultdict

from app.core.models import Uncertainty, Usage
from app.llm.provider import ModelRequest, ModelResponse, ToolCall
from demos.schemas import (
    Conflict,
    ConflictReport,
    FinalReport,
    Finding,
    Findings,
    ReviewResult,
    Severity,
)


def respond(request: ModelRequest) -> ModelResponse:
    if (
        not request.exchanges
        and "changed_code" in request.context.inputs
        and any(tool["name"] == "scan_python" for tool in request.tools)
    ):
        return ModelResponse(
            tool_calls=[
                ToolCall(
                    id="scan",
                    name="scan_python",
                    arguments={
                        "code": request.context.inputs["changed_code"],
                    },
                )
            ],
            usage=Usage(input_tokens=len(request.model_dump_json()) // 4, output_tokens=30),
        )
    findings: list[Finding] = []
    for document in request.context.knowledge:
        for subject, value in re.findall(
            r"^([a-z_.]+)\s*=\s*([^\n]+)$", document.content, re.MULTILINE
        ):
            findings.append(
                Finding(subject=subject, value=value.strip(), evidence_ids=[document.id])
            )
    for artifact in request.context.artifacts:
        published = artifact.payload.get("findings", [])
        if isinstance(published, list):
            findings.extend(Finding.model_validate(item) for item in published)
    inputs = request.context.inputs
    rules: list[tuple[str, str, str, str, Severity]] = [
        (
            "architecture",
            "directly",
            "layering",
            "API reaches the database directly",
            "warning",
        ),
        (
            "changed_code",
            "eval(",
            "dynamic_execution",
            "Untrusted expression reaches eval",
            "critical",
        ),
        (
            "tests",
            "happy path",
            "negative_tests",
            "Missing adversarial and error-path tests",
            "warning",
        ),
        (
            "diff",
            "duplicate",
            "duplication",
            "Repeated validation should be centralized",
            "warning",
        ),
    ]
    for key, marker, subject, value, severity in rules:
        if key in inputs and marker in str(inputs[key]).lower():
            findings.append(Finding(subject=subject, value=value, severity=severity))
    unique = {f"{f.subject}:{f.value}:{','.join(f.evidence_ids)}": f for f in findings}
    findings = list(unique.values())
    groups: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        groups[finding.subject].append(finding)
    conflicts = [
        Conflict(
            subject=subject,
            values=sorted({f.value for f in items}),
            evidence_ids=sorted({e for f in items for e in f.evidence_ids}),
        )
        for subject, items in groups.items()
        if len({f.value for f in items}) > 1
    ]
    uncertainty = Uncertainty(
        confidence=0.6 if conflicts else 0.8,
        assumptions=["Deterministic fixture extraction; not an independent factual verification"],
        evidence_ids=sorted({e for f in findings for e in f.evidence_ids}),
        unknowns=["Unresolved source disagreement"] if conflicts else [],
    )
    title = request.output_schema.get("title")
    result: Findings
    if title == "FinalReport":
        result = FinalReport(
            findings=findings,
            conflicts=conflicts,
            uncertainty=uncertainty,
            summary=(
                f"{len(findings)} supported fixture findings; "
                f"{len(conflicts)} unresolved conflicts."
            ),
            decision="needs_review"
            if conflicts or any(f.severity == "critical" for f in findings)
            else "accept",
        )
    elif title == "ConflictReport":
        result = ConflictReport(findings=findings, conflicts=conflicts, uncertainty=uncertainty)
    elif title == "ReviewResult":
        result = ReviewResult(findings=findings, uncertainty=uncertainty)
    else:
        result = Findings(findings=findings, uncertainty=uncertainty)
    output = result.model_dump(mode="json")
    return ModelResponse(
        output=output,
        usage=Usage(
            input_tokens=max(1, len(request.model_dump_json()) // 4),
            output_tokens=max(1, len(json.dumps(output)) // 4),
            model_calls=1,
        ),
    )
