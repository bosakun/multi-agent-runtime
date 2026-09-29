"""Prospective Windows Protocol 2.5. Only a fresh 48-call C2/C3 Pilot is enabled."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1]))

from prospective_pilot.pilot25 import MOCK, execute, prepare, verify_binding  # noqa: E402
from prospective_pilot.seals import verify_historical  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["historical", "mock", "prepare", "verify", "run"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--approve-real", action="store_true")
    args = parser.parse_args()
    if args.command == "historical":
        print(verify_historical()["freeze_sha256"])
    elif args.command == "prepare":
        asyncio.run(prepare())
        print(verify_binding()["sha256"])
    elif args.command == "verify":
        print(verify_binding()["sha256"])
    elif args.command == "mock":
        print(asyncio.run(execute(mock=True, mock_output=args.output or MOCK)))
    else:
        if not args.approve_real:
            parser.error("Explicit real-launch approval is required")
        path = asyncio.run(execute())
        print(path)
        if not json.loads(path.read_text(encoding="utf-8"))["metadata"]["operational_integrity"]:
            raise SystemExit(2)
