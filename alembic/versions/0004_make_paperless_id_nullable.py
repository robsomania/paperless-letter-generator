"""Make paperless_id nullable in correspondent_profiles

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("correspondent_profiles") as batch_op:
        batch_op.alter_column("paperless_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("correspondent_profiles") as batch_op:
        batch_op.alter_column("paperless_id", existing_type=sa.Integer(), nullable=False)
