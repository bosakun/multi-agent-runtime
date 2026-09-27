"""Initial runtime storage, intentionally independent of mutable app metadata."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
    )
    for name, counter in (("events", "sequence"), ("snapshots", "revision")):
        op.create_table(
            name,
            sa.Column("run_id", sa.String(64), primary_key=True),
            sa.Column(counter, sa.Integer, primary_key=True),
            sa.Column("payload", sa.JSON, nullable=False),
        )
    op.create_table(
        "definitions",
        sa.Column("kind", sa.String(32), primary_key=True),
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("payload", sa.JSON, nullable=False),
    )
    op.create_table(
        "projections",
        sa.Column("run_id", sa.String(64), primary_key=True),
        sa.Column("kind", sa.String(32), primary_key=True),
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("payload", sa.JSON, nullable=False),
    )
    op.create_table(
        "memories",
        sa.Column("scope", sa.String(16), primary_key=True),
        sa.Column("namespace", sa.String(160), primary_key=True),
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("payload", sa.JSON, nullable=False),
    )


def downgrade() -> None:
    for table in ("memories", "projections", "definitions", "snapshots", "events", "runs"):
        op.drop_table(table)
