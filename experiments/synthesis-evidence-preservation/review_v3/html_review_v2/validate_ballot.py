"""Validate an exported, untouched v3 form or Registry ballot."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3.html_review_v2.renderer import validate_export  # noqa: E402
from review_v3.storage import read  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ballot", required=True)
    parser.add_argument(
        "--phase", required=True, choices=("R1", "R2", "S1", "S2", "S3", "S4", "S5")
    )
    args = parser.parse_args()
    validate_export(read(args.ballot), args.phase)
    print(json.dumps({"valid": True, "phase": args.phase}, ensure_ascii=False))
