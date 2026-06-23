"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "correspondent_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("paperless_id", sa.Integer(), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("salutation", sa.String(50), server_default=""),
        sa.Column("company", sa.String(255), server_default=""),
        sa.Column("street", sa.String(255), server_default=""),
        sa.Column("zip_city", sa.String(255), server_default=""),
        sa.Column("country", sa.String(255), server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "latex_templates",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("latex_source", sa.Text(), nullable=False),
        sa.Column("variable_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "letters",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("latex_templates.id"), nullable=False),
        sa.Column("correspondent_profile_id", sa.Integer(), sa.ForeignKey("correspondent_profiles.id"), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("paperless_document_id", sa.String(255), nullable=True),
        sa.Column("version_group_id", sa.Integer(), nullable=True),
        sa.Column("field_values", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("letters")
    op.drop_table("latex_templates")
    op.drop_table("correspondent_profiles")
