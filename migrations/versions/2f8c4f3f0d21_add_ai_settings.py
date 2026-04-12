"""add ai settings

Revision ID: 2f8c4f3f0d21
Revises: d8960b572068
Create Date: 2026-04-10 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f8c4f3f0d21"
down_revision: Union[str, None] = "d8960b572068"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("credential_mode", sa.String(length=50), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("gemini_api_key", sa.Text(), nullable=False),
        sa.Column("anthropic_api_key", sa.Text(), nullable=False),
        sa.Column("default_provider", sa.String(length=50), nullable=False),
        sa.Column("default_model", sa.String(length=100), nullable=False),
        sa.Column("fallback_provider", sa.String(length=50), nullable=False),
        sa.Column("fallback_model", sa.String(length=100), nullable=False),
        sa.Column("enable_platform_fallback", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_settings")
