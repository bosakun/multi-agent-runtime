"""Prepare fully artificial v2 previews from existing synthetic materials only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3.html_display_v1.examples import synthetic_a  # noqa: E402
from review_v3.html_review_v2.renderer import build  # noqa: E402
from review_v3.storage import exclusive  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
PILOT_ROOT = (
    REPO
    / "experiments/synthesis-evidence-preservation/review_v3/local"
    / "pilot-materials-v1/prepared-20261006-002/pilot_b/reviewer_materials"
)


def prepare(destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Choose a new ignored-local preview directory")
    r1, r2, asset = synthetic_a()
    a_root = destination / "artificial-registry-tutorial"
    a_root.mkdir(parents=True)
    asset_path = a_root / "synthetic-translation.json"
    exclusive(asset_path, asset)
    for phase, source in (("R1", r1), ("R2", r2)):
        source_path = a_root / f"{phase}.synthetic.json"
        exclusive(source_path, source)
        build(source_path, phase, a_root / phase, asset_path)
    b_root = destination / "pilot-b-synthetic-training"
    for phase in ("S1", "S2", "S3", "S4", "S5"):
        build(PILOT_ROOT / f"{phase}.source.json", phase, b_root / phase)
    return destination


if __name__ == "__main__":
    prepare(sys.argv[1])
    print("Artificial previews prepared; no human labels or review started.")
