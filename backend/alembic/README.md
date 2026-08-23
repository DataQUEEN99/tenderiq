# Alembic Database Migrations

This directory contains the Alembic database migration configuration for the TenderIQ backend.

## Overview

- **Configuration**: `alembic.ini` - Main alembic configuration file
- **Environment**: `env.py` - Migration environment setup with async support
- **Templates**: `script.py.mako` - Migration script template
- **Migrations**: `versions/` - Directory containing migration scripts

## Usage

### Running Migrations

```bash
# Run all pending migrations
python -m alembic upgrade head

# Run specific migration
python -m alembic upgrade <revision>

# Downgrade one migration
python -m alembic downgrade -1

# Downgrade to specific revision
python -m alembic downgrade <revision>
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "Description of changes"

# Create empty migration
python -m alembic revision -m "Description of changes"
```

### Using the Migration Runner Script

```bash
# Run migrations
python run_migrations.py

# Create new migration
python run_migrations.py --create "Description of changes"
```

## Migration History

- **001_initial_migration**: Initial schema creation for all models

## Models Included

The migrations cover all database models:

1. **organizations** - Multi-tenant organizations
2. **users** - User accounts with roles
3. **documents** - File storage with metadata
4. **tenders** - Tender/RFP records
5. **tender_documents** - Junction table for tender-document relationships
6. **proposals** - Proposal drafts
7. **proposal_sections** - Proposal sections
8. **proposal_documents** - Junction table for proposal-document relationships
9. **chat_sessions** - RAG chat sessions
10. **chat_messages** - Chat messages
11. **chat_contexts** - Chat context documents
12. **exports** - Export records
13. **company_profiles** - Company information
14. **user_invitations** - User invitation system
15. **audit_logs** - Audit trail logging

## Enum Types

The following PostgreSQL enum types are created:

- `organizationstatus` (Active, Suspended, Disabled)
- `userrole` (Admin, Manager, Member, Viewer)
- `documenttype` (Tender, Proposal, Company, Reference, Other)
- `documentstatus` (Uploading, Processing, Processed, Failed, Deleted)
- `tenderstatus` (Draft, Published, In Progress, Submitted, Awarded, Lost, Archived)
- `proposalstatus` (Draft, In Review, Finalized, Submitted, Won, Lost, Archived)
- `chatsessionstatus` (Active, Archived)
- `exportformat` (PDF, DOCX, HTML)
- `exportstatus` (Pending, Processing, Completed, Failed)
- `auditaction` (CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, IMPORT, AI_PROCESS, STATUS_CHANGE)

## Database URL Configuration

The database URL is loaded from the application settings (`app.config.get_settings()`). It uses the `DATABASE_URL` environment variable or the default from `.env`.

For local development with SQLite:
```
DATABASE_URL=sqlite:///./tender_rfp.db
```

For production with PostgreSQL:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

## Notes

- Migrations use async engine for compatibility with the async SQLAlchemy setup
- All enum types are created as PostgreSQL native enums
- The `Base.metadata` from `app.shared.database.session` is used as the target metadata
- All models are imported in `env.py` to ensure they're registered before autogenerate