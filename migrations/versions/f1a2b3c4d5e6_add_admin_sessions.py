"""add admin sessions

Revision ID: f1a2b3c4d5e6
Revises: b91e4a6d2c11
Create Date: 2026-04-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "b91e4a6d2c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_username", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_sessions_actor_username"), "admin_sessions", ["actor_username"], unique=False)
    op.create_index(op.f("ix_admin_sessions_expires_at"), "admin_sessions", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_sessions_expires_at"), table_name="admin_sessions")
    op.drop_index(op.f("ix_admin_sessions_actor_username"), table_name="admin_sessions")
    op.drop_table("admin_sessions")
