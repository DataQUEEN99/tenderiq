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

All entities inherit from `BaseModel`, providing an explicit UUID `id` primary key, `created_at`, and `updated_at` timestamps:

1. **`organizations`**
   - `id`: UUID (PK)
   - `name`: String(255)
   - `slug`: String(100, Unique, Indexed)
   - `status`: Enum (`Active`, `Suspended`, `Disabled`)
   - `is_deleted`: Boolean

2. **`users`**
   - `id`: UUID (PK)
   - `email`: String(255, Unique, Indexed)
   - `password_hash`: String(255)
   - `full_name`: String(255)
   - `role`: Enum (`Admin`, `Manager`, `Member`, `Viewer`)
   - `is_active`: Boolean
   - `organization_id`: UUID (FK -> `organizations.id`)

3. **`user_invitations`**
   - `id`: UUID (PK)
   - `email`: String(255, Indexed)
   - `role`: Enum (`Admin`, `Manager`, `Member`, `Viewer`)
   - `token`: String(255, Unique, Indexed)
   - `expires_at`: DateTime(timezone=True)
   - `accepted_at`: DateTime(timezone=True, Nullable)
   - `organization_id`: UUID (FK -> `organizations.id`)
   - `invited_by`: UUID (FK -> `users.id`)

4. **`company_profiles`**
   - `id`: UUID (PK)
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
   - `organization_id`: UUID (FK -> `organizations.id`, Unique, Indexed)

5. **`company_documents`**
   - `id`: UUID (PK)
   - `company_profile_id`: UUID (FK -> `company_profiles.id`, Cascade)
   - `document_id`: UUID (FK -> `documents.id`, Cascade)
   - `document_type`: String(50)

6. **`documents`**
   - `id`: UUID (PK)
   - `filename`: String(255)
   - `original_filename`: String(255)
   - `file_hash`: String(64, Indexed)
   - `file_size`: Integer
   - `mime_type`: String(100)
   - `extension`: String(20)
   - `document_type`: Enum (`Tender`, `Proposal`, `Company`, `Reference`, `Other`)
   - `status`: Enum (`Uploading`, `Processing`, `Processed`, `Failed`, `Deleted`)
   - `error_message`: Text
   - `organization_id`: UUID (FK -> `organizations.id`, Indexed)
   - `uploaded_by`: UUID (FK -> `users.id`)
   - `chunk_count`: Integer
   - `vector_collection`: String(100)

7. **`tenders`**
   - `id`: UUID (PK)
   - `title`: String(500)
   - `reference_number`: String(100, Indexed)
   - `description`: Text
   - `issuing_authority`: String(255)
   - `submission_deadline`: DateTime(timezone=True)
   - `estimated_value`: String(100)
   - `currency`: String(3)
   - `contract_duration`: String(100)
   - `status`: Enum (`Draft`, `Published`, `In Progress`, `Submitted`, `Awarded`, `Lost`, `Archived`)
   - `organization_id`: UUID (FK -> `organizations.id`, Indexed)
   - `created_by`: UUID (FK -> `users.id`)

8. **`tender_documents`**
   - `id`: UUID (PK)
   - `tender_id`: UUID (FK -> `tenders.id`, Cascade)
   - `document_id`: UUID (FK -> `documents.id`, Cascade)

9. **`tender_summaries`**
   - `id`: UUID (PK)
   - `tender_id`: UUID (FK -> `tenders.id`, Cascade)
   - `organization_id`: UUID (FK -> `organizations.id`, Cascade)
   - `summary_type`: String(50)
   - `version`: Integer (Auto-incremented per tender/type)
   - `content`: Text
   - `structured_data`: JSON
   - `model`: String(100)
   - `prompt_hash`: String(64)
   - `tokens`: Integer
   - `latency`: Float
   - `created_by`: UUID (FK -> `users.id`, Nullable)

10. **`eligibility_analyses`**
    - `id`: UUID (PK)
    - `tender_id`: UUID (FK -> `tenders.id`, Cascade)
    - `organization_id`: UUID (FK -> `organizations.id`, Cascade)
    - `company_profile_id`: UUID (FK -> `company_profiles.id`, Set Null)
    - `version`: Integer (Auto-incremented per tender)
    - `decision`: String(50) (`GO`, `NO-GO`, `UNKNOWN`)
    - `confidence`: Float
    - `criteria_analysis`: JSON
    - `missing_requirements`: JSON
    - `recommendations`: JSON
    - `reasoning`: Text
    - `model`: String(100)
    - `prompt_hash`: String(64)
    - `tokens`: Integer
    - `latency`: Float
    - `created_by`: UUID (FK -> `users.id`, Nullable)

11. **`proposals`**
    - `id`: UUID (PK)
    - `title`: String(500)
    - `version`: Integer
    - `status`: Enum (`Draft`, `In Review`, `Finalized`, `Submitted`, `Won`, `Lost`, `Archived`)
    - `executive_summary`: Text
    - `compliance_score`: Integer
    - `submitted_at`: DateTime(timezone=True)
    - `tender_id`: UUID (FK -> `tenders.id`)
    - `organization_id`: UUID (FK -> `organizations.id`, Indexed)
    - `created_by`: UUID (FK -> `users.id`)

12. **`proposal_sections`**
    - `id`: UUID (PK)
    - `title`: String(255)
    - `content`: Text
    - `order`: Integer
    - `section_type`: String(50)
    - `is_generated`: Boolean
    - `generation_prompt`: Text
    - `proposal_id`: UUID (FK -> `proposals.id`, Cascade)

13. **`proposal_documents`**
    - `id`: UUID (PK)
    - `proposal_id`: UUID (FK -> `proposals.id`, Cascade)
    - `document_id`: UUID (FK -> `documents.id`, Cascade)

14. **`compliance_matrices`**
    - `id`: UUID (PK)
    - `tender_id`: UUID (FK -> `tenders.id`, Cascade)
    - `proposal_id`: UUID (FK -> `proposals.id`, Cascade, Nullable)
    - `organization_id`: UUID (FK -> `organizations.id`, Cascade)
    - `version`: Integer
    - `overall_score`: Float
    - `summary`: JSON
    - `matrix`: JSON
    - `gaps`: JSON
    - `recommendations`: JSON
    - `model`: String(100)
    - `prompt_hash`: String(64)
    - `tokens`: Integer
    - `latency`: Float
    - `created_by`: UUID (FK -> `users.id`, Nullable)

15. **`chat_sessions`**
    - `id`: UUID (PK)
    - `title`: String(255)
    - `status`: Enum (`Active`, `Archived`)
    - `organization_id`: UUID (FK -> `organizations.id`, Indexed)
    - `created_by`: UUID (FK -> `users.id`)

16. **`chat_messages`**
    - `id`: UUID (PK)
    - `role`: String(20) (`user`, `assistant`, `system`)
    - `content`: Text
    - `tokens_used`: Integer
    - `model_used`: String(100)
    - `session_id`: UUID (FK -> `chat_sessions.id`, Cascade)

17. **`chat_contexts`**
    - `id`: UUID (PK)
    - `context_type`: String(50)
    - `reference_id`: UUID
    - `content`: Text
    - `metadata`: Text
    - `session_id`: UUID (FK -> `chat_sessions.id`, Cascade)

18. **`exports`**
    - `id`: UUID (PK)
    - `export_format`: Enum (`PDF`, `DOCX`, `HTML`)
    - `status`: Enum (`Pending`, `Processing`, `Completed`, `Failed`)
    - `file_path`: String(500)
    - `error_message`: Text
    - `proposal_id`: UUID (FK -> `proposals.id`)
    - `organization_id`: UUID (FK -> `organizations.id`, Indexed)
    - `created_by`: UUID (FK -> `users.id`)

19. **`audit_logs`**
    - `id`: UUID (PK)
    - `action`: Enum (`CREATE`, `READ`, `UPDATE`, `DELETE`, `LOGIN`, `LOGOUT`, `EXPORT`, `IMPORT`, `AI_PROCESS`, `STATUS_CHANGE`)
    - `resource_type`: String(50)
    - `resource_id`: UUID
    - `details`: JSON
    - `ip_address`: String(45)
    - `user_agent`: Text
    - `is_deleted`: Boolean
    - `organization_id`: UUID (FK -> `organizations.id`, Indexed)
    - `user_id`: UUID (FK -> `users.id`, Nullable)

---

## 3. Transaction & Persistence Strategy

- **Unit of Work**: In FastAPI, database sessions are yielded per request via `get_db()`.
- **Repository Boundary**: Repositories only add, query, and call `session.flush()` to allocate identifiers and validate constraints without issuing uncontrolled commits.
- **Service Transaction Boundaries**: Services coordinate multi-step workflows across domain entities.
- **Durable Persistence**: Commits occur at the transaction boundary before HTTP responses return success.

---

## 4. Tenant Isolation Rules

- **Organization Boundary**: Every business resource belongs to an `organization_id`.
- **Query Scoping**: All tenant-scoped repositories enforce `WHERE organization_id = :org_id` and filter soft-deleted records.
- **Vector Isolation**: ChromaDB collections are partitioned per organization (`org_{organization_id}`) and queries enforce `organization_id` metadata filters.
- **Security Check**: Organization management APIs explicitly verify that requests are scoped to `current_user.organization_id` unless the user holds global `ADMIN` privileges.

---

## 5. Module Communication Contracts

- **Service-to-Service Only**: Modules never import or invoke another module's repository directly.
- **Clean Decoupling**: If `TenderService` requires document metadata, it calls `DocumentService.get_by_id`.
- **AI Invocation**: Domain modules interact with AI capabilities strictly through `AIFacade`.

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
- **Cache**: Redis 7 Alpine (`redis://redis:6379/0`)
- **File Storage**: Unified `STORAGE_ROOT` (`/app/data` in Docker, `./storage` locally)
- **Primary AI Provider**: Google Gemini (`gemini-1.5-pro`, `models/embedding-001`) with optional Ollama fallback.
