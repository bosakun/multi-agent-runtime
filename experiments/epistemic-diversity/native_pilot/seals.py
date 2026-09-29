"""Bind new controls without changing the 2.5 file inventory or historical seals."""

import hashlib

from epistemic.paths import REPO, ROOT
from prospective_pilot.seals import sources as previous_sources


def sources() -> dict[str, str]:
    files = previous_sources()
    paths = list((ROOT / "native_pilot").glob("*.py")) + [
        ROOT / "pilot26.py",
        ROOT / "docs/protocol-2.6-amendment.md",
        ROOT / "tests/test_pilot26.py",
        ROOT / "freezes/benchmark-2.0.0-protocol-2.5.json",
    ]
    files.update(
        {
            p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)
        }
    )
    return files
