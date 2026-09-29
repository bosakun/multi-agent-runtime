"""Explicitly approved additive HotpotQA recovery; never resume an old campaign."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1]))

from hotpot_recovery import runner  # noqa: E402
from hotpot_recovery.analysis import analyze  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "mock", "bind", "verify", "run", "analyze"])
    parser.add_argument("--approve-real", action="store_true")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    if args.command == "plan":
        print(json.dumps({**runner.controls(), "work_grid": runner.work_grid()}, indent=2))
    elif args.command == "bind":
        asyncio.run(runner.bind())
        print(runner.verify_binding()["sha256"])
    elif args.command == "verify":
        print(runner.verify_binding()["sha256"])
    elif args.command == "analyze":
        print(analyze(mock=args.mock))
    else:
        if args.command == "run" and not args.approve_real:
            parser.error("Explicit real launch authorization required")
        path = asyncio.run(runner.execute(mock=args.command == "mock"))
        print(path)
        if not runner.load(path)["metadata"]["operational_integrity"]:
            raise SystemExit(2)
