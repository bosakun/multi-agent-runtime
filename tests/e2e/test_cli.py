import json
import os
import subprocess
import sys

import pytest


def cli(database, *arguments):
    process = subprocess.run(
        [sys.executable, "-m", "app.cli", *arguments],
        env={
            **os.environ,
            "DATABASE_URL": f"sqlite+aiosqlite:///{database}",
            "MODEL_PROVIDER": "mock",
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return process


@pytest.mark.parametrize("workflow", ["investigation", "software_review"])
def test_documented_cli_run_and_inspect(tmp_path, workflow):
    database = tmp_path / "cli.db"
    executed = cli(database, "run", "--workflow", workflow, "--input", f"examples/{workflow}.json")
    result = json.loads(executed.stdout)
    assert result["status"] == "succeeded"
    assert "[START]" in executed.stderr and "[DONE]" in executed.stderr
    run_id = result["run_id"]
    assert "Artifacts:" in cli(database, "inspect", run_id).stdout
    assert "flowchart TD" in cli(database, "inspect", run_id, "--mermaid").stdout
    assert "uncertainty" in cli(database, "inspect", run_id, "--content").stdout
    assert "revision 1" in cli(database, "inspect", run_id, "--revision", "1").stdout


@pytest.mark.parametrize("decision", ["--approve", "--reject"])
def test_documented_cli_approval(tmp_path, decision):
    database = tmp_path / "cli.db"
    result = json.loads(
        cli(
            database,
            "run",
            "--workflow",
            "investigation",
            "--input",
            "examples/investigation.json",
            "--approval",
        ).stdout
    )
    assert result["status"] == "paused"
    resumed = json.loads(cli(database, "resume", result["run_id"], decision, "approval").stdout)
    assert resumed["status"] == "succeeded"


def test_documented_cli_cancel(tmp_path):
    database = tmp_path / "cli.db"
    result = json.loads(
        cli(
            database,
            "run",
            "--workflow",
            "investigation",
            "--input",
            "examples/investigation.json",
            "--approval",
        ).stdout
    )
    cancelled = json.loads(cli(database, "cancel", result["run_id"]).stdout)
    assert cancelled["status"] == "cancelled"
