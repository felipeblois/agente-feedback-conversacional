"""add admin users and session actor

Revision ID: b91e4a6d2c11
Revises: 8d4f1a2b7c90
Create Date: 2026-04-13 10:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b91e4a6d2c11"
down_revision = "8d4f1a2b7c90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_admin_users_username", "admin_users", ["username"], unique=True)

    op.add_column("sessions", sa.Column("created_by_admin_username", sa.String(length=255), nullable=True))
    op.add_column("sessions", sa.Column("updated_by_admin_username", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "updated_by_admin_username")
    op.drop_column("sessions", "created_by_admin_username")
    op.drop_index("ix_admin_users_username", table_name="admin_users")
    op.drop_table("admin_users")
