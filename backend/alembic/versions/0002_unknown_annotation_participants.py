"""Allow explicit unknown annotation participants.

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("annotation_participants", "player_id", existing_type=sa.Uuid(), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM annotation_participants WHERE player_id IS NULL")
    op.alter_column("annotation_participants", "player_id", existing_type=sa.Uuid(), nullable=False)
