"""New layer hashes include both immutable earlier prospective implementations."""

import hashlib

from epistemic.paths import REPO, ROOT
from native_pilot.seals import sources as previous_sources


def sources() -> dict[str, str]:
    files = previous_sources()
    paths = list((ROOT / "bounded_pilot").glob("*.py")) + [
        ROOT / "pilot27.py",
        ROOT / "docs/protocol-2.7-amendment.md",
        ROOT / "tests/test_pilot27.py",
        ROOT / "freezes/benchmark-2.0.0-protocol-2.6.json",
    ]
    files.update(
        {
            p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)
        }
    )
    return files
