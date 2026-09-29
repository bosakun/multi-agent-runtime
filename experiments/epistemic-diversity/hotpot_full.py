"""Complete HotpotQA 30 x five conditions, reusing rather than regenerating the Pilot."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1]))

from hotpot_main import data, runner  # noqa: E402
from hotpot_main.analysis import analyze  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["prepare-data", "plan", "mock", "bind", "verify", "run", "analyze"]
    )
    parser.add_argument("--approve-real", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare-data":
        print(data.prepare())
    elif args.command == "plan":
        print(
            json.dumps(
                {**runner.controls(), "task_ids": runner.verify_data()["task_ids"]}, indent=2
            )
        )
    elif args.command == "bind":
        asyncio.run(runner.bind())
        print(runner.verify_binding()["sha256"])
    elif args.command == "verify":
        print(runner.verify_binding()["sha256"])
    elif args.command == "analyze":
        print(
            analyze(
                args.input or runner.CAMPAIGN / "additional/results.json",
                args.output or runner.CAMPAIGN / "analysis",
            )
        )
    else:
        if args.command == "run" and not args.approve_real:
            parser.error("Explicit real launch authorization required")
        result = asyncio.run(runner.execute(mock=args.command == "mock"))
        print(result)
        if not json.loads(result.read_text(encoding="utf-8"))["metadata"]["operational_integrity"]:
            raise SystemExit(2)
