import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[1]
sys.path[:0] = [
    str(STUDY / "src"),
    str(REPO),
    str(REPO / "experiments/epistemic-diversity"),
    str(REPO / "experiments/epistemic-diversity/src"),
]
