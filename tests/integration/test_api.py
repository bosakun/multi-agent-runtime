import asyncio

import httpx

from app.api.main import create_app


async def wait_terminal(client, run_id):
    async with asyncio.timeout(5):
        while True:
            response = await client.get(f"/runs/{run_id}")
            data = response.json()
            if data["status"] not in {"pending", "running"}:
                return data
            await asyncio.sleep(0.01)


async def test_api_submit_read_events_graph_and_approval(service, investigation_input):
    api = create_app(service)
    async with (
        api.router.lifespan_context(api),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as client,
    ):
        response = await client.post(
            "/runs",
            json={
                "workflow": "investigation",
                "input": investigation_input.model_dump(mode="json"),
                "approval": True,
            },
        )
        assert response.status_code == 202
        run_id = response.json()["id"]
        paused = await wait_terminal(client, run_id)
        assert paused["status"] == "paused"
        assert "task" not in paused and "knowledge" not in paused
        approval = await client.post(f"/runs/{run_id}/approvals/approval", json={"approved": True})
        assert approval.status_code == 200
        assert (await client.post(f"/runs/{run_id}/resume")).status_code == 202
        for _ in range(200):
            completed = (await client.get(f"/runs/{run_id}")).json()
            if completed["status"] == "succeeded":
                break
            await asyncio.sleep(0.01)
        assert completed["status"] == "succeeded" and completed["final_results"]
        assert (await client.get(f"/runs/{run_id}/events")).json()[-1]["kind"] == "RUN_COMPLETED"
        assert "flowchart TD" in (await client.get(f"/runs/{run_id}/graph")).json()["mermaid"]
        assert len((await client.get("/agents")).json()) == 11
        assert len((await client.get("/workflows")).json()) == 2
        assert (await client.get("/runs/missing")).status_code == 404


async def test_invalid_api_input_does_not_echo_private_values(service):
    api = create_app(service)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api), base_url="http://test"
    ) as client:
        response = await client.post(
            "/runs", json={"workflow": "investigation", "input": {"task": {"SECRET": "private"}}}
        )
        assert response.status_code == 422
        assert "SECRET" not in response.text and "private" not in response.text
        response = await client.post("/runs", json={"workflow": "unknown", "input": {"task": "x"}})
        assert response.status_code == 404
