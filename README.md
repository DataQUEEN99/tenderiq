# AI Tender & RFP Copilot

An AI-powered platform for automating tender/RFP analysis, eligibility checking, compliance matrix generation, and proposal drafting.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI Tender & RFP Copilot                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │   Frontend   │◄───│   FastAPI    │◄───│  PostgreSQL  │    │ChromaDB  │  │
│  │  (React/Vue) │    │   Backend    │    │  (Relational)│    │ (Vectors)│  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘    └──────────┘  │
│                             │                                               │
│                    ┌────────┴────────┐                                     │
│                    │  File Storage   │                                     │
│                    │ (Local/S3/MinIO)│                                     │
│                    └─────────────────┘                                     │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      AI Processing Pipeline                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │  Document   │──│  Chunking & │──│  Embedding  │──│  Vector    │  │  │
│  │  │  Processor  │  │  Metadata   │  │  Generation │  │  Storage   │  │  │
│  │  │ (PyMuPDF)   │  │  Extraction │  │ (Ollama/    │  │ (ChromaDB) │  │  │
│  │  └─────────────┘  └─────────────┘  │  Gemini)    │  └────────────┘  │  │
│  │                                     └──────┬──────┘                  │  │
│  │                                            │                         │  │
│  │  ┌─────────────┐  ┌─────────────┐         │                         │  │
│  │  │  Eligibility│  │  Compliance │◄────────┘                         │  │
│  │  │  Engine     │  │  Matrix     │                                   │  │
│  │  │ (Rule-based)│  │  Generator  │                                   │  │
│  │  └─────────────┘  └─────────────┘                                   │  │
│  │         │                │                                          │  │
│  │         └──────┬─────────┘                                          │  │
│  │                ▼                                                   │  │
│  │  ┌─────────────────────┐                                           │  │
│  │  │  Proposal Generator │                                           │  │
│  │  │ (Templates + AI)    │                                           │  │
│  │  └─────────────────────┘                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Architectural Decisions (MVP)

| Module | Decision | Rationale |
|--------|----------|-----------|
| **Company Info** | Hybrid (Profile + Documents) | Structured data for queries, docs for evidence |
| **Eligibility** | Rule-based + AI explanations | Transparent, auditable, no hallucination risk |
| **Compliance Matrix** | Tender vs Profile + Documents | Combines speed with verification |
| **Proposal Generator** | Templates + Verified Data + AI | Professional output, no fabricated content |
| **Missing Info** | "Not Found" + Human Review | No AI guessing on legal documents |
| **PDF Processing** | PyMuPDF (text-based PDFs only) | Fast, accurate, covers 90% of gov tenders |
| **LLM Provider** | Pluggable (Ollama dev, Gemini prod) | Free local dev, quality production option |
| **Storage** | PostgreSQL + ChromaDB + File Storage | Workload isolation, cost optimization |
| **Multi-tenancy** | Defense in Depth (RLS + App + Vector) | Security-first, regulatory compliant |
| **Error Handling** | Graceful degradation + retries | Actionable feedback, progress preservation |

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Pydantic settings from .env
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py          # SQLAlchemy engine/session
│   │   └── base.py             # BaseModel with timestamps
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tender.py           # SQLAlchemy models
│   │   ├── embeddings.py       # Embedding model wrappers
│   │   └── llm.py              # LLM model wrappers
│   ├── schemas/
│   │   └── tender.py           # Pydantic request/response DTOs
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py         # CRUD services
│   │   ├── document_processor.py  # PDF/DOCX/TXT processing
│   │   ├── embeddings.py       # FAISS/ChromaDB vector store
│   │   ├── chains.py           # LangChain prompt chains
│   │   ├── llm.py              # LLM provider interface
│   │   └── orchestrator.py     # TenderPipeline main class
│   └── api/v1/
│       ├── __init__.py
│       └── tender.py           # REST endpoints
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tenders/upload` | Upload & process tender PDF |
| `GET` | `/api/v1/tenders` | List all tenders |
| `GET` | `/api/v1/tenders/{id}` | Get tender details |
| `DELETE` | `/api/v1/tenders/{id}` | Delete tender |
| `POST` | `/api/v1/tenders/{id}/query` | Ask questions about tender |
| `POST` | `/api/v1/tenders/{id}/eligibility` | Check eligibility |
| `POST` | `/api/v1/tenders/{id}/executive-summary` | Generate summary |
| `POST` | `/api/v1/tenders/{id}/proposal-draft` | Generate proposal draft |
| `POST` | `/api/v1/tenders/{id}/compliance-matrix` | Generate compliance matrix |
| `POST` | `/api/v1/tenders/{id}/key-fields` | Extract key fields |

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Ollama (for local LLM) or Gemini API key

### Installation

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
docker-compose up -d db
uvicorn app.main:app --reload
```

### Environment Variables

```env
# LLM Provider: ollama (local) or gemini (cloud)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# For Gemini (production)
GEMINI_API_KEY=your_key
GEMINI_CHAT_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=models/embedding-001

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tender_rfp

# Vector Store
VECTOR_STORE_PATH=./data/vectorstore

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Using Ollama (Local Development)

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama serve
```

## Multi-Tenant Data Isolation

The system implements **defense-in-depth** isolation:

1. **PostgreSQL Row-Level Security (RLS)** - Database-enforced policies
2. **Application Middleware** - Sets org context per request, explicit checks
3. **ChromaDB Metadata Filtering** - Mandatory `organization_id` filter on every query
4. **File Storage Paths** - Prefixed with `/orgs/{org_id}/...`

## Error Handling Strategy

| Failure Mode | Handling |
|--------------|----------|
| PDF extraction fails | 3 fallback methods → manual text entry option |
| LLM unavailable | Exponential backoff (1s, 2s, 4s) + circuit breaker |
| No retrieval results | Show full text, suggest broader queries |
| Proposal timeout | Streaming with per-section timeout, save progress |

## Roadmap

### MVP (Current)
- [x] Upload & process tender PDFs
- [x] Tender Q&A with citations
- [x] Eligibility assessment (rule-based)
- [x] Compliance matrix
- [x] Proposal draft generation
- [x] Executive summary
- [x] Key field extraction
- [x] Export to DOCX/PDF

### Phase 2
- Company Knowledge Base
- Proposal Memory (reuse past content)
- Document Gap Analysis

### Phase 3
- Risk Analyzer
- Tender Match Score
- Timeline Planner

### Enterprise
- Competitor Intelligence
- Pricing Recommendation Engine
- CRM/ERP Integration
- Multi-user Collaboration
- Analytics Dashboard

## Modular Architecture & Enhancements (Phases 5 - 14)

The backend has been consolidated into an enterprise-grade **Modular Monolith** adhering to the Backend Architecture Design (`docs/BAD.md`):

### 1. Elimination of Direct DB Access in Services (Phase 5)
- All raw `self.session.execute(select(...))` queries moved into their owning domain repositories (`TenderRepository`, `ProposalRepository`, `ExportRepository`, `AuthRepository`, etc.).
- Services strictly interact through repository interfaces.

### 2. Elimination of Cross-Module Repository Access (Phase 6)
- Replaced all direct cross-repo imports with explicit service-to-service calls:
  - `TenderService.attach_documents` delegates document existence checks to `DocumentService.verify_documents_exist()`.
  - `ProposalService.attach_documents` delegates document verification to `DocumentService.verify_documents_exist()`.
  - `ExportService` delegates proposal and section retrieval to `ProposalService.get_proposal_with_sections()`.
- Modules only import and interact with their own dedicated repository.

### 3. Configuration Unification & AI Provider Standardization (Phase 7)
- Standardized configuration under `app/config.py` with `get_settings()` singleton.
- Configured Google Gemini as primary LLM/embedding provider with optional local Ollama fallback.
- Added ChromaDB HTTP client settings (`chroma_host`, `chroma_port`) to settings and `VectorIndexer`.

### 4. End-to-End Document Ingestion & Reprocessing (Phase 8)
- Integrated automated document processing on upload via `AIFacade.process_document` (PyMuPDF text extraction, chunking, embedding generation, ChromaDB vector indexing scoped to `org_{org_id}`).
- Document status transitions (`UPLOADING` -> `PROCESSING` -> `PROCESSED` / `FAILED`).
- Added document `reprocess` endpoint.

### 5. AI Output Persistence with Versioning & Telemetry (Phase 9)
- **`tender_summaries`**: Versioned storage for generated executive, technical, and key point summaries with generation metadata (`model`, `prompt_hash`, `tokens`, `latency`).
- **`eligibility_analyses`**: Versioned persistence of tender GO/NO-GO eligibility analyses, confidence scores, criteria breakdown, and recommendations.
- **`compliance_matrices`**: Versioned compliance matrices mapping requirements against proposals with score calculation and gap identification.

### 6. Legacy Architecture Removal (Phase 10)
- Fully removed legacy monolithic packages (`app/models`, `app/services`, `app/api/v1`, `app/auth`, `app/db`, `app/core`, `app/utils`, `app/middleware`, and legacy AI subpackages).
- Consolidated all HTTP routing into modular domain routers under `app/modules/*` loaded directly in `app/main.py`.

### 7. API Contract Alignment (Phase 11)
- **User Management Module**: Exposed `/api/v1/users` endpoints for invitations, accept invitation, listing users, role updates, and user deactivation.
- **Company Document Relations**: Added `/api/v1/company/documents` endpoints to attach, list, and detach company profile reference documents.
- **Document Pipeline Enhancements**: Added `/api/v1/documents/{id}/status`, `/api/v1/documents/{id}/reprocess`, and `/api/v1/documents/{id}/download`.
- **Chat Endpoints**: Standardized route paths including `/api/v1/chat/sessions/{id}/messages`.
- **System Bootstrap**: Added `/api/v1/auth/bootstrap` for initial first-tenant and root administrator setup.
- **Tenant Isolation**: Strict organization boundary enforcement across repositories, services, and API authorization checks.

### 8. Configuration & Deployment Alignment (Phase 12)
- Upgraded database engine and Docker Compose to async SQLAlchemy with `postgresql+asyncpg://`.
- Standardized ChromaDB vector database service host and port.
- Unified `STORAGE_ROOT` across settings and `StorageService`.
- Synchronized `.env.example` and Alembic migrations.

### 9. Architectural Documentation (Phase 13)
- Detailed entity schemas, transaction boundaries, tenant isolation rules, and AI ingestion/generation pipelines are comprehensively documented in `docs/BAD.md`.

### 10. Security, Transaction-Safety & Layering Remediation (Phase 14)
Implemented multi-tenant hardening, transaction-safety, and layering fixes according to the Backend Remediation Plan:
- **Single-Owner Transaction Management**: Refactored `UnitOfWork` in `backend/app/shared/database/transaction.py` to serve as the sole transaction boundary with native async context management; eliminated manual `__aenter__()` / `__aexit__()` calls; prevented double begin/commit via `session.in_transaction()`.
- **Tenant Isolation in Document Processing**: Enforced `organization_id` scoping in `DocumentService.get_progress` when querying `DocumentProcessingRepository`, and standardized `DocumentRepository.get_by_id` and `update_status` parameters to `(document_id, organization_id)`.
- **Background Worker Transaction Safety**: Passed `organization_id=doc.organization_id` in `document_tasks.py` during stuck document status cleanup within Celery background tasks.
- **Organization API Tenant Verification**: Fixed parameter bug in `_verify_tenant_access(current_user, organization_id)` in `backend/app/modules/organization/api.py`.
- **Explicit Primary Key References**: Updated export generation (`_export_pdf`, `_export_docx`, `_export_html`) in `backend/app/modules/export/service.py` to use explicit `proposal_id = getattr(proposal, "proposal_id", getattr(proposal, "id", None))`.
- **Configuration & Validation Consistency**: Synchronized `ALLOWED_EXTENSIONS=.pdf` in `backend/.env.example` to ensure uniform PDF-only validation across application configuration and validators.

## License

MIT