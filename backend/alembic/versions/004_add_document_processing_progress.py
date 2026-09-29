"""Add progress tracking to document processing.

Revision ID: 004_add_document_processing_progress
Revises: 003_schema_reconciliation
Create Date: 2026-09-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_add_document_processing_progress"
down_revision: Union[str, None] = "003_schema_reconciliation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "document_processing",
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("document_processing", "progress")
