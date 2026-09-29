"""Host observations cannot select tasks, bind a campaign, or generate model output."""

import asyncio
from datetime import UTC, datetime

import httpx

from host_support.commands import Commands
from host_support.hardware import capture_hardware, capture_runtime
from host_support.models import Fingerprint
from host_support.ollama import inspect_ollama


async def capture(
    commands: Commands,
    endpoint: str,
    model: str,
    expected_digest: str | None = None,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> Fingerprint:
    host, cpu, memory, cards, hardware_checks = await asyncio.to_thread(capture_hardware, commands)
    runtime, runtime_checks = await asyncio.to_thread(capture_runtime, commands)
    ollama, ollama_checks = await inspect_ollama(
        commands, endpoint, model, expected_digest, transport=transport
    )
    return Fingerprint(
        captured_at=datetime.now(UTC).isoformat(),
        platform=host,
        cpu=cpu,
        memory=memory,
        gpu=cards,
        gpu_count=len(cards) if cards else None,
        ollama=ollama,
        runtime=runtime,
        checks=[*hardware_checks, *runtime_checks, *ollama_checks],
    )
