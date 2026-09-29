import json
from pathlib import Path, PureWindowsPath

import httpx
import pytest
from host_support import artifacts, hardware, startup
from host_support.artifacts import report_path, write_report
from host_support.commands import CIM_SCRIPT, PROCESS_SCRIPT, CommandResult
from host_support.hardware import capture_hardware, capture_runtime, parse_nvidia
from host_support.models import Fingerprint
from host_support.ollama import endpoint_root, inspect_ollama, residency
from host_support.preflight import capture
from host_support.smoke import smoke
from host_support.startup import startup_check

MODEL = "qwen3:14b"
DIGEST = "a" * 64
ENDPOINT = "http://127.0.0.1:11434/v1/"
REPOSITORY = Path(__file__).resolve().parents[2]


def gpu_xml(count=1):
    return (
        "<nvidia_smi_log><driver_version>570.0</driver_version><cuda_version>12.8</cuda_version>"
        + "".join(
            f"<gpu><product_name>RTX 4070 Ti {i}</product_name><uuid>GPU-{i}</uuid>"
            "<fb_memory_usage><total>12288 MiB</total></fb_memory_usage></gpu>"
            for i in range(count)
        )
        + "</nvidia_smi_log>"
    )


class FakeCommands:
    def __init__(self):
        self.missing = set()
        self.dirty = ""
        self.processes = "[]"
        self.smi = gpu_xml()
        self.ps = f"{MODEL}  abc123  11 GB  100% GPU  4096  Forever"
        self.calls = []

    def which(self, name):
        return None if name in self.missing else f"C:/Program Files/{name}.exe"

    def run(self, args, *, env=None):
        self.calls.append((args, env))
        if args[0] in self.missing:
            return CommandResult(None, "executable_unavailable")
        if args[-1] == CIM_SCRIPT:
            return CommandResult(
                json.dumps(
                    {"cpu": "Test CPU", "memory": 34359738368, "version": "10.0", "build": "26100"}
                )
            )
        if args[-1] == PROCESS_SCRIPT:
            return CommandResult(self.processes)
        if args == ["nvidia-smi", "-q", "-x"]:
            return CommandResult(self.smi)
        if args == ["ollama", "ps"]:
            assert env == {"OLLAMA_HOST": "http://127.0.0.1:11434"}
            return CommandResult(self.ps)
        if args == ["uv", "--version"]:
            return CommandResult("uv test")
        if args == ["git", "rev-parse", "HEAD"]:
            return CommandResult("b" * 40)
        if args == ["git", "branch", "--show-current"]:
            return CommandResult("research/epistemic-diversity")
        if args == ["git", "status", "--porcelain", "--untracked-files=normal"]:
            return CommandResult(self.dirty)
        raise AssertionError(f"Unapproved command {args}")


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.data = {
            "/api/version": {"version": "test-ollama"},
            "/api/tags": {
                "models": [{"name": MODEL, "model": MODEL, "digest": DIGEST, "size": 9000000000}]
            },
            "/api/show": {
                "details": {"quantization_level": "Q4_K_M"},
                "model_info": {"qwen3.context_length": 40960},
                "capabilities": [],
            },
            "/v1/models": {"data": [{"id": MODEL}]},
            "/api/ps": {
                "models": [
                    {
                        "name": MODEL,
                        "digest": DIGEST,
                        "size": 1000,
                        "size_vram": 1000,
                        "context_length": 4096,
                    }
                ]
            },
        }

    def respond(self, request):
        path = request.url.path
        assert path in self.data, "Generation or an unexpected endpoint was requested"
        assert request.method == ("POST" if path == "/api/show" else "GET")
        assert request.url.host == "127.0.0.1" and request.url.port == 11434
        if path == "/api/show":
            assert json.loads(request.content) == {"model": MODEL}
        self.calls.append(path)
        data = self.data[path]
        return httpx.Response(
            data if isinstance(data, int) else 200, json={} if isinstance(data, int) else data
        )

    @property
    def transport(self):
        return httpx.MockTransport(self.respond)


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(hardware.platform, "system", lambda: "Windows")
    monkeypatch.setattr(hardware.platform, "machine", lambda: "AMD64")
    return FakeCommands()


@pytest.mark.parametrize("count", [1, 2, 4])
def test_nvidia_multiple_adapters(count):
    cards = parse_nvidia(gpu_xml(count))
    assert len(cards) == count and len({g.uuid for g in cards}) == count
    assert all(g.vram_mb == 12288 for g in cards)
    assert all(
        g.driver_supported_cuda == "12.8" and g.installed_cuda_runtime is None for g in cards
    )


@pytest.mark.parametrize(
    "bad", ["", "bad XML", "<wrong/>", "<nvidia_smi_log><gpu/></nvidia_smi_log>", "<!ENTITY x 'x'>"]
)
def test_malformed_nvidia(bad):
    with pytest.raises(ValueError):
        parse_nvidia(bad)


@pytest.mark.parametrize("missing", ["nvidia-smi", "powershell.exe"])
def test_missing_hardware_tool(windows, missing):
    windows.missing.add(missing)
    host, _, memory, cards, checks = capture_hardware(windows)
    assert host.os == "Windows"
    if missing == "nvidia-smi":
        assert not cards and any(c.status == "fail" for c in checks)
    else:
        assert memory.total_bytes is None
        assert any(c.name == "windows_cim" and c.status == "warning" for c in checks)


def test_missing_vram_is_not_invented(windows):
    windows.smi = gpu_xml().replace("12288 MiB", "N/A")
    *_, cards, checks = capture_hardware(windows)
    assert cards[0].vram_mb is None
    assert next(c for c in checks if c.name == "vram").status == "fail"


@pytest.mark.parametrize("dirty", ["", " M something.py\n?? new.json"])
def test_git_clean_dirty(windows, dirty):
    windows.dirty = dirty
    runtime, _ = capture_runtime(windows)
    assert runtime.git_dirty is bool(dirty)
    assert runtime.git_commit == "b" * 40


def test_git_unavailable(windows):
    windows.missing.add("git")
    runtime, checks = capture_runtime(windows)
    assert runtime.git_dirty is None and runtime.git_commit is None
    assert next(c for c in checks if c.name == "git").status == "fail"


@pytest.mark.parametrize("url", ["http://localhost:11434", ENDPOINT])
def test_local_endpoint(url):
    assert endpoint_root(url).endswith(":11434/")


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/v1/",
        "http://remote:11434/v1/",
        "https://127.0.0.1:11434/",
        "http://127.0.0.1:11434/other",
        "http://user:secret@localhost:11434",
        "http://localhost:11434/?x=secret",
        "http://localhost:bad",
        "http://localhost:11434/#fragment",
    ],
)
async def test_reject_endpoint_before_http(windows, url):
    api = FakeAPI()
    _, checks = await inspect_ollama(windows, url, MODEL, transport=api.transport)
    assert not api.calls
    assert next(c for c in checks if c.name == "endpoint").status == "fail"
    assert "secret" not in str(checks)


async def test_fingerprint_roundtrip_and_metadata_reuse(windows):
    api = FakeAPI()
    result = await capture(windows, ENDPOINT, MODEL, DIGEST, transport=api.transport)
    assert result.passed and result.generation_calls == 0
    assert result.platform.build == "26100" and result.platform.architecture == "AMD64"
    assert result.memory.total_bytes == 34359738368
    assert result.ollama.quantization == "Q4_K_M"
    assert result.ollama.model_context_lengths == {"qwen3.context_length": 40960}
    assert result.ollama.model_size_bytes == 9000000000
    assert Fingerprint.model_validate_json(result.model_dump_json()) == result
    assert sorted(api.calls) == sorted(api.data)  # Exactly one metadata fetch per resource.


@pytest.mark.parametrize(
    "case", ["missing", "alias", "digest", "expected", "compatible", "malformed", "resident"]
)
async def test_wrong_model_identity(windows, case):
    api = FakeAPI()
    expected = DIGEST
    if case == "missing":
        api.data["/api/tags"]["models"] = []
    elif case == "alias":
        api.data["/api/tags"]["models"][0]["model"] = "qwen3:8b"
    elif case == "digest":
        api.data["/api/tags"]["models"][0]["digest"] = "short"
    elif case == "expected":
        expected = "c" * 64
    elif case == "compatible":
        api.data["/v1/models"] = {"data": [{"id": "qwen3:8b"}]}
    elif case == "malformed":
        api.data["/api/tags"] = {"models": None}
    else:
        api.data["/api/ps"]["models"][0]["digest"] = "c" * 64
    result = await capture(windows, ENDPOINT, MODEL, expected, transport=api.transport)
    assert not result.passed


async def test_ollama_unavailable(windows):
    def unavailable(request):
        raise httpx.ConnectError("offline", request=request)

    windows.missing.add("ollama")
    result = await capture(windows, ENDPOINT, MODEL, transport=httpx.MockTransport(unavailable))
    assert not result.passed
    assert result.ollama.version is None and result.ollama.digest is None
    assert result.ollama.residency.state == "unavailable"


@pytest.mark.parametrize(
    "vram,state", [(1000, "full_gpu"), (600, "partial_gpu"), (0, "cpu"), (None, "loaded_unknown")]
)
def test_residency_bytes_are_not_compute_percent(vram, state):
    data = {"models": [{"name": MODEL, "size": 1000, "size_vram": vram}]}
    observed = residency(data, None, MODEL)
    assert observed.state == state and observed.gpu_percent is None
    assert observed.context_length is None


@pytest.mark.parametrize(
    "processor,state,gpu",
    [("100% GPU", "full_gpu", 100), ("100% CPU", "cpu", 0), ("30%/70% CPU/GPU", "partial_gpu", 70)],
)
def test_cli_residency_fallback(processor, state, gpu):
    observed = residency(None, f"{MODEL}  id  11 GB  {processor}  4096", MODEL)
    assert observed.state == state and observed.gpu_percent == gpu
    assert observed.cpu_percent == 100 - gpu and observed.size_bytes is None


@pytest.mark.parametrize("data,state", [(None, "unavailable"), ({"models": []}, "not_loaded")])
def test_unavailable_residency(data, state):
    assert residency(data, None, MODEL).state == state


async def test_partial_offload_warns_without_altering_context(windows):
    api = FakeAPI()
    api.data["/api/ps"]["models"][0]["size_vram"] = 600
    windows.ps = f"{MODEL}  abc  11 GB  40%/60% CPU/GPU  4096"
    result = await capture(windows, ENDPOINT, MODEL, transport=api.transport)
    assert result.passed
    assert result.ollama.residency.state == "partial_gpu"
    assert next(c for c in result.checks if c.name == "gpu_residency").status == "warning"
    assert all(args[0] != "ollama" or args == ["ollama", "ps"] for args, _ in windows.calls)


@pytest.mark.parametrize(
    "processes,free,allowed",
    [
        ("[]", True, True),
        ('{"ProcessName":"ollama","Id":123}', True, False),
        ("[]", False, False),
        ("broken", True, False),
        (None, True, False),
    ],
)
def test_startup_process_and_port_guards(windows, processes, free, allowed):
    windows.processes = processes
    assert startup_check(windows, port_probe=lambda: free)["allowed"] is allowed
    assert len(windows.calls) == 1 and windows.calls[0][0][-1] == PROCESS_SCRIPT


def test_startup_nonwindows_rejected(windows, monkeypatch):
    monkeypatch.setattr(startup.platform, "system", lambda: "Darwin")
    assert not startup_check(windows, port_probe=lambda: True)["allowed"]
    assert not windows.calls


def test_report_windows_paths_and_no_overwrite(tmp_path):
    root = tmp_path / "repo 日本語 spaces"
    target = report_path(root, "fingerprint")
    assert ":" not in PureWindowsPath(target.name).name
    data = {"cpu": "実機", "unknown": None}
    assert write_report(root, target, data) == target
    assert json.loads(target.read_text(encoding="utf-8")) == data
    with pytest.raises(FileExistsError):
        write_report(root, target, {"bad": True})
    assert json.loads(target.read_text(encoding="utf-8")) == data
    assert not list(target.parent.glob("*.tmp"))


def test_reports_cannot_touch_campaign(tmp_path):
    with pytest.raises(ValueError):
        write_report(tmp_path, tmp_path / "experiments/epistemic-diversity/runs/old/new.json", {})


def test_report_sharing_violation_no_partial_output(tmp_path, monkeypatch):
    target = report_path(tmp_path, "fingerprint")

    def denied(source, destination):
        # The writer's handle is already closed before publishing.
        with Path(source).open("rb") as handle:
            assert json.load(handle) == {"saved": True}
        raise PermissionError("simulated Windows sharing violation")

    monkeypatch.setattr(artifacts.os, "link", denied)
    with pytest.raises(PermissionError):
        write_report(tmp_path, target, {"saved": True})
    assert not target.exists() and not list(target.parent.glob("*.tmp"))


async def test_mock_smoke_never_uses_real_provider(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("MODEL_NAME", MODEL)
    result = await smoke(REPOSITORY)
    assert result["passed"] and result["generation_calls"] == 0
    assert result["provider"] == "mock" and result["mock_calls"] == 6
    assert result["sqlite_closed_handle_check"] == "passed"


def test_powershell_scripts_static_contract():
    scripts = REPOSITORY / "scripts/windows"
    start = (scripts / "start-ollama-research.ps1").read_text()
    assert start.index("startup-check") < start.index("& ollama serve")
    assert "$env:OLLAMA_NUM_PARALLEL = '1'" in start
    assert "$env:OLLAMA_MAX_LOADED_MODELS = '1'" in start
    for path in scripts.glob("*.ps1"):
        text = path.read_text()
        assert "Stop-Process" not in text and "taskkill" not in text
        assert "pilot24.py" not in text and "--provider real" not in text
