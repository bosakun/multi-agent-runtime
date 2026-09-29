"""Host reports are separate from campaigns and published without overwriting any file."""

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def report_path(repository: Path, kind: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return repository / "reports" / "windows-host" / f"{kind}-{stamp}-{uuid4().hex}.json"


def write_report(repository: Path, path: Path, data: dict[str, Any]) -> Path:
    """Publish a closed, fsynced sibling file with an atomic no-clobber hard link.

    NTFS/APFS/ext4 support this operation. Unsupported filesystems fail explicitly;
    do not fall back to replace(), which could destroy an existing observation.
    """
    destination = path.resolve()
    reports = (repository / "reports" / "windows-host").resolve()
    if not destination.is_relative_to(reports):
        raise ValueError("Host reports must be inside reports/windows-host (not research assets)")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination
