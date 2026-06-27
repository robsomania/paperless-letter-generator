"""Add attachments and attachment_watermark to letters

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("letters") as batch_op:
        batch_op.add_column(sa.Column("attachments", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("attachment_watermark", sa.Boolean(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("letters") as batch_op:
        batch_op.drop_column("attachment_watermark")
        batch_op.drop_column("attachments")
