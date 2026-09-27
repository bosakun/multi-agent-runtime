import os
import subprocess
import sys


def test_alembic_upgrade_and_schema_alignment(tmp_path):
    environment = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'migration.db'}"}
    for arguments in (["upgrade", "head"], ["check"]):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
