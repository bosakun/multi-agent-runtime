"""Exercise the real transport path using only in-process fake HTTP responses."""

import copy
import ctypes
import json
import os
from pathlib import Path

import httpx
import pytest
from synthesis_study import runner
from synthesis_study.io import STUDY, digest, exclusive, file_hash, read
from synthesis_study.tokenizer import TEMPLATE_DIGEST


@pytest.fixture
def fake_study(tmp_path, monkeypatch):
    manifest = read(STUDY / "data/replay-inputs/manifest.json")
    exclusive(tmp_path / "data/replay-inputs/manifest.json", manifest)
    exclusive(tmp_path / "freezes/v1.json", {"test_only": True})
    exclusive(
        tmp_path / "data/binding.json", {"freeze_sha256": file_hash(tmp_path / "freezes/v1.json")}
    )
    monkeypatch.setattr(runner, "STUDY", tmp_path)
    monkeypatch.setattr(runner, "verify_seal", lambda: {"test_only": True})
    monkeypatch.setattr(runner, "fingerprint", lambda *_: {"transport": "fake"})
    return tmp_path, manifest


@pytest.mark.parametrize("failure", [None, "timeout", "unknown_id"])
def test_http_path_is_bounded_and_fail_stops(fake_study, monkeypatch, failure):
    root, manifest = fake_study
    sent = []
    original_client = httpx.Client
    bodies = {p["body_sha256"]: p for p in manifest["calls"]}

    def transport(request):
        if request.url.path == "/api/ps":
            return httpx.Response(200, json={"models": []})
        assert request.url.path == "/api/chat" and request.method == "POST"
        body = json.loads(request.content)
        sent.append(body)
        planned = bodies[digest(body)]
        if len(sent) == 2 and failure == "timeout":
            raise httpx.ReadTimeout("fake timeout", request=request)
        response = runner.mock_response(planned)
        if len(sent) == 2 and failure == "unknown_id":
            payload = json.loads(response["message"]["content"])
            payload["evidence_ids"] = ["unauthorized"]
            response["message"]["content"] = json.dumps(payload)
        return httpx.Response(200, json=response)

    def client(**kwargs):
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
        return original_client(transport=httpx.MockTransport(transport), **kwargs)

    monkeypatch.setattr(runner.httpx, "Client", client)
    campaign = root / "runs/fake-http"
    if failure:
        with pytest.raises(ValueError, match="failed; original records retained"):
            runner.replay(mock=False, campaign=campaign)
    else:
        assert runner.replay(mock=False, campaign=campaign) == campaign
    result = read(campaign / "results.json")
    expected = 2 if failure else 81
    assert len(sent) == result["reservations"] == len(result["records"]) == expected
    assert result["status"] == ("failed" if failure else "completed")
    assert result["new_worker_calls"] == 0
    assert result["source_preservation"]["passed"]
    assert (campaign / "smoke-gate.json").exists() is (failure is None)
    with pytest.raises(ValueError, match="already exists"):
        runner.replay(mock=False, campaign=root / "runs/forbidden-retry")
    assert len(sent) == expected


@pytest.mark.parametrize("mutation", ["version", "digest", "template"])
def test_backend_drift_refused_before_generation(mutation):
    spec = read(STUDY / "study.json")
    template = Path.home() / ".ollama/models/blobs" / ("sha256-" + TEMPLATE_DIGEST)
    routes = {
        "/api/version": {"version": spec["generation"]["ollama_version"]},
        "/api/tags": {
            "models": [
                {"name": spec["generation"]["model"], "digest": spec["generation"]["model_digest"]}
            ]
        },
        "/api/show": {"template": template.read_text(encoding="utf-8"), "details": {}},
        "/api/ps": {"models": []},
    }
    routes = copy.deepcopy(routes)
    if mutation == "version":
        routes["/api/version"]["version"] = "wrong"
    elif mutation == "digest":
        routes["/api/tags"]["models"][0]["digest"] = "wrong"
    else:
        routes["/api/show"]["template"] = "wrong"

    def transport(request):
        assert request.url.path in routes  # Never a generation endpoint.
        return httpx.Response(200, json=routes[request.url.path])

    with httpx.Client(base_url=runner.ENDPOINT, transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(ValueError, match="drift"):
            runner.fingerprint(client, spec)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows sharing lock")
def test_native_windows_shared_lock_and_handle_release(tmp_path):
    target = tmp_path / "owned-lock-test.txt"
    target.write_text("temporary test data", encoding="utf-8")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    create.restype = ctypes.c_void_p
    close = kernel.CloseHandle
    close.argtypes = [ctypes.c_void_p]
    close.restype = ctypes.c_int
    handle = create(str(target), 0x80000000, 0, None, 3, 0x80, None)
    assert handle not in (None, ctypes.c_void_p(-1).value)
    try:
        with pytest.raises(OSError) as error:
            target.unlink()
        assert error.value.winerror == 32
        assert target.exists()
    finally:
        assert close(handle)
    target.rename(tmp_path / "closed-lock-test.txt")
    (tmp_path / "closed-lock-test.txt").unlink()
