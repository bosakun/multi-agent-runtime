"""Bounded structured model/tool execution."""

from pydantic import ValidationError

from app.core.errors import RuntimeFault
from app.core.models import AgentContext, AgentDefinition, AgentResult, Status, Uncertainty, Usage
from app.core.schemas import SchemaRegistry
from app.llm.provider import ModelProvider, ModelRequest, ToolExchange
from app.tools.gateway import ToolGateway


class AgentExecutor:
    def __init__(self, providers: dict[str, ModelProvider], schemas: SchemaRegistry) -> None:
        self._providers = providers
        self._schemas = schemas

    def validate_definition(self, agent: AgentDefinition) -> None:
        self._schemas.get(agent.input_schema)
        self._schemas.get(agent.output_schema)
        if agent.model.provider not in self._providers:
            raise RuntimeFault("unknown_provider")

    async def execute(
        self, agent: AgentDefinition, context: AgentContext, tools: ToolGateway, usage: Usage
    ) -> AgentResult:
        try:
            self._schemas.get(agent.input_schema).model_validate(context.inputs)
        except ValidationError as exc:
            raise RuntimeFault("invalid_agent_input") from exc
        output_type = self._schemas.get(agent.output_schema)
        request = ModelRequest(
            agent_id=agent.id,
            instruction=agent.instruction,
            context=context,
            config=agent.model.model_copy(deep=True),
            output_schema=output_type.model_json_schema(),
            tools=tools.descriptions(),
        )
        for _ in range(agent.execution.max_model_turns):
            # Count attempted calls even when a transport fails before returning usage.
            usage.model_calls += 1
            response = await self._providers[agent.model.provider].generate(request)
            usage.input_tokens += response.usage.input_tokens
            usage.output_tokens += response.usage.output_tokens
            usage.cost_usd += (
                response.usage.input_tokens * agent.model.input_cost_per_million
                + response.usage.output_tokens * agent.model.output_cost_per_million
            ) / 1_000_000
            if response.tool_calls:
                if response.output is not None:
                    raise RuntimeFault("ambiguous_model_response", retryable=True)
                for call in response.tool_calls:
                    result = await tools.invoke(call.name, call.arguments)
                    request.exchanges.append(ToolExchange(call=call, result=result))
                continue
            try:
                parsed = output_type.model_validate(response.output)
                output = parsed.model_dump(mode="json")
                uncertainty = Uncertainty.model_validate(output.get("uncertainty", {}))
            except ValidationError as exc:
                raise RuntimeFault("malformed_output", retryable=True) from exc
            # Check every nested evidence_ids field, not only the top-level summary.
            if not evidence_ids(output).issubset(context.evidence_scope()):
                raise RuntimeFault("unknown_evidence_reference")
            return AgentResult(
                status=Status.SUCCEEDED, output=output, uncertainty=uncertainty, usage=usage
            )
        raise RuntimeFault("model_turn_budget_exceeded")


def evidence_ids(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_ids" and isinstance(child, list):
                found.update(item for item in child if isinstance(item, str))
            else:
                found.update(evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(evidence_ids(child))
    return found
