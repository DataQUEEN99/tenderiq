"""Add AI output tables and document processing tables

Revision ID: 002_ai_output_doc_processing
Revises: 001_initial
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_ai_output_doc_processing'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create document_contents table
    op.create_table(
        'document_contents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('char_count', sa.Integer(), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', name='uq_document_contents_document_id')
    )
    op.create_index(op.f('ix_document_contents_document_id'), 'document_contents', ['document_id'], unique=True)

    # Create document_processing table
    op.create_table(
        'document_processing',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('Uploading', 'Processing', 'Processed', 'Failed', 'Deleted', name='documentstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('vector_collection', sa.String(length=100), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', name='uq_document_processing_document_id')
    )
    op.create_index(op.f('ix_document_processing_document_id'), 'document_processing', ['document_id'], unique=True)

    # Create tender_summaries table
    op.create_table(
        'tender_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('generation_model', sa.String(length=100), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tender_id', name='uq_tender_summaries_tender_id')
    )
    op.create_index(op.f('ix_tender_summaries_tender_id'), 'tender_summaries', ['tender_id'], unique=True)
    op.create_index(op.f('ix_tender_summaries_organization_id'), 'tender_summaries', ['organization_id'], unique=False)

    # Create eligibility_analyses table
    op.create_table(
        'eligibility_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_eligible', sa.Boolean(), nullable=False),
        sa.Column('eligibility_score', sa.Integer(), nullable=True),
        sa.Column('mandatory_requirements', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('optional_requirements', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('gaps', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('generation_model', sa.String(length=100), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['company_profile_id'], ['company_profiles.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tender_id', name='uq_eligibility_analyses_tender_id')
    )
    op.create_index(op.f('ix_eligibility_analyses_tender_id'), 'eligibility_analyses', ['tender_id'], unique=True)
    op.create_index(op.f('ix_eligibility_analyses_organization_id'), 'eligibility_analyses', ['organization_id'], unique=False)
    op.create_index(op.f('ix_eligibility_analyses_company_profile_id'), 'eligibility_analyses', ['company_profile_id'], unique=False)

    # Create compliance_matrices table
    op.create_table(
        'compliance_matrices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('proposal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('compliance_score', sa.Integer(), nullable=False),
        sa.Column('requirements', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('non_compliant_items', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('partially_compliant_items', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('generation_model', sa.String(length=100), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id']),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tender_id', name='uq_compliance_matrices_tender_id')
    )
    op.create_index(op.f('ix_compliance_matrices_tender_id'), 'compliance_matrices', ['tender_id'], unique=True)
    op.create_index(op.f('ix_compliance_matrices_organization_id'), 'compliance_matrices', ['organization_id'], unique=False)
    op.create_index(op.f('ix_compliance_matrices_proposal_id'), 'compliance_matrices', ['proposal_id'], unique=False)

    # Create company_documents table
    op.create_table(
        'company_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('company_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['company_profile_id'], ['company_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_documents_company_profile_id'), 'company_documents', ['company_profile_id'], unique=False)
    op.create_index(op.f('ix_company_documents_document_id'), 'company_documents', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_company_documents_document_id'), table_name='company_documents')
    op.drop_index(op.f('ix_company_documents_company_profile_id'), table_name='company_documents')
    op.drop_table('company_documents')

    op.drop_index(op.f('ix_compliance_matrices_proposal_id'), table_name='compliance_matrices')
    op.drop_index(op.f('ix_compliance_matrices_organization_id'), table_name='compliance_matrices')
    op.drop_index(op.f('ix_compliance_matrices_tender_id'), table_name='compliance_matrices')
    op.drop_table('compliance_matrices')

    op.drop_index(op.f('ix_eligibility_analyses_company_profile_id'), table_name='eligibility_analyses')
    op.drop_index(op.f('ix_eligibility_analyses_organization_id'), table_name='eligibility_analyses')
    op.drop_index(op.f('ix_eligibility_analyses_tender_id'), table_name='eligibility_analyses')
    op.drop_table('eligibility_analyses')

    op.drop_index(op.f('ix_tender_summaries_organization_id'), table_name='tender_summaries')
    op.drop_index(op.f('ix_tender_summaries_tender_id'), table_name='tender_summaries')
    op.drop_table('tender_summaries')

    op.drop_index(op.f('ix_document_processing_document_id'), table_name='document_processing')
    op.drop_table('document_processing')

    op.drop_index(op.f('ix_document_contents_document_id'), table_name='document_contents')
    op.drop_table('document_contents')