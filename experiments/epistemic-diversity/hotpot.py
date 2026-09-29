"""Active published HotpotQA benchmark. Download/prepare/plan/Mock never generate models."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1]))

from external_benchmarks.provenance import (  # noqa: E402
    BUNDLE,
    DATA,
    download,
    prepare,
    verify_bundle,
    verify_download,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "download",
            "prepare-data",
            "verify-download",
            "plan",
            "mock",
            "bind",
            "verify",
            "run",
            "analyze",
        ],
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--approve-real", action="store_true")
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="Explicit pinned HF mirror when original host is unavailable",
    )
    args = parser.parse_args()
    if args.command == "download":
        print(download(mirror=args.mirror))
    elif args.command == "verify-download":
        print(verify_download())
    elif args.command == "prepare-data":
        print(prepare(DATA / "hotpot_dev_distractor_v1.json"))
    elif args.command == "plan":
        from external_benchmarks.runner import controls

        manifest = verify_bundle() if (BUNDLE / "manifest.json").exists() else None
        print(
            json.dumps(
                {**controls(), "task_ids": manifest["task_ids"] if manifest else None}, indent=2
            )
        )
    else:
        from external_benchmarks.runner import (
            CAMPAIGN,
            MOCK,
            analyze,
            bind,
            execute,
            verify_binding,
        )

        if args.command == "mock":
            print(asyncio.run(execute(mock=True, output=args.output or MOCK)))
        elif args.command == "bind":
            asyncio.run(bind())
            print(verify_binding()["sha256"])
        elif args.command == "verify":
            print(verify_binding()["sha256"])
        elif args.command == "analyze":
            print(
                analyze(
                    args.input or CAMPAIGN / "pilot/results.json",
                    args.output or CAMPAIGN / "analysis",
                )
            )
        else:
            if not args.approve_real:
                parser.error("Explicit real launch authorization required")
            path = asyncio.run(execute())
            print(path)
            if not json.loads(path.read_text(encoding="utf-8"))["metadata"][
                "operational_integrity"
            ]:
                raise SystemExit(2)


if __name__ == "__main__":
    main()
