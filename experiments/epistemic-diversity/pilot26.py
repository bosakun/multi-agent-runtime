"""Prospective native no-thinking Protocol 2.6, one diagnostic plus 48 Pilot calls."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1]))

from native_pilot.pilot26 import MOCK, execute, prepare, verify_binding  # noqa: E402
from native_pilot.recovery import prepare_diagnostic, run_diagnostic  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "mock",
            "diagnostic-prepare",
            "diagnostic",
            "prepare",
            "verify",
            "run",
        ],
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--approve-real", action="store_true")
    args = parser.parse_args()
    if args.command in {"run", "diagnostic"} and not args.approve_real:
        parser.error("Explicit real-launch approval required")
    if args.command == "mock":
        print(asyncio.run(execute(mock=True, mock_output=args.output or MOCK)))
    elif args.command == "diagnostic-prepare":
        asyncio.run(prepare_diagnostic())
    elif args.command == "diagnostic":
        print(asyncio.run(run_diagnostic()))
    elif args.command == "prepare":
        asyncio.run(prepare())
        print(verify_binding()["sha256"])
    elif args.command == "verify":
        print(verify_binding()["sha256"])
    else:
        path = asyncio.run(execute())
        print(path)
        if not json.loads(path.read_text(encoding="utf-8"))["metadata"]["operational_integrity"]:
            raise SystemExit(2)
