# Backend Architecture Design (BAD) - TenderIQ

## 1. Executive Architecture Summary

TenderIQ is built as a **Modular Monolith with Layered Domains** running on FastAPI, SQLAlchemy 2.0 (asyncpg), PostgreSQL, and ChromaDB.

The system is organized into decoupled domain modules, a centralized AI subsystem, and shared infrastructure utilities.

```
                  ┌────────────────────────────────────────────────────────┐
                  │                      Client / UI                       │
                  └──────────────────────────┬─────────────────────────────┘
                                             │ HTTP / REST
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                  FastAPI Main Router                   │
                  │   (/api/v1 - Auth, User, Org, Company, Doc, Tender...) │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      │                                      │                                      │
      ▼                                      ▼                                      ▼
┌───────────────────┐              ┌───────────────────┐                  ┌───────────────────┐
│  Business Modules │              │   AI Subsystem    │                  │  Shared / Infra   │
│  (API -> Service  │ ───────────► │  (Facade ->       │ ───────────────► │ (Async Database,  │
│   -> Repository)  │              │   Retrieval /     │                  │  Storage, JWT,    │
│                   │              │   Generation)     │                  │  Logging, Errors) │
└─────────┬─────────┘              └─────────┬─────────┘                  └─────────┬─────────┘
          │                                  │                                      │
          ▼                                  ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL 16 (Relational) + ChromaDB (Vector Store)                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Table Schemas with Explicit Primary Keys (PKs)

All entities inherit from `BaseModel`, providing `created_at` and `updated_at` timestamps. **Each entity defines its own explicit UUID primary key column** named `<entity>_id` (e.g., `organization_id`, `user_id`, `document_id`, `tender_id`, `proposal_id`, `export_id`, `chat_session_id`, `chat_message_id`, `audit_log_id`, `company_profile_id`, `company_document_id`, `tender_document_id`, `tender_summary_id`, `eligibility_analysis_id`, `proposal_section_id`, `proposal_document_id`, `compliance_matrix_id`).

1. **`organizations`**
   - `organization_id`: UUID (PK)
   - `name`: String(255)
   - `slug`: String(100, Unique, Indexed)
   - `status`: Enum (`Active`, `Suspended`, `Disabled`)
   - `is_deleted`: Boolean

2. **`users`**
   - `user_id`: UUID (PK)
   - `email`: String(255, Unique, Indexed)
   - `password_hash`: String(255)
   - `full_name`: String(255)
   - `role`: Enum (`Admin`, `Manager`, `Member`, `Viewer`)
   - `is_active`: Boolean
   - `organization_id`: UUID (FK -> `organizations.organization_id`)

3. **`company_profiles`**
   - `company_profile_id`: UUID (PK)
   - `company_name`: String(255)
   - `industry`: String(100)
   - `employee_count`: String(50)
   - `annual_revenue`: String(100)
   - `website`: String(255)
   - `address`: Text
   - `phone`: String(50)
   - `email`: String(255)
   - `certifications`: Array(String)
   - `capabilities`: Array(String)
   - `past_experience`: Text
   - `key_personnel`: Text
   - `financial_info`: Text
   - `organization_id`: UUID (FK -> `organizations.organization_id`, Unique, Indexed)

4. **`company_documents`**
   - `company_document_id`: UUID (PK)
   - `company_profile_id`: UUID (FK -> `company_profiles.company_profile_id`, Cascade)
   - `document_id`: UUID (FK -> `documents.document_id`, Cascade)
   - `relationship_type`: String(50)
   - `created_by`: UUID (FK -> `users.user_id`)

5. **`documents`**
   - `document_id`: UUID (PK)
   - `filename`: String(255)
   - `original_filename`: String(255)
   - `file_hash`: String(64, Indexed)
   - `file_size`: Integer
   - `mime_type`: String(100)
   - `extension`: String(20)
   - `document_type`: Enum (`Tender`, `Proposal`, `Company`, `Reference`, `Other`)
   - `status`: Enum (`Uploading`, `Processing`, `Processed`, `Failed`, `Deleted`)
   - `error_message`: Text
   - `organization_id`: UUID (FK -> `organizations.organization_id`, Indexed)
   - `uploaded_by`: UUID (FK -> `users.user_id`)
   - `chunk_count`: Integer
   - `vector_collection`: String(100)

6. **`tenders`**
   - `tender_id`: UUID (PK)
   - `title`: String(500)
   - `reference_number`: String(100, Indexed)
   - `description`: Text
   - `issuing_authority`: String(255)
   - `submission_deadline`: DateTime(timezone=True)
   - `estimated_value`: String(100)
   - `currency`: String(3)
   - `contract_duration`: String(100)
   - `status`: Enum (`Draft`, `Published`, `In Progress`, `Submitted`, `Awarded`, `Lost`, `Archived`)
   - `organization_id`: UUID (FK -> `organizations.organization_id`, Indexed)
   - `created_by`: UUID (FK -> `users.user_id`)

7. **`tender_documents`**
   - `tender_document_id`: UUID (PK)
   - `tender_id`: UUID (FK -> `tenders.tender_id`, Cascade)
   - `document_id`: UUID (FK -> `documents.document_id`, Cascade)

8. **`tender_summaries`**
   - `tender_summary_id`: UUID (PK)
   - `tender_id`: UUID (FK -> `tenders.tender_id`, Cascade)
   - `organization_id`: UUID (FK -> `organizations.organization_id`, Cascade)
   - `version`: Integer
   - `summary_text`: Text
   - `summary_type`: String(30)
   - `model_used`: String(100)
   - `prompt_hash`: String(64)
   - `tokens_used`: Integer
   - `generation_latency_ms`: Integer
   - `source_document_ids`: Array(UUID)
   - `is_current`: Boolean

9. **`eligibility_analyses`**
   - `eligibility_analysis_id`: UUID (PK)
   - `tender_id`: UUID (FK -> `tenders.tender_id`, Cascade)
   - `organization_id`: UUID (FK -> `organizations.organization_id`, Cascade)
   - `company_profile_id`: UUID (FK -> `company_profiles.company_profile_id`, Cascade)
   - `version`: Integer
   - `overall_eligible`: Boolean
   - `eligibility_score`: Integer
   - `criteria_results`: JSONB
   - `missing_requirements`: JSONB
   - `model_used`: String(100)
   - `prompt_hash`: String(64)
   - `tokens_used`: Integer
   - `generation_latency_ms`: Integer
   - `is_current`: Boolean
   - `generated_at`: DateTime(timezone=True)

10. **`proposals`**
    - `proposal_id`: UUID (PK)
    - `title`: String(500)
    - `version`: Integer
    - `status`: Enum (`Draft`, `In Review`, `Finalized`, `Submitted`, `Won`, `Lost`, `Archived`)
    - `executive_summary`: Text
    - `compliance_score`: Integer
    - `submitted_at`: DateTime(timezone=True)
    - `tender_id`: UUID (FK -> `tenders.tender_id`)
    - `organization_id`: UUID (FK -> `organizations.organization_id`, Indexed)
    - `created_by`: UUID (FK -> `users.user_id`)

11. **`proposal_sections`**
    - `proposal_section_id`: UUID (PK)
    - `title`: String(255)
    - `content`: Text
    - `order`: Integer
    - `section_type`: String(50)
    - `is_generated`: Boolean
    - `generation_prompt`: Text
    - `version`: Integer
    - `is_current`: Boolean
    - `generated_at`: DateTime(timezone=True)
    - `proposal_id`: UUID (FK -> `proposals.proposal_id`, Cascade)

12. **`proposal_documents`**
    - `proposal_document_id`: UUID (PK)
    - `proposal_id`: UUID (FK -> `proposals.proposal_id`, Cascade)
    - `document_id`: UUID (FK -> `documents.document_id`, Cascade)

13. **`compliance_matrices`**
    - `compliance_matrix_id`: UUID (PK)
    - `tender_id`: UUID (FK -> `tenders.tender_id`, Cascade)
    - `organization_id`: UUID (FK -> `organizations.organization_id`, Cascade)
    - `proposal_id`: UUID (FK -> `proposals.proposal_id`, Cascade, Nullable)
    - `version`: Integer
    - `overall_compliance_score`: Integer
    - `mandatory_met`: Integer
    - `mandatory_total`: Integer
    - `desirable_met`: Integer
    - `desirable_total`: Integer
    - `requirement_results`: JSONB
    - `model_used`: String(100)
    - `prompt_hash`: String(64)
    - `tokens_used`: Integer
    - `generation_latency_ms`: Integer
    - `is_current`: Boolean
    - `generated_at`: DateTime(timezone=True)

14. **`chat_sessions`**
    - `chat_session_id`: UUID (PK)
    - `title`: String(255)
    - `status`: Enum (`Active`, `Archived`)
    - `organization_id`: UUID (FK -> `organizations.organization_id`, Indexed)
    - `created_by`: UUID (FK -> `users.user_id`)

15. **`chat_messages`**
    - `chat_message_id`: UUID (PK)
    - `role`: String(20) (`user`, `assistant`, `system`)
    - `content`: Text
    - `tokens_used`: Integer
    - `model_used`: String(100)
    - `session_id`: UUID (FK -> `chat_sessions.chat_session_id`, Cascade)

16. **`exports`**
    - `export_id`: UUID (PK)
    - `export_format`: Enum (`PDF`, `DOCX`, `HTML`)
    - `status`: Enum (`Pending`, `Processing`, `Completed`, `Failed`)
    - `file_path`: String(500)
    - `error_message`: Text
    - `proposal_id`: UUID (FK -> `proposals.proposal_id`)
    - `organization_id`: UUID (FK -> `organizations.organization_id`, Indexed)
    - `created_by`: UUID (FK -> `users.user_id`)

17. **`audit_logs`**
    - `audit_log_id`: UUID (PK)
    - `action`: Enum (`CREATE`, `READ`, `UPDATE`, `DELETE`, `LOGIN`, `LOGOUT`, `EXPORT`, `IMPORT`, `AI_PROCESS`, `STATUS_CHANGE`)
    - `resource_type`: String(50)
    - `resource_id`: UUID
    - `details`: JSONB
    - `ip_address`: String(45)
    - `user_agent`: Text
    - `is_deleted`: Boolean
    - `organization_id`: UUID (FK -> `organizations.organization_id`, Indexed)
    - `user_id`: UUID (FK -> `users.user_id`, Nullable)

18. **`document_contents`**
    - `document_content_id`: UUID (PK)
    - `document_id`: UUID (FK -> `documents.document_id`, Cascade, Unique)
    - `extracted_text`: Text
    - `extraction_method`: String(50)
    - `extraction_status`: String(20)
    - `error_message`: Text
    - `page_count`: Integer
    - `word_count`: Integer
    - `character_count`: Integer
    - `extracted_at`: DateTime(timezone=True)

19. **`document_processing`**
    - `document_processing_id`: UUID (PK)
    - `document_id`: UUID (FK -> `documents.document_id`, Cascade)
    - `stage`: String(30)
    - `status`: String(20)
    - `progress`: Integer (0-100)
    - `started_at`: DateTime(timezone=True)
    - `completed_at`: DateTime(timezone=True)
    - `error_message`: Text
    - `metadata`: JSONB

---

## 3. Transaction & Persistence Strategy

- **Unit of Work**: `UnitOfWork` class wraps `AsyncSession` and owns the transaction lifecycle (`async with uow.begin():` → commit/rollback). No layer commits/rollbacks directly.
- **Repository Boundary**: Repositories only add, query, and call `session.flush()` to allocate identifiers and validate constraints without issuing uncontrolled commits.
- **Service Transaction Boundaries**: Services coordinate multi-step workflows across domain entities within a `UnitOfWork`.
- **Durable Persistence**: Commits occur at the transaction boundary (end of `UnitOfWork`) before HTTP responses return success.
- **Celery Tasks**: Background tasks create their own `UnitOfWork` per task execution for explicit transaction boundaries.

---

## 4. Tenant Isolation Rules

- **Organization Boundary**: Every business resource belongs to an `organization_id`.
- **Query Scoping**: All tenant-scoped repositories (`TenantRepository`) enforce `WHERE organization_id = :org_id` and filter soft-deleted records. Every repository call requires `organization_id` parameter.
- **Vector Isolation**: ChromaDB collections are partitioned per organization (`org_{organization_id}`) and queries enforce `organization_id` metadata filters.
- **Security Check**: Organization management APIs explicitly verify that requests are scoped to `current_user.organization_id` unless the user holds global `ADMIN` privileges.
- **Background Tasks**: Celery tasks pass `organization_id` through the pipeline; all repository calls in background processing are tenant-scoped.

---

## 5. Module Communication Contracts

- **Service-to-Service Only**: Modules never import or invoke another module's repository directly.
- **Clean Decoupling**: If `TenderService` requires document metadata, it calls `DocumentService.get_by_id`.
- **AI Invocation**: Domain modules interact with AI capabilities strictly through `AIFacade`.
- **Cross-Module Access**: Authentication bootstrap creates organizations via `OrganizationService.create_organization()` — never accesses `OrganizationRepository` directly.

---

## 6. AI Pipeline Flow

```
[Upload] ──► [SHA-256 Hash & Dedup] ──► [StorageService (Local Disk)]
     │
     ▼
[Text Extraction (PyMuPDF / DOCX)] ──► [Chunker (1000 chars / 200 overlap)]
     │
     ▼
[Embedding Generator (Gemini / Nomic)] ──► [ChromaDB Indexing (org_{org_id})]
     │
     ▼
[AI Analysis (Summary / Eligibility / Compliance / Proposal)]
     │
     ▼
[Persist Output to tender_summaries / eligibility_analyses / compliance_matrices with version & latency]
```

---

## 7. Deployment Configuration

- **Database**: PostgreSQL 16 (Async URL: `postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}`)
- **Vector Database**: ChromaDB HTTP Service (`http://chroma:8000`)
- **Cache/Queue**: Redis 7 Alpine (`redis://redis:6379/0`) — single `redis_url` setting used by both Celery and application
- **File Storage**: Unified `STORAGE_ROOT` (`/app/data` in Docker, `./storage` locally)
- **Primary AI Provider**: Google Gemini (`gemini-1.5-pro`, `models/embedding-001`) with optional Ollama fallback.
- **File Validation**: PDF-only (`application/pdf`, `.pdf`)
- **Migrations**: Alembic runs on startup; failure raises `RuntimeError` to prevent API starting against incompatible schema
- **Bootstrap Security**: `/auth/bootstrap` protected by PostgreSQL advisory lock (`pg_try_advisory_lock`) to prevent re-entry and token leak on first init

---

## 8. Key Architectural Decisions

| Concern | Decision |
|---------|----------|
| Primary Keys | Explicit `<entity>_id` per table; no generic `id` column or compatibility property |
| Transaction Ownership | `UnitOfWork` is the sole owner; services/repositories do not commit |
| Tenant Scoping | Required parameter on every repository method; enforced by `TenantRepository` base class |
| Layer Separation | API → Service → Repository → Database; no direct DB access from API layer |
| Cross-Module Deps | Services call other services; never repositories |
| Background Processing | Celery tasks create own `UnitOfWork`; pass `organization_id` throughout |
| Configuration | Single `redis_url` in `Settings`; PDF-only file validation; fail-fast migrations |
| Bootstrap | Advisory lock + idempotency check; no token returned after first init |

---

*Updated to reflect implementation after P0/P1/P2 fixes (items 1–17 complete).*