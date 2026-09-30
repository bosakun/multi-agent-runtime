"""Native Windows entrypoint; the old frozen study is imported read-only."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [
    str(HERE / "src"),
    str(ROOT),
    str(ROOT / "experiments/epistemic-diversity"),
    str(ROOT / "experiments/epistemic-diversity/src"),
]

from synthesis_study.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
