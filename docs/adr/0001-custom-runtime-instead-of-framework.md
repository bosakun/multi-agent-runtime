# ADR 0001: Implement the runtime directly

Status: accepted.

The portfolio must expose scheduling, authority and state transitions. Build a
small asyncio DAG scheduler rather than adopting LangGraph, CrewAI, AutoGen or
LangChain Agents. This makes the boundaries auditable and the experiments
controllable. The cost is owning cancellation, retries and persistence semantics.
Distributed workers and dynamic planning remain out of scope.
