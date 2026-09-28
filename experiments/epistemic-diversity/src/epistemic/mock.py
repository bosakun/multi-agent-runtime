"""Public-rule interpreter, NOT a model of role-dependent LLM behavior."""

from app.core.models import Uncertainty, Usage
from app.llm.provider import ModelRequest, ModelResponse
from epistemic.models import Claim, FinalOutput, TaskInstructions, WorkerOutput
from epistemic.reasoning import derive, observation, supported_claims


def respond(request: ModelRequest) -> ModelResponse:
    """Solve only supplied observations/public rules; never import annotations."""
    instructions = TaskInstructions.model_validate(request.context.inputs)
    known: dict[str, Claim] = {}
    for document in request.context.knowledge:
        claim = observation(document)
        if claim and claim.subject in instructions.reporting_fields:
            known[claim.key()] = claim
    for artifact in request.context.artifacts:
        published = WorkerOutput.model_validate(artifact.payload)
        for claim in published.claims + published.insights:
            known[claim.key()] = claim
    known = {
        claim.key(): claim
        for claim in supported_claims(derive(list(known.values()), instructions.inference_rules))
    }
    claims = [c for c in known.values() if c.subject in instructions.reporting_fields]
    insights = [c for c in known.values() if c.subject not in instructions.reporting_fields]
    values = WorkerOutput(
        claims=claims,
        insights=insights,
        uncertainty=Uncertainty(
            evidence_ids=sorted({eid for claim in known.values() for eid in claim.evidence_ids}),
            unknowns=[c.value for c in insights if c.subject == "information_gap"]
            + [
                field
                for field in instructions.reporting_fields
                if field not in {c.subject for c in claims}
            ],
        ),
    )
    output: WorkerOutput
    if request.output_schema.get("title") == "FinalOutput":
        choices = [
            rule.choice
            for rule in instructions.decision_rules
            if all(p.key() in known for p in rule.premises)
        ]
        output = FinalOutput(
            **values.model_dump(),
            conclusion=choices[0] if len(choices) == 1 else "undetermined",
            decision_summary="Public rules evaluated over available observations.",
        )
    else:
        output = values
    return ModelResponse(
        output=output.model_dump(mode="json"),
        usage=Usage(
            input_tokens=len(request.model_dump_json()) // 4,
            output_tokens=len(output.model_dump_json()) // 4,
        ),
    )
