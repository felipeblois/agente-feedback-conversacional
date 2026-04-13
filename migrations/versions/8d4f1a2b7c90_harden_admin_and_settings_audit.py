"""harden admin and settings audit

Revision ID: 8d4f1a2b7c90
Revises: 6c8b0e5f4a12
Create Date: 2026-04-13 09:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8d4f1a2b7c90"
down_revision = "6c8b0e5f4a12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_settings", sa.Column("gemini_key_updated_at", sa.DateTime(), nullable=True))
    op.add_column("ai_settings", sa.Column("anthropic_key_updated_at", sa.DateTime(), nullable=True))

    op.create_table(
        "settings_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("area", sa.String(length=100), nullable=False, server_default="ai_settings"),
        sa.Column("action", sa.String(length=100), nullable=False, server_default="update"),
        sa.Column("actor", sa.String(length=255), nullable=False, server_default="admin"),
        sa.Column("instance_id", sa.String(length=100), nullable=False, server_default="local-default"),
        sa.Column("details", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("settings_audit_logs")
    op.drop_column("ai_settings", "anthropic_key_updated_at")
    op.drop_column("ai_settings", "gemini_key_updated_at")
