"""add session briefing fields

Revision ID: 6c8b0e5f4a12
Revises: 2f8c4f3f0d21
Create Date: 2026-04-11 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c8b0e5f4a12"
down_revision: Union[str, None] = "2f8c4f3f0d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("theme_summary", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("session_goal", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("target_audience", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("topics_to_explore", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("ai_guidance", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "ai_guidance")
    op.drop_column("sessions", "topics_to_explore")
    op.drop_column("sessions", "target_audience")
    op.drop_column("sessions", "session_goal")
    op.drop_column("sessions", "theme_summary")
