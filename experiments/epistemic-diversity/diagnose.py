"""Offline entry point; no model generation, resume, retry, or performance analysis."""

import argparse
from pathlib import Path

from operational_diagnostics.campaign import save_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", type=Path, help="Preserved campaign pilot directory")
    parser.add_argument("--output", type=Path, required=True, help="Fresh diagnostics directory")
    args = parser.parse_args()
    save_report(args.phase, args.output)


if __name__ == "__main__":
    main()
