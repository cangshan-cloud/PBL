"""add users and experiment ownership

Revision ID: 20261010_0003
Revises: 20261010_0002
Create Date: 2026-10-10
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261010_0003"
down_revision: Union[str, None] = "20261010_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(300), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    with op.batch_alter_table("experiments") as batch:
        batch.add_column(sa.Column("created_by_id", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_experiments_created_by", "users", ["created_by_id"], ["id"])
        batch.create_index("ix_experiments_created_by_id", ["created_by_id"])


def downgrade() -> None:
    with op.batch_alter_table("experiments") as batch:
        batch.drop_index("ix_experiments_created_by_id")
        batch.drop_constraint("fk_experiments_created_by", type_="foreignkey")
        batch.drop_column("created_by_id")
    op.drop_table("users")
