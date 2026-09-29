"""Independent diagnostic commands; the research pilot CLI and freeze are unchanged."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from operational_diagnostics.budget_experiment import (
    PLAN_ROOT,
    ROOT,
    prepare,
    read,
    run_campaign,
    verify_binding,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "verify", "run"])
    parser.add_argument("--approve-real", action="store_true")
    args = parser.parse_args()
    plan = read(PLAN_ROOT / "plan.json")
    seal_path, campaign = ROOT / plan["future_seal"], ROOT / plan["future_campaign"]
    if args.command == "prepare":
        prepare(seal_path, campaign)
    elif args.command == "verify":
        print(verify_binding(seal_path, campaign)["seal_sha256"])
    else:
        if not args.approve_real:
            parser.error("Real generation requires explicit --approve-real and human authorization")
        print(asyncio.run(run_campaign(seal_path, campaign)))


if __name__ == "__main__":
    main()
