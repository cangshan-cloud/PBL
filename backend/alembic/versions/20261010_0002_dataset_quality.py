"""add dataset quality metadata

Revision ID: 20261010_0002
Revises: 20261010_0001
Create Date: 2026-10-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261010_0002"
down_revision: Union[str, None] = "20261010_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dataset_versions", sa.Column("symbol_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("dataset_versions", sa.Column("source_filename", sa.String(255), nullable=False, server_default=""))
    op.add_column("dataset_versions", sa.Column("quality_report", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("dataset_versions", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("dataset_versions", "published_at")
    op.drop_column("dataset_versions", "quality_report")
    op.drop_column("dataset_versions", "source_filename")
    op.drop_column("dataset_versions", "symbol_count")

