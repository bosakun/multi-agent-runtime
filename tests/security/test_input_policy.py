from app.core.models import WorkflowState
from app.policies.context import ContextBuilder
from demos.catalog import configure


async def test_task_and_input_access_are_explicit(service, investigation_input):
    _, agents = configure("investigation", investigation_input)
    agent = agents["investigator_a"]
    agent.context.include_task = False
    agent.context.input_keys = ["allowed"]
    investigation_input.inputs = {"allowed": "public", "forbidden": "banana"}
    context = await ContextBuilder(service.repository).build_context(
        agent=agent, state=WorkflowState(task=investigation_input, nodes={}), run_id="r"
    )
    assert context.task is None
    assert context.inputs == {"allowed": "public"}
    assert "banana" not in context.model_dump_json()
