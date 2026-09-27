import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest


@pytest.mark.skipif(not os.getenv("TEST_API_URL"), reason="Set TEST_API_URL for a live server")
@pytest.mark.parametrize("workflow", ["investigation", "software_review"])
async def test_live_server(workflow):
    content = await asyncio.to_thread(Path(f"examples/{workflow}.json").read_text)
    async with httpx.AsyncClient(base_url=os.environ["TEST_API_URL"]) as client:
        submitted = await client.post(
            "/runs", json={"workflow": workflow, "input": json.loads(content)}
        )
        assert submitted.status_code == 202
        run_id = submitted.json()["id"]
        async with asyncio.timeout(15):
            for _ in range(300):
                result = (await client.get(f"/runs/{run_id}")).json()
                if result["status"] in {"succeeded", "failed", "partial"}:
                    break
                await asyncio.sleep(0.02)
        assert result["status"] == "succeeded" and result["final_results"]
        assert (await client.get(f"/runs/{run_id}/events")).json()
        assert (
            (await client.get(f"/runs/{run_id}/graph")).json()["mermaid"].startswith("flowchart TD")
        )
