"""Protocol 2.4 extension; does not modify the historical run.py entry point."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from operational_recovery.pilot24 import execute, prepare, verify_binding

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "verify", "mock", "run"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--approve-real", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "verify":
        print(verify_binding()["sha256"])
    elif args.command == "mock":
        print(asyncio.run(execute(mock=True, mock_output=args.output)))
    else:
        if not args.approve_real:
            parser.error("Explicit real-launch approval is required")
        print(asyncio.run(execute()))
