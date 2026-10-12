"""add run logs and cooperative cancellation

Revision ID: 20261010_0004
Revises: 20261010_0003
Create Date: 2026-10-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261010_0004"
down_revision: Union[str, None] = "20261010_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch:
        batch.add_column(sa.Column("cancellation_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "run_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("event", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_run_logs_run_id", "run_logs", ["run_id"])


def downgrade() -> None:
    op.drop_table("run_logs")
    with op.batch_alter_table("runs") as batch:
        batch.drop_column("cancellation_requested_at")
