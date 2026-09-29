"""Explicitly authorized recovery diagnostic; never reuses an old campaign."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from operational_recovery.live_diagnostic import prepare, run, verify_binding

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "verify", "run"])
    parser.add_argument("--approve-real", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "verify":
        print(verify_binding()["sha256"])
    else:
        if not args.approve_real:
            parser.error("Explicit real-launch approval is required")
        print(asyncio.run(run()))
