"""Repository-root entrypoint for the independent experiment package."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from epistemic.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
