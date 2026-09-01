"""Phase 2: Schema Reconciliation - PK Renaming, BAD Tables, Disputed Tables

Revision ID: 003_schema_reconciliation
Revises: 002_ai_output_doc_processing
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_schema_reconciliation'
down_revision: Union[str, None] = '002_ai_output_doc_processing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _drop_fk_constraints(table_name: str, fk_columns: list[str]) -> None:
    """Drop foreign key constraints for given columns on a table."""
    for col in fk_columns:
        # Constraint name follows pattern: fk_<table>_<column>_<referred_table>
        # We'll try to drop by the known column; if it fails, continue
        constraint_name = f'fk_{table_name}_{col}'
        try:
            op.drop_constraint(constraint_name, table_name, type_='foreignkey')
        except Exception:
            # Try without the referred table part
            try:
                op.drop_constraint(f'{constraint_name}_organizations', table_name, type_='foreignkey')
            except Exception:
                try:
                    op.drop_constraint(f'{constraint_name}_users', table_name, type_='foreignkey')
                except Exception:
                    try:
                        op.drop_constraint(f'{constraint_name}_tenders', table_name, type_='foreignkey')
                    except Exception:
                        try:
                            op.drop_constraint(f'{constraint_name}_proposals', table_name, type_='foreignkey')
                        except Exception:
                            try:
                                op.drop_constraint(f'{constraint_name}_chat_sessions', table_name, type_='foreignkey')
                            except Exception:
                                try:
                                    op.drop_constraint(f'{constraint_name}_company_profiles', table_name, type_='foreignkey')
                                except Exception:
                                    pass


def _rename_pk_column(table_name: str, old_col: str, new_col: str) -> None:
    """Rename primary key column from old_col to new_col."""
    # 1. Add new column as nullable
    op.add_column(table_name, sa.Column(new_col, postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Copy data from old PK to new column
    op.execute(f'UPDATE {table_name} SET {new_col} = {old_col}')

    # 3. Make new column non-nullable
    op.alter_column(table_name, new_col, nullable=False)

    # 4. Drop old primary key constraint
    op.drop_constraint(f'{table_name}_pkey', table_name, type_='primary')

    # 5. Create new primary key constraint on new column
    op.create_primary_key(f'{table_name}_pkey', table_name, [new_col])

    # 6. Drop old id column
    op.drop_column(table_name, old_col)


def _create_fk_constraint(
    child_table: str,
    child_col: str,
    parent_table: str,
    parent_col: str,
    ondelete: str = None
) -> None:
    """Create a foreign key constraint with explicit naming."""
    constraint_name = f'fk_{child_table}_{child_col}_{parent_table}'
    if ondelete:
        op.create_foreign_key(
            constraint_name, child_table, parent_table,
            [child_col], [parent_col], ondelete=ondelete
        )
    else:
        op.create_foreign_key(
            constraint_name, child_table, parent_table,
            [child_col], [parent_col]
        )


def upgrade() -> None:
    # =========================================================================
    # STEP 1: Drop all foreign key constraints before renaming PKs
    # =========================================================================

    # Drop FKs from child tables (order: most dependent first)
    _drop_fk_constraints('audit_logs', ['organization_id', 'user_id'])
    _drop_fk_constraints('user_invitations', ['organization_id', 'invited_by'])
    _drop_fk_constraints('company_profiles', ['organization_id'])
    _drop_fk_constraints('exports', ['proposal_id', 'organization_id', 'created_by'])
    _drop_fk_constraints('chat_contexts', ['session_id'])
    _drop_fk_constraints('chat_messages', ['session_id'])
    _drop_fk_constraints('chat_sessions', ['organization_id', 'created_by'])
    _drop_fk_constraints('proposal_documents', ['proposal_id', 'document_id'])
    _drop_fk_constraints('proposal_sections', ['proposal_id'])
    _drop_fk_constraints('tender_documents', ['tender_id', 'document_id'])
    _drop_fk_constraints('proposals', ['tender_id', 'organization_id', 'created_by'])
    _drop_fk_constraints('tenders', ['organization_id', 'created_by'])
    _drop_fk_constraints('documents', ['organization_id', 'uploaded_by'])
    _drop_fk_constraints('users', ['organization_id'])

    # Drop FKs from tables created in migration 002
    _drop_fk_constraints('company_documents', ['company_profile_id', 'document_id'])
    _drop_fk_constraints('compliance_matrices', ['tender_id', 'organization_id', 'proposal_id'])
    _drop_fk_constraints('eligibility_analyses', ['tender_id', 'organization_id', 'company_profile_id'])
    _drop_fk_constraints('tender_summaries', ['tender_id', 'organization_id'])
    _drop_fk_constraints('document_processing', ['document_id'])
    _drop_fk_constraints('document_contents', ['document_id'])

    # =========================================================================
    # STEP 2: Rename primary key columns in all core tables
    # =========================================================================

    # Core tables (parent tables first, then children)
    _rename_pk_column('organizations', 'id', 'organization_id')
    _rename_pk_column('users', 'id', 'user_id')
    _rename_pk_column('documents', 'id', 'document_id')
    _rename_pk_column('tenders', 'id', 'tender_id')
    _rename_pk_column('proposals', 'id', 'proposal_id')
    _rename_pk_column('chat_sessions', 'id', 'chat_session_id')
    _rename_pk_column('chat_messages', 'id', 'chat_message_id')
    _rename_pk_column('audit_logs', 'id', 'audit_log_id')
    _rename_pk_column('company_profiles', 'id', 'company_profile_id')
    _rename_pk_column('tender_documents', 'id', 'tender_document_id')
    _rename_pk_column('proposal_sections', 'id', 'proposal_section_id')
    _rename_pk_column('proposal_documents', 'id', 'proposal_document_id')
    _rename_pk_column('exports', 'id', 'export_id')

    # Note: chat_contexts and user_invitations will be dropped (disputed tables)
    # But we need to rename their PKs first if they have FKs pointing to them
    # Actually, no other tables reference chat_contexts or user_invitations
    # So we can just drop them later

    # =========================================================================
    # STEP 3: Recreate all foreign key constraints with new referenced column names
    # =========================================================================

    # users -> organizations
    _create_fk_constraint('users', 'organization_id', 'organizations', 'organization_id')

    # documents -> organizations, users
    _create_fk_constraint('documents', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('documents', 'uploaded_by', 'users', 'user_id')

    # tenders -> organizations, users
    _create_fk_constraint('tenders', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('tenders', 'created_by', 'users', 'user_id')

    # tender_documents -> tenders, documents
    _create_fk_constraint('tender_documents', 'tender_id', 'tenders', 'tender_id', ondelete='CASCADE')
    _create_fk_constraint('tender_documents', 'document_id', 'documents', 'document_id', ondelete='CASCADE')

    # proposals -> tenders, organizations, users
    _create_fk_constraint('proposals', 'tender_id', 'tenders', 'tender_id', ondelete='CASCADE')
    _create_fk_constraint('proposals', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('proposals', 'created_by', 'users', 'user_id')

    # proposal_sections -> proposals
    _create_fk_constraint('proposal_sections', 'proposal_id', 'proposals', 'proposal_id', ondelete='CASCADE')

    # proposal_documents -> proposals, documents
    _create_fk_constraint('proposal_documents', 'proposal_id', 'proposals', 'proposal_id', ondelete='CASCADE')
    _create_fk_constraint('proposal_documents', 'document_id', 'documents', 'document_id', ondelete='CASCADE')

    # chat_sessions -> organizations, users
    _create_fk_constraint('chat_sessions', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('chat_sessions', 'created_by', 'users', 'user_id')

    # chat_messages -> chat_sessions
    _create_fk_constraint('chat_messages', 'session_id', 'chat_sessions', 'chat_session_id', ondelete='CASCADE')

    # exports -> proposals, organizations, users
    _create_fk_constraint('exports', 'proposal_id', 'proposals', 'proposal_id', ondelete='CASCADE')
    _create_fk_constraint('exports', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('exports', 'created_by', 'users', 'user_id')

    # company_profiles -> organizations
    _create_fk_constraint('company_profiles', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')

    # audit_logs -> organizations, users
    _create_fk_constraint('audit_logs', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('audit_logs', 'user_id', 'users', 'user_id')

    # =========================================================================
    # STEP 4: Handle disputed tables
    # =========================================================================

    # Drop chat_contexts (disputed - DELETE)
    op.drop_table('chat_contexts')

    # Drop user_invitations (disputed - DELETE)
    op.drop_table('user_invitations')

    # proposal_sections: KEEP, add versioning columns
    # proposal_documents: KEEP (already has PK renamed)
    # exports: KEEP (already has PK renamed)

    # Add versioning columns to proposal_sections
    op.add_column('proposal_sections',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('proposal_sections',
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('proposal_sections',
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # =========================================================================
    # STEP 5: Drop and recreate the 6 BAD tables with correct schema
    # =========================================================================

    # Drop existing tables from migration 002
    op.drop_table('company_documents')
    op.drop_table('compliance_matrices')
    op.drop_table('eligibility_analyses')
    op.drop_table('tender_summaries')
    op.drop_table('document_processing')
    op.drop_table('document_contents')

    # ---- company_documents ----
    op.create_table(
        'company_documents',
        sa.Column('company_document_id', postgresql.UUID(as_uuid=True),
                  primary_key=True, default=uuid.uuid4),
        sa.Column('company_profile_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('company_profiles.company_profile_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('documents.document_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False, server_default='primary'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id'), nullable=False),
        sa.UniqueConstraint('company_profile_id', 'document_id', name='uq_company_document')
    )
    op.create_index('ix_company_documents_company_profile_id', 'company_documents', ['company_profile_id'])
    op.create_index('ix_company_documents_document_id', 'company_documents', ['document_id'])

    # ---- document_contents ----
    op.create_table(
        'document_contents',
        sa.Column('document_content_id', postgresql.UUID(as_uuid=True),
                  primary_key=True, default=uuid.uuid4),
        sa.Column('document_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('documents.document_id', ondelete='CASCADE'),
                  nullable=False, unique=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=False),
        sa.Column('extraction_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('character_count', sa.Integer(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    op.create_index('ix_document_contents_document_id', 'document_contents', ['document_id'], unique=True)

    # ---- document_processing ----
    op.create_table(
        'document_processing',
        sa.Column('document_processing_id', postgresql.UUID(as_uuid=True),
                  primary_key=True, default=uuid.uuid4),
        sa.Column('document_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('documents.document_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('stage', sa.String(30), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    op.create_index('ix_document_processing_document_id', 'document_processing', ['document_id'])
    op.create_index('ix_document_processing_document_stage', 'document_processing', ['document_id', 'stage'])

    # ---- tender_summaries (with versioning) ----
    op.create_table(
        'tender_summaries',
        sa.Column('tender_summary_id', postgresql.UUID(as_uuid=True),
                  primary_key=True, default=uuid.uuid4),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenders.tender_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.organization_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('summary_type', sa.String(30), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('generation_latency_ms', sa.Integer(), nullable=True),
        sa.Column('source_document_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('generated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('tender_id', 'version', name='uq_tender_summary_version')
    )
    op.create_index('ix_tender_summaries_tender_id', 'tender_summaries', ['tender_id'])
    op.create_index('ix_tender_summaries_organization_id', 'tender_summaries', ['organization_id'])

    # ---- eligibility_analyses (with versioning) ----
    op.create_table(
        'eligibility_analyses',
        sa.Column('eligibility_analysis_id', postgresql.UUID(as_uuid=True),
                  primary_key=True, default=uuid.uuid4),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenders.tender_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.organization_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('company_profile_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('company_profiles.company_profile_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('overall_eligible', sa.Boolean(), nullable=False),
        sa.Column('eligibility_score', sa.Integer(), nullable=True),
        sa.Column('criteria_results', postgresql.JSONB(), nullable=False),
        sa.Column('missing_requirements', postgresql.JSONB(), default=[], nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('generation_latency_ms', sa.Integer(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('generated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('tender_id', 'company_profile_id', 'version', name='uq_eligibility_version')
    )
    op.create_index('ix_eligibility_analyses_tender_id', 'eligibility_analyses', ['tender_id'])
    op.create_index('ix_eligibility_analyses_organization_id', 'eligibility_analyses', ['organization_id'])
    op.create_index('ix_eligibility_analyses_company_profile_id', 'eligibility_analyses', ['company_profile_id'])

    # ---- compliance_matrices (with versioning) ----
    op.create_table(
        'compliance_matrices',
        sa.Column('compliance_matrix_id', postgresql.UUID(as_uuid=True),
                  primary_key=True, default=uuid.uuid4),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenders.tender_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organizations.organization_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('proposal_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('proposals.proposal_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('overall_compliance_score', sa.Integer(), nullable=True),
        sa.Column('mandatory_met', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mandatory_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('desirable_met', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('desirable_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('requirement_results', postgresql.JSONB(), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('generation_latency_ms', sa.Integer(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('generated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('proposal_id', 'version', name='uq_compliance_version')
    )
    op.create_index('ix_compliance_matrices_tender_id', 'compliance_matrices', ['tender_id'])
    op.create_index('ix_compliance_matrices_organization_id', 'compliance_matrices', ['organization_id'])
    op.create_index('ix_compliance_matrices_proposal_id', 'compliance_matrices', ['proposal_id'])

    # =========================================================================
    # STEP 6: Recreate FKs for the newly created BAD tables
    # =========================================================================

    # company_documents FKs
    _create_fk_constraint('company_documents', 'company_profile_id', 'company_profiles', 'company_profile_id', ondelete='CASCADE')
    _create_fk_constraint('company_documents', 'document_id', 'documents', 'document_id', ondelete='CASCADE')
    _create_fk_constraint('company_documents', 'created_by', 'users', 'user_id')

    # document_contents FK
    _create_fk_constraint('document_contents', 'document_id', 'documents', 'document_id', ondelete='CASCADE')

    # document_processing FK
    _create_fk_constraint('document_processing', 'document_id', 'documents', 'document_id', ondelete='CASCADE')

    # tender_summaries FKs
    _create_fk_constraint('tender_summaries', 'tender_id', 'tenders', 'tender_id', ondelete='CASCADE')
    _create_fk_constraint('tender_summaries', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')

    # eligibility_analyses FKs
    _create_fk_constraint('eligibility_analyses', 'tender_id', 'tenders', 'tender_id', ondelete='CASCADE')
    _create_fk_constraint('eligibility_analyses', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('eligibility_analyses', 'company_profile_id', 'company_profiles', 'company_profile_id', ondelete='CASCADE')

    # compliance_matrices FKs
    _create_fk_constraint('compliance_matrices', 'tender_id', 'tenders', 'tender_id', ondelete='CASCADE')
    _create_fk_constraint('compliance_matrices', 'organization_id', 'organizations', 'organization_id', ondelete='CASCADE')
    _create_fk_constraint('compliance_matrices', 'proposal_id', 'proposals', 'proposal_id', ondelete='CASCADE')


def downgrade() -> None:
    # =========================================================================
    # REVERSE: Drop FKs for BAD tables
    # =========================================================================
    _drop_fk_constraints('compliance_matrices', ['tender_id', 'organization_id', 'proposal_id'])
    _drop_fk_constraints('eligibility_analyses', ['tender_id', 'organization_id', 'company_profile_id'])
    _drop_fk_constraints('tender_summaries', ['tender_id', 'organization_id'])
    _drop_fk_constraints('document_processing', ['document_id'])
    _drop_fk_constraints('document_contents', ['document_id'])
    _drop_fk_constraints('company_documents', ['company_profile_id', 'document_id', 'created_by'])

    # Drop BAD tables
    op.drop_table('compliance_matrices')
    op.drop_table('eligibility_analyses')
    op.drop_table('tender_summaries')
    op.drop_table('document_processing')
    op.drop_table('document_contents')
    op.drop_table('company_documents')

    # Remove versioning columns from proposal_sections
    op.drop_column('proposal_sections', 'generated_at')
    op.drop_column('proposal_sections', 'is_current')
    op.drop_column('proposal_sections', 'version')

    # Recreate disputed tables (chat_contexts, user_invitations)
    op.create_table(
        'user_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('Admin', 'Manager', 'Member', 'Viewer', name='userrole'), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], name='fk_user_invitations_invited_by_users'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_user_invitations_organization_id_organizations'),
        sa.PrimaryKeyConstraint('id', name='user_invitations_pkey')
    )
    op.create_index(op.f('ix_user_invitations_email'), 'user_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_user_invitations_organization_id'), 'user_invitations', ['organization_id'], unique=False)
    op.create_index(op.f('ix_user_invitations_token'), 'user_invitations', ['token'], unique=True)

    op.create_table(
        'chat_contexts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('context_type', sa.String(length=50), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE', name='fk_chat_contexts_session_id_chat_sessions'),
        sa.PrimaryKeyConstraint('id', name='chat_contexts_pkey')
    )
    op.create_index(op.f('ix_chat_contexts_session_id'), 'chat_contexts', ['session_id'], unique=False)

    # =========================================================================
    # REVERSE: Drop all FKs again before renaming PKs back
    # =========================================================================
    _drop_fk_constraints('audit_logs', ['organization_id', 'user_id'])
    _drop_fk_constraints('company_profiles', ['organization_id'])
    _drop_fk_constraints('exports', ['proposal_id', 'organization_id', 'created_by'])
    _drop_fk_constraints('chat_messages', ['session_id'])
    _drop_fk_constraints('chat_sessions', ['organization_id', 'created_by'])
    _drop_fk_constraints('proposal_documents', ['proposal_id', 'document_id'])
    _drop_fk_constraints('proposal_sections', ['proposal_id'])
    _drop_fk_constraints('tender_documents', ['tender_id', 'document_id'])
    _drop_fk_constraints('proposals', ['tender_id', 'organization_id', 'created_by'])
    _drop_fk_constraints('tenders', ['organization_id', 'created_by'])
    _drop_fk_constraints('documents', ['organization_id', 'uploaded_by'])
    _drop_fk_constraints('users', ['organization_id'])

    # =========================================================================
    # REVERSE: Rename PK columns back to 'id'
    # =========================================================================

    def _rename_pk_back(table_name: str, current_col: str) -> None:
        op.add_column(table_name, sa.Column('id', postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(f'UPDATE {table_name} SET id = {current_col}')
        op.alter_column(table_name, 'id', nullable=False)
        op.drop_constraint(f'{table_name}_pkey', table_name, type_='primary')
        op.create_primary_key(f'{table_name}_pkey', table_name, ['id'])
        op.drop_column(table_name, current_col)

    _rename_pk_back('exports', 'export_id')
    _rename_pk_back('proposal_documents', 'proposal_document_id')
    _rename_pk_back('proposal_sections', 'proposal_section_id')
    _rename_pk_back('tender_documents', 'tender_document_id')
    _rename_pk_back('company_profiles', 'company_profile_id')
    _rename_pk_back('audit_logs', 'audit_log_id')
    _rename_pk_back('chat_messages', 'chat_message_id')
    _rename_pk_back('chat_sessions', 'chat_session_id')
    _rename_pk_back('proposals', 'proposal_id')
    _rename_pk_back('tenders', 'tender_id')
    _rename_pk_back('documents', 'document_id')
    _rename_pk_back('users', 'user_id')
    _rename_pk_back('organizations', 'organization_id')

    # =========================================================================
    # REVERSE: Recreate original FK constraints with old column names
    # =========================================================================

    def _create_fk_old(
        child_table: str,
        child_col: str,
        parent_table: str,
        parent_col: str = 'id',
        ondelete: str = None
    ) -> None:
        constraint_name = f'fk_{child_table}_{child_col}_{parent_table}'
        if ondelete:
            op.create_foreign_key(
                constraint_name, child_table, parent_table,
                [child_col], [parent_col], ondelete=ondelete
            )
        else:
            op.create_foreign_key(
                constraint_name, child_table, parent_table,
                [child_col], [parent_col]
            )

    # Recreate in dependency order (parents first for referenced tables)
    _create_fk_old('users', 'organization_id', 'organizations')

    _create_fk_old('documents', 'organization_id', 'organizations', ondelete='CASCADE')
    _create_fk_old('documents', 'uploaded_by', 'users')

    _create_fk_old('tenders', 'organization_id', 'organizations', ondelete='CASCADE')
    _create_fk_old('tenders', 'created_by', 'users')

    _create_fk_old('tender_documents', 'tender_id', 'tenders', ondelete='CASCADE')
    _create_fk_old('tender_documents', 'document_id', 'documents', ondelete='CASCADE')

    _create_fk_old('proposals', 'tender_id', 'tenders', ondelete='CASCADE')
    _create_fk_old('proposals', 'organization_id', 'organizations', ondelete='CASCADE')
    _create_fk_old('proposals', 'created_by', 'users')

    _create_fk_old('proposal_sections', 'proposal_id', 'proposals', ondelete='CASCADE')

    _create_fk_old('proposal_documents', 'proposal_id', 'proposals', ondelete='CASCADE')
    _create_fk_old('proposal_documents', 'document_id', 'documents', ondelete='CASCADE')

    _create_fk_old('chat_sessions', 'organization_id', 'organizations', ondelete='CASCADE')
    _create_fk_old('chat_sessions', 'created_by', 'users')

    _create_fk_old('chat_messages', 'session_id', 'chat_sessions', ondelete='CASCADE')

    _create_fk_old('chat_contexts', 'session_id', 'chat_sessions', ondelete='CASCADE')

    _create_fk_old('exports', 'proposal_id', 'proposals', ondelete='CASCADE')
    _create_fk_old('exports', 'organization_id', 'organizations', ondelete='CASCADE')
    _create_fk_old('exports', 'created_by', 'users')

    _create_fk_old('company_profiles', 'organization_id', 'organizations', ondelete='CASCADE')

    _create_fk_old('user_invitations', 'organization_id', 'organizations', ondelete='CASCADE')
    _create_fk_old('user_invitations', 'invited_by', 'users')

    _create_fk_old('audit_logs', 'organization_id', 'organizations', ondelete='CASCADE')
    _create_fk_old('audit_logs', 'user_id', 'users')

    # Recreate 002 tables with old schema
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
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE', name='fk_document_contents_document_id_documents'),
        sa.PrimaryKeyConstraint('id', name='document_contents_pkey'),
        sa.UniqueConstraint('document_id', name='uq_document_contents_document_id')
    )
    op.create_index(op.f('ix_document_contents_document_id'), 'document_contents', ['document_id'], unique=True)

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
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE', name='fk_document_processing_document_id_documents'),
        sa.PrimaryKeyConstraint('id', name='document_processing_pkey'),
        sa.UniqueConstraint('document_id', name='uq_document_processing_document_id')
    )
    op.create_index(op.f('ix_document_processing_document_id'), 'document_processing', ['document_id'], unique=True)

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
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_tender_summaries_organization_id_organizations'),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE', name='fk_tender_summaries_tender_id_tenders'),
        sa.PrimaryKeyConstraint('id', name='tender_summaries_pkey'),
        sa.UniqueConstraint('tender_id', name='uq_tender_summaries_tender_id')
    )
    op.create_index(op.f('ix_tender_summaries_tender_id'), 'tender_summaries', ['tender_id'], unique=True)
    op.create_index(op.f('ix_tender_summaries_organization_id'), 'tender_summaries', ['organization_id'], unique=False)

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
        sa.ForeignKeyConstraint(['company_profile_id'], ['company_profiles.id'], name='fk_eligibility_analyses_company_profile_id_company_profiles'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_eligibility_analyses_organization_id_organizations'),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE', name='fk_eligibility_analyses_tender_id_tenders'),
        sa.PrimaryKeyConstraint('id', name='eligibility_analyses_pkey'),
        sa.UniqueConstraint('tender_id', name='uq_eligibility_analyses_tender_id')
    )
    op.create_index(op.f('ix_eligibility_analyses_tender_id'), 'eligibility_analyses', ['tender_id'], unique=True)
    op.create_index(op.f('ix_eligibility_analyses_organization_id'), 'eligibility_analyses', ['organization_id'], unique=False)
    op.create_index(op.f('ix_eligibility_analyses_company_profile_id'), 'eligibility_analyses', ['company_profile_id'], unique=False)

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
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_compliance_matrices_organization_id_organizations'),
        sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id'], name='fk_compliance_matrices_proposal_id_proposals'),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE', name='fk_compliance_matrices_tender_id_tenders'),
        sa.PrimaryKeyConstraint('id', name='compliance_matrices_pkey'),
        sa.UniqueConstraint('tender_id', name='uq_compliance_matrices_tender_id')
    )
    op.create_index(op.f('ix_compliance_matrices_tender_id'), 'compliance_matrices', ['tender_id'], unique=True)
    op.create_index(op.f('ix_compliance_matrices_organization_id'), 'compliance_matrices', ['organization_id'], unique=False)
    op.create_index(op.f('ix_compliance_matrices_proposal_id'), 'compliance_matrices', ['proposal_id'], unique=False)

    op.create_table(
        'company_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('company_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['company_profile_id'], ['company_profiles.id'], ondelete='CASCADE', name='fk_company_documents_company_profile_id_company_profiles'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE', name='fk_company_documents_document_id_documents'),
        sa.PrimaryKeyConstraint('id', name='company_documents_pkey')
    )
    op.create_index(op.f('ix_company_documents_company_profile_id'), 'company_documents', ['company_profile_id'], unique=False)
    op.create_index(op.f('ix_company_documents_document_id'), 'company_documents', ['document_id'], unique=False)

    # Recreate FKs for 002 tables
    _create_fk_old('company_documents', 'company_profile_id', 'company_profiles', ondelete='CASCADE')
    _create_fk_old('company_documents', 'document_id', 'documents', ondelete='CASCADE')

    _create_fk_old('compliance_matrices', 'tender_id', 'tenders', ondelete='CASCADE')
    _create_fk_old('compliance_matrices', 'organization_id', 'organizations')
    _create_fk_old('compliance_matrices', 'proposal_id', 'proposals')

    _create_fk_old('eligibility_analyses', 'tender_id', 'tenders', ondelete='CASCADE')
    _create_fk_old('eligibility_analyses', 'organization_id', 'organizations')
    _create_fk_old('eligibility_analyses', 'company_profile_id', 'company_profiles', ondelete='CASCADE')

    _create_fk_old('tender_summaries', 'tender_id', 'tenders', ondelete='CASCADE')
    _create_fk_old('tender_summaries', 'organization_id', 'organizations')

    _create_fk_old('document_processing', 'document_id', 'documents', ondelete='CASCADE')
    _create_fk_old('document_contents', 'document_id', 'documents', ondelete='CASCADE')