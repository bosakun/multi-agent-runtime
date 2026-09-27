"""Deterministic, scriptable provider for offline tests and experiments."""

import asyncio
from collections import defaultdict, deque
from collections.abc import Callable

from app.llm.provider import ModelRequest, ModelResponse

Responder = Callable[[ModelRequest], ModelResponse]


class MockProvider:
    def __init__(
        self, responder: Responder, *, delay_seconds: float = 0.01, capture: bool = False
    ) -> None:
        self.responder = responder
        self.delay_seconds = delay_seconds
        self.capture = capture
        self.requests: list[ModelRequest] = []
        self.scripts: dict[str, deque[ModelResponse | Exception]] = defaultdict(deque)
        self.active = 0
        self.max_active = 0

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if self.capture:
            self.requests.append(request.model_copy(deep=True))
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(self.delay_seconds)
            if self.scripts[request.agent_id]:
                value = self.scripts[request.agent_id].popleft()
                if isinstance(value, Exception):
                    raise value
                return value.model_copy(deep=True)
            return self.responder(request)
        finally:
            self.active -= 1
