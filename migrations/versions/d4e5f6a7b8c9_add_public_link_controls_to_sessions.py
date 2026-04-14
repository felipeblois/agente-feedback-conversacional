"""add public link controls to sessions

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-14 16:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("public_link_enabled", sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column("sessions", sa.Column("public_link_expires_at", sa.DateTime(), nullable=True))
    op.add_column("sessions", sa.Column("public_link_revoked_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "public_link_revoked_at")
    op.drop_column("sessions", "public_link_expires_at")
    op.drop_column("sessions", "public_link_enabled")
