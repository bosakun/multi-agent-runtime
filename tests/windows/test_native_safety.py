import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from host_support import commands, startup
from host_support.commands import NativeCommands


def test_native_command_argv_utf8_and_no_shell(tmp_path, monkeypatch):
    native = NativeCommands(tmp_path)
    monkeypatch.setattr(native, "which", lambda name: "C:/Program Files/Ollama/ollama.exe")

    def fake_run(args, **kwargs):
        assert args == ["C:/Program Files/Ollama/ollama.exe", "ps"]
        assert kwargs["shell"] is False and kwargs["timeout"] == 10
        assert kwargs["encoding"] == "utf-8" and kwargs["cwd"] == tmp_path
        assert kwargs["env"]["OLLAMA_HOST"] == "127.0.0.1:11434"
        return SimpleNamespace(returncode=0, stdout="observed\n")

    monkeypatch.setattr(commands.subprocess, "run", fake_run)
    assert native.run(["ollama", "ps"], env={"OLLAMA_HOST": "127.0.0.1:11434"}).output == "observed"


@pytest.mark.parametrize("failure", ["missing", "timeout", "oserror", "nonzero"])
def test_native_command_failure_is_bounded_and_redacted(tmp_path, monkeypatch, failure):
    native = NativeCommands(tmp_path)
    monkeypatch.setattr(native, "which", lambda name: None if failure == "missing" else name)

    def fake_run(args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args, 10, stderr="do-not-log")
        if failure == "oserror":
            raise OSError("do-not-log")
        return SimpleNamespace(returncode=1, stdout="do-not-log", stderr="do-not-log")

    monkeypatch.setattr(commands.subprocess, "run", fake_run)
    result = native.run(["ollama", "ps"])
    assert result.output is None and result.error
    assert "do-not-log" not in str(result)


@pytest.mark.parametrize("conflict", [False, True])
def test_port_socket_closed_and_conflict_stops(monkeypatch, conflict):
    sockets = []

    class FakeSocket:
        def __init__(self, *args):
            self.closed = False
            sockets.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

        def setsockopt(self, *args):
            pass

        def bind(self, address):
            assert address[1] == 11434 and address[0] in {"127.0.0.1", "::1"}
            if conflict:
                raise OSError("port in use")

    monkeypatch.setattr(startup.socket, "socket", FakeSocket)
    monkeypatch.setattr(startup.socket, "has_ipv6", True)
    assert startup.port_available() is not conflict
    assert all(s.closed for s in sockets)
    assert len(sockets) == (1 if conflict else 2)


def test_preservation_detects_changes_and_excludes_additions(tmp_path, monkeypatch):
    from scripts import audit_preservation as audit

    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "PROTECTED", ["historical"])
    folder = tmp_path / "historical"
    folder.mkdir()
    original = folder / "kept.json"
    original.write_text('{"value":1}', encoding="utf-8")
    baseline = audit.snapshot()
    assert "historical/kept.json" in baseline["files"]
    (folder / "new.json").write_text("{}", encoding="utf-8")
    assert audit.compare(baseline)["passed"]
    original.write_text('{"value":2}', encoding="utf-8")
    assert not audit.compare(baseline)["passed"]
    with pytest.raises(ValueError):
        audit.write_new(original, {})


def test_no_host_import_from_runtime():
    root = Path(__file__).resolve().parents[2]
    for source in (root / "app").rglob("*.py"):
        assert "host_support" not in source.read_text(encoding="utf-8")


def test_cli_has_no_research_command():
    root = Path(__file__).resolve().parents[2]
    source = (root / "experiments/epistemic-diversity/host.py").read_text(encoding="utf-8")
    assert '"pilot"' not in source and '"bind"' not in source
    assert '"resume"' not in source and '"generate"' not in source


def test_cli_checks_actual_environment_configuration(monkeypatch):
    import host

    monkeypatch.setenv("MODEL_BASE_URL", "http://wrong:11434/v1/")
    monkeypatch.setenv("MODEL_NAME", "wrong-model")
    monkeypatch.setattr("sys.argv", ["host.py", "preflight"])

    async def observe(args):
        assert args.endpoint == "http://wrong:11434/v1/" and args.model == "wrong-model"
        return 2

    monkeypatch.setattr(host, "execute", observe)
    with pytest.raises(SystemExit) as stopped:
        host.main()
    assert stopped.value.code == 2


def test_preservation_baseline_includes_old_campaigns():
    root = Path(__file__).resolve().parents[2]
    path = root / "reports/windows-support-preservation-before.json"
    if not path.exists():
        pytest.skip("Implementation-local preservation baseline is not distributed in Git")
    baseline = json.loads(path.read_text(encoding="utf-8"))
    for campaign in [
        "qwen3-14b/",
        "qwen3-14b-protocol22/",
        "qwen3-14b-protocol23/",
        "qwen3-14b-protocol24/",
    ]:
        assert any(f"/runs/{campaign}" in name for name in baseline["files"])
