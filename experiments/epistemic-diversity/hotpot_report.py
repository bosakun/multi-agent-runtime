"""Offline report from a completed HotpotQA cohort; no model generation."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1]))

from external_benchmarks.provenance import BUNDLE  # noqa: E402
from hotpot_reporting.report import create  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, default=BUNDLE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(create(args.input, args.bundle, args.output))
