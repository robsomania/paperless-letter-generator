"""Create sender_profiles table

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sender_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("street", sa.String(255), server_default=""),
        sa.Column("zip_city", sa.String(255), server_default=""),
        sa.Column("country", sa.String(255), server_default=""),
        sa.Column("email", sa.String(255), server_default=""),
        sa.Column("phone", sa.String(255), server_default=""),
        sa.Column("is_default", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table("letters") as batch_op:
        batch_op.add_column(sa.Column("sender_profile_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_letters_sender_profile", "sender_profiles", ["sender_profile_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("letters") as batch_op:
        batch_op.drop_constraint("fk_letters_sender_profile", type_="foreignkey")
        batch_op.drop_column("sender_profile_id")
    op.drop_table("sender_profiles")
