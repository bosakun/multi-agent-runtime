"""Record the non-live regression gate before sealing the implementation."""

import os
import subprocess
import sys
import uuid

from synthesis_study.io import REPO, STUDY, digest, exclusive
from synthesis_study.runner import code_hashes, now


def validate_offline():
    from synthesis_study.archival import archival_exceptions

    archival = archival_exceptions()
    validation_root = STUDY / "reports" / ("prelaunch-validation-" + uuid.uuid4().hex)
    environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    commands = [
        [sys.executable, "-X", "utf8", "-m", "ruff", "check", str(STUDY)],
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "pytest",
            "-q",
            "-rs",
            "tests",
            "experiments/epistemic-diversity/tests",
            str(STUDY / "tests"),
            "--ignore=tests/e2e/test_live_api.py",
        ],
    ]
    commands[-1].extend("--deselect=" + node for node in archival["deselected_archival_nodes"])
    print(
        "Archival scope exceptions retained: "
        f"{len(archival['deselected_archival_nodes'])} named nodes; "
        "old full suite is NOT claimed passing.",
        flush=True,
    )
    results = []
    for command in commands:
        with subprocess.Popen(
            command,
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=environment,
        ) as run:
            chunks = []
            assert run.stdout is not None
            for line in run.stdout:
                print(line, end="", flush=True)
                chunks.append(line)
            run.wait()
        text = "".join(chunks)
        results.append(
            {"command": command[1:], "exit_code": run.returncode, "output_sha256": digest(text)}
        )
        exclusive(validation_root / f"{len(results)}.txt", text, text=True)
        if run.returncode:
            raise ValueError("Offline validation failed; no seal or generation")
    report = {
        "created_at": now(),
        "passed": True,
        "live_api_tests_excluded": True,
        "archival_exceptions": archival,
        "report_root": validation_root.relative_to(REPO).as_posix(),
        "gate_scope": "current_Runtime_and_study_not_all_historical_campaigns",
        "code_hashes": code_hashes(),
        "commands": results,
    }
    exclusive(STUDY / "data/prelaunch-validation.json", report)
    return {"passed": True, "commands": len(results)}
