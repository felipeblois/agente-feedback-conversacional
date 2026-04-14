"""add openai to ai settings

Revision ID: c3d4e5f6a7b8
Revises: f1a2b3c4d5e6
Create Date: 2026-04-14 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_settings", sa.Column("openai_api_key", sa.Text(), nullable=True, server_default=""))
    op.add_column("ai_settings", sa.Column("openai_key_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_settings", "openai_key_updated_at")
    op.drop_column("ai_settings", "openai_api_key")
