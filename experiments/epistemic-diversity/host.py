"""Native host preparation only. There is deliberately no research-run command."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parent
REPOSITORY = EXPERIMENT.parents[1]
sys.path.insert(0, str(EXPERIMENT / "src"))
sys.path.insert(0, str(REPOSITORY))

from host_support.artifacts import report_path, write_report  # noqa: E402
from host_support.commands import NativeCommands  # noqa: E402
from host_support.ollama import inspect_ollama  # noqa: E402
from host_support.preflight import capture  # noqa: E402
from host_support.smoke import smoke  # noqa: E402
from host_support.startup import startup_check  # noqa: E402


async def execute(args: argparse.Namespace) -> int:
    commands = NativeCommands(REPOSITORY)
    if args.command == "startup-check":
        data = await asyncio.to_thread(startup_check, commands)
        print(json.dumps(data, indent=2))
        return 0 if data["allowed"] else 2
    if args.command == "smoke":
        data = await smoke(REPOSITORY)
        passed = data["passed"]
    elif args.command == "inspect":
        info, checks = await inspect_ollama(
            commands, args.endpoint, args.model, args.expected_digest
        )
        data = {
            "ollama": info.model_dump(),
            "checks": [c.model_dump() for c in checks],
            "generation_calls": 0,
        }
        passed = all(c.status != "fail" for c in checks)
    else:
        fingerprint = await capture(commands, args.endpoint, args.model, args.expected_digest)
        data = fingerprint.model_dump()
        passed = fingerprint.passed
    path = await asyncio.to_thread(
        write_report, REPOSITORY, args.output or report_path(REPOSITORY, args.command), data
    )
    print(json.dumps({"passed": passed, "report": str(path), "observations": data}, indent=2))
    return 0 if passed else 2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["preflight", "fingerprint", "inspect", "startup-check", "smoke"]
    )
    parser.add_argument(
        "--endpoint", default=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:11434/v1/")
    )
    parser.add_argument("--model", default=os.environ.get("MODEL_NAME", "qwen3:14b"))
    parser.add_argument("--expected-digest")
    parser.add_argument("--output", type=Path, help="New path inside reports/windows-host only")
    args = parser.parse_args()
    try:
        code = asyncio.run(execute(args))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Host check stopped: {type(exc).__name__}: {exc}\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
