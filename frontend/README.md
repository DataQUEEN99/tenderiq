# TenderIQ — Enterprise Multi-Tenant AI Tender Management Platform

TenderIQ is a production-grade, AI-powered Tender Management & RFP Response Platform designed to streamline the entire procurement lifecycle for enterprise bid teams. Built with a Clean Architecture Express TypeScript backend, a high-performance React + Vite frontend web application, a multi-tenant database layer via Prisma ORM, and isolated vector/file storage pipelines.

---

## 📋 Table of Contents
1. [System Architecture](#-system-architecture)
2. [Frontend Architecture & UI Web App](#-frontend-architecture--ui-web-app)
3. [Backend Architecture & API Reference](#-backend-architecture--api-reference)
4. [Database Architecture & Schema](#-database-architecture--schema)
5. [Environment & Local Development Setup](#-environment--local-development-setup)
6. [Verification & Testing](#-verification--testing)
7. [Docker Compose & Container Architecture](#-docker-compose--container-architecture)
8. [Safe SQLite to PostgreSQL Data Migration](#-safe-sqlite-to-postgresql-data-migration)


---

## 🏛️ System Architecture

```text
                                  ┌─────────────────────────────────────────────────────────┐
                                  │                  TenderIQ Architecture                  │
                                  └────────────────────────────┬────────────────────────────┘
                                                               │
                       ┌───────────────────────────────────────┼───────────────────────────────────────┐
                       ▼                                       ▼                                       ▼
        ┌─────────────────────────────┐         ┌─────────────────────────────┐         ┌─────────────────────────────┐
        │   React / Vite Web App      │         │   Clean Architecture API    │         │  Prisma ORM & SQLite / PG   │
        │   (Port 5173)               │         │   (Express / Node Port 4000)│         │  (16 Relational Entities)   │
        ├─────────────────────────────┤         ├─────────────────────────────┤         ├─────────────────────────────┤
        │ • Modern Dashboard UI       │ ──────> │ • Presentation Layer        │ ──────> │ • Tenant Isolation          │
        │ • API Client (`client.ts`)  │  HTTP   │ • Application Services      │  ORM    │ • Audit Logs & Traceability │
        │ • Theme & Multi-Tenant Context│ Headers │ • Domain Model & Errors     │ Queries │ • File Storage Linkage      │
        │ • Interactive RAG Chat      │         │ • Prisma & File Adapters    │         │ • Vector Index Linkage      │
        └─────────────────────────────┘         └─────────────────────────────┘         └─────────────────────────────┘
                                                               │
                                       ┌───────────────────────┴───────────────────────┐
                                       ▼                                               ▼
                        ┌─────────────────────────────┐                 ┌─────────────────────────────┐
                        │   Physical Storage          │                 │   ChromaDB Vector Store     │
                        ├─────────────────────────────┤                 ├─────────────────────────────┤
                        │ • `./storage/uploads/`      │                 │ • Collection:               │
                        │ • Multipart File Ingestion  │                 │   `tenderiq_embeddings`     │
                        │ • File Hash De-duplication  │                 │ • Mandatory tenant filtering│
                        └─────────────────────────────┘                 └─────────────────────────────┘
```

---

## 🎨 Frontend Architecture & UI Web App

The frontend is a modern, responsive Single Page Application (SPA) built using React 18, Vite 6, TypeScript, Tailwind CSS v4, and Radix UI / Shadcn UI components.

### 1. Key Frameworks & Dependencies
- **Core**: React 18, React DOM, Vite 6, TypeScript
- **Styling & UI Components**: Tailwind CSS v4, Radix UI primitives (`@radix-ui/react-*`), Lucide Icons (`lucide-react`), Emotion/MUI icons.
- **Charts & Data Visualization**: Recharts (`recharts`) for analytics dashboards.
- **State & Theme**: `next-themes` and custom `ThemeProvider` / `AutoThemeScheduler` supporting Light, Dark, and System modes.

### 2. Frontend Project Structure (`src/app`)
```text
src/app/
├── api/
│   └── client.ts                   # Centralized API client wrapper with multi-tenant headers
├── components/
│   ├── figma/
│   │   └── ImageWithFallback.tsx    # Responsive image fallback component
│   └── ui/                         # 49+ Reusable UI primitives (Buttons, Cards, Dialogs, Tables, Tabs, etc.)
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── table.tsx
│       ├── tabs.tsx
│       └── ...
├── App.tsx                         # Main Dashboard SPA layout, state management & view routing
├── ThemeProvider.tsx               # Context provider for application theme
├── AutoThemeScheduler.ts           # Automatic dark/light theme scheduler based on time of day
└── themeConfig.ts                  # Design system tokens and palette settings
```

### 3. Frontend Features & Workflows
- **Authentication & Tenant Switcher**: Organization registration, login, and instant multi-tenant header management (`x-organization-id`, `x-user-id`).
- **Company Profile Manager**: Interactive editor for company registration identifiers (GST, PAN, CIN), turnovers, experience, and compliance documents.
- **RFP & Tender Ingestion Workspace**: Drag-and-drop file upload zone supporting PDF, DOCX, and text file ingestion with upload status tracking.
- **AI Tender Intelligence Hub**:
  - *Tender Summary View*: Interactive executive summary display with key metadata extraction.
  - *Compliance Matrix Table*: Categorized table listing extracted clauses, technical compliance levels, and risk factors.
  - *Eligibility Evaluator*: Automated score breakdown assessing vendor qualifications against RFP criteria.
  - *AI Bid Proposal Builder*: Versioned proposal draft generator with markdown export capabilities.
- **RAG Chat Assistant**: Dual-panel chat interface supporting document context retrieval, message history persistence, and citation source highlighting.

### 4. API Client Integration (`src/app/api/client.ts`)
All API calls from the frontend pass through the centralized `apiClient` singleton:
- **Automatic Headers**: Injects `x-organization-id` and `x-user-id` on every outgoing request.
- **Error Handling**: Formats server domain errors into structured UI notifications via Sonner toast library.
- **API Methods**:
  - `auth`: `login()`, `registerOrg()`
  - `organization`: `get()`, `update()`
  - `companyProfile`: `get()`, `update()`, `uploadDocument()`
  - `tenders`: `list()`, `get()`, `create()`
  - `documents`: `upload()`, `get()`, `delete()`
  - `aiOutput`: `generateSummary()`, `getSummary()`, `generateCompliance()`, `getCompliance()`, `generateEligibility()`, `getEligibility()`, `generateProposal()`, `getProposal()`
  - `chat`: `createSession()`, `sendMessage()`, `getSessionHistory()`

---

## ⚙️ Backend Architecture & API Reference

The backend follows **Clean Architecture** principles in Node.js / Express, separating presentation, business logic, domain boundaries, and database infrastructure.

### 1. Backend Layer Breakdown (`src/backend`)
```text
src/backend/
├── application/                    # Application Use Cases & Orchestration Services
│   ├── DocumentIngestionService.ts # Handles file upload, hashing, physical storage & DB records
│   ├── ChatService.ts               # RAG chat logic, vector store retrieval & session history
│   ├── TenderService.ts             # Tender CRUD & document linking logic
│   └── CompanyProfileService.ts     # Company profile updates & certification document management
├── domain/                         # Core Domain Logic & Protocols
│   ├── errors/                      # Domain-specific error classes (TenantError, NotFoundError, etc.)
│   ├── interfaces/                  # Repository contracts & external provider interfaces
│   └── models/                      # Domain entities and TypeScript DTOs
├── infrastructure/                 # Concrete Adapters & External Implementations
│   ├── repositories/               # Prisma DB implementations (PrismaTenderRepository, PrismaCompanyProfileRepository, etc.)
│   ├── storage/                     # Local physical disk storage adapter
│   └── vectorstore/                 # ChromaDB vector collection client
└── presentation/                   # HTTP Web API Interfaces
    ├── controllers/                # Express Controllers (Auth, Tender, Document, Chat, AI Output, etc.)
    ├── middleware/                 # Multi-tenant context middleware (`tenantContextMiddleware`), Multer file upload
    └── routes/                     # Express Router handlers mapped to REST endpoints
```

### 2. REST API Endpoint Reference

#### Authentication & Organization
| Method | Endpoint | Description | Headers / Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register-org` | Register new tenant org & admin user | `{ orgName, email, password, fullName }` |
| `POST` | `/api/v1/auth/login` | Authenticate user & retrieve session | `{ email, password }` |
| `GET` | `/api/v1/organizations` | Get current tenant organization details | `x-organization-id` |
| `PUT` | `/api/v1/organizations` | Update organization metadata | `x-organization-id`, `{ name, industry, address, ... }` |

#### Company Profile Management
| Method | Endpoint | Description | Headers / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/company-profiles` | Fetch tenant company profile | `x-organization-id` |
| `PUT` | `/api/v1/company-profiles` | Create/Update company profile details | `x-organization-id`, `{ company_name, gst_number, pan_number, cin, turnover, experience }` |
| `POST` | `/api/v1/company-profiles/documents` | Upload company compliance/tax document | `x-organization-id`, `x-user-id`, Multipart Form (`file`, `document_type`) |

#### Tenders & Document Processing
| Method | Endpoint | Description | Headers / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/tenders` | List tenders for active tenant | `x-organization-id` |
| `POST` | `/api/v1/tenders` | Create new tender record | `x-organization-id`, `x-user-id`, `{ tender_number, tender_name, issuing_authority, ... }` |
| `GET` | `/api/v1/tenders/:tenderId` | Get detailed tender information | `x-organization-id` |
| `POST` | `/api/v1/documents/upload` | Upload & ingest RFP tender document | `x-organization-id`, `x-user-id`, Multipart Form (`file`, `tender_id`, `document_type`) |
| `GET` | `/api/v1/documents/:documentId` | Download / view document metadata | `x-organization-id` |

#### AI Generation & Outputs
| Method | Endpoint | Description | Headers / Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ai-outputs/summary/generate` | Generate tender summary | `x-organization-id`, `x-user-id`, `{ tender_id }` |
| `GET` | `/api/v1/ai-outputs/summary/:tenderId` | Retrieve latest tender summary | `x-organization-id` |
| `POST` | `/api/v1/ai-outputs/compliance/generate` | Generate compliance matrix JSON | `x-organization-id`, `x-user-id`, `{ tender_id }` |
| `GET` | `/api/v1/ai-outputs/compliance/:tenderId` | Retrieve compliance matrix | `x-organization-id` |
| `POST` | `/api/v1/ai-outputs/eligibility/generate` | Run vendor eligibility evaluation | `x-organization-id`, `x-user-id`, `{ tender_id }` |
| `GET` | `/api/v1/ai-outputs/eligibility/:tenderId` | Retrieve eligibility report | `x-organization-id` |
| `POST` | `/api/v1/ai-outputs/proposal/generate` | Draft AI bid proposal | `x-organization-id`, `x-user-id`, `{ tender_id }` |

#### RAG Chat Assistant
| Method | Endpoint | Description | Headers / Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/chat/sessions` | Create or fetch chat session for tender | `x-organization-id`, `x-user-id`, `{ tender_id }` |
| `GET` | `/api/v1/chat/sessions/:sessionId/history` | Retrieve full chat message history | `x-organization-id` |
| `POST` | `/api/v1/chat/messages` | Send message to AI & get RAG response | `x-organization-id`, `x-user-id`, `{ session_id, message_text }` |

---

## 🗄️ Database Architecture & Schema

TenderIQ uses **Prisma ORM** with **PostgreSQL** as the single production relational database for multi-tenant data storage, enterprise security, strict ACID transactions, and high concurrency.


### 1. Schema Overview (16 Relational Models)

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Organization   │ ────< │      User       │ ────< │    AuditLog     │
└────────┬────────┘       └────────┬────────┘       └─────────────────┘
         │                         │
         ├─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ CompanyProfile  │       │    Document     │       │     Tender      │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ CompanyDocument │       │ TenderDocument  │       │  TenderSummary  │
└─────────────────┘       └─────────────────┘       ├─────────────────┤
                                                    │ ComplianceMatrix│
                                                    ├─────────────────┤
                                                    │ EligibilityAnal.│
                                                    ├─────────────────┤
                                                    │    Proposal     │
                                                    ├─────────────────┤
                                                    │   ChatSession   │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │   ChatMessage   │
                                                    └─────────────────┘
```

### 2. Relational Models & Purpose
1. `Organization`: Core multi-tenant boundary storing corporate identity and tenant status.
2. `User`: User accounts bound to an Organization with role RBAC (`ORG_ADMIN`, `Contributor`, `Reviewer`, `Viewer`).
3. `CompanyProfile`: Enterprise metadata (GST, PAN, CIN, Turnover, Past Experience) for eligibility matching.
4. `Document`: Physical file registry storing hashes (`file_hash`), path, size, MIME type, and uploader IDs.
5. `CompanyDocument`: Junction table linking uploaded compliance/tax certificates to a `CompanyProfile`.
6. `Tender`: Specific tender opportunity records created within an Organization.
7. `TenderDocument`: Junction table linking uploaded RFP documents to a `Tender`.
8. `DocumentContent`: Extracted raw/cleaned text strings, word counts, and language detection results.
9. `DocumentProcessing`: Background ingestion job tracking (chunking progress, page counts, embedding models).
10. `TenderSummary`: Versioned AI executive summaries of tenders.
11. `ComplianceMatrix`: Extracted versioned compliance clause matrices stored as structured JSON.
12. `EligibilityAnalysis`: Vendor qualification scoring, gap analysis, and missing document flags.
13. `Proposal`: Generated bid proposal drafts with version tracking.
14. `ChatSession`: Conversational sessions linked to specific Tenders and Users.
15. `ChatMessage`: Individual prompt/response messages with citation metadata.
16. `AuditLog`: Security and compliance audit log recording all system events and access timestamps.

### 3. Multi-Tenant Data Isolation Strategy
- Every query executes with strict filter clauses on `organization_id`.
- Foreign key cascading deletes (`onDelete: Cascade`) maintain integrity when organizations or tenders are removed.
- Vector database embeddings stored in ChromaDB are tagged with `organization_id` in metadata to enforce tenant retrieval boundaries.

---

## ⚡ Environment & Local Development Setup

### 1. Prerequisites
- **Node.js**: v18.x or higher (v20+ recommended)
- **PostgreSQL**: v14.x or higher (or Docker)
- **Redis**: v7.x (or Docker)
- **npm**: v9.x or higher (or `pnpm`)

### 2. Environment Configuration (`.env`)
Create or verify `.env` in the root directory (refer to `.env.example` for clean template):
```env
NODE_ENV=development
PORT=4000
API_PORT=4000
FRONTEND_PORT=5173

# PostgreSQL Database Configuration
POSTGRES_USER=tenderiq_user
POSTGRES_PASSWORD=tenderiq_password
POSTGRES_DB=tenderiq_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL="postgresql://tenderiq_user:tenderiq_password@localhost:5432/tenderiq_db?schema=public"

# Redis Cache & Queues
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL="redis://localhost:6379"

# Storage & AI Engine
UPLOAD_DIR="./storage/uploads"
CHROMADB_URL="http://localhost:8000"
CHROMADB_COLLECTION="tenderiq_embeddings"
VITE_API_URL="http://localhost:4000/api/v1"
```

### 3. Installation & Database Setup Commands

```bash
# 1. Install all Node.js dependencies
npm install

# 2. Generate Prisma Client for PostgreSQL
node node_modules/prisma/build/index.js generate

# 3. Push Prisma Schema to PostgreSQL Database
node node_modules/prisma/build/index.js db push

# 4. Seed initial multi-tenant database records (Optional demo data)
node node_modules/tsx/dist/cli.mjs prisma/seed.ts

# 5. Migrate existing SQLite dev.db records to PostgreSQL (Zero Data Loss)
node node_modules/tsx/dist/cli.mjs scripts/migrateSqliteToPostgres.ts
```

### 4. Running the Services

> 💡 **Windows OS Path Note**: If your project directory path contains spaces or special characters (e.g. `c:\AI Tender & RFP Copilot`), invoke the local Node binary binaries directly as shown below:

- **Backend Express API Server** (Port 4000):
  ```bash
  node node_modules/tsx/dist/cli.mjs src/backend/server.ts
  ```
  *Base API*: `http://localhost:4000/api/v1`  
  *Health Check*: `http://localhost:4000/health`  
  *Readiness Probe*: `http://localhost:4000/ready`

- **Frontend Vite Web Application** (Port 5173):
  ```bash
  node node_modules/vite/bin/vite.js
  ```
  *Web App*: `http://localhost:5173`

- **Prisma Studio (Visual Database GUI)** (Port 5555):
  ```bash
  node node_modules/prisma/build/index.js studio --port 5555
  ```
  *Database Web GUI*: `http://localhost:5555`

---

## 🧪 Verification & Testing

### 1. End-to-End Database & API Verification Script
Run the built-in database verification script to test complete transactional writes across all 16 entities:
```bash
node scripts/test_db_write.js
```

### 2. Expected Verification Test Output
```text
=== TenderIQ E2E Persistence Verification ===
✓ Organization Persisted: org-xxxx
✓ User Persisted: user-xxxx
✓ Company Profile Persisted: profile-xxxx
✓ Tender Created: tender-xxxx
✓ Document Upload & Processing Record Created: doc-xxxx
✓ Company & Tender Document Junction Links Persisted
✓ Tender Summary Generated & Persisted
✓ Compliance Matrix Version Persisted
✓ Eligibility Analysis Score Persisted
✓ AI Proposal Draft Version Persisted
✓ Chat Session & Messages Persisted
✓ Security Audit Log Recorded
🎉 ALL Persisted DB Write Checks Passed Successfully!
```

---

## 🐳 Docker Compose & Container Architecture

TenderIQ includes a complete, production-ready multi-container orchestration architecture powered by Docker Compose.

### 1. Container Topology

```text
                    ┌──────────────────┐
                    │   User Browser   │
                    └────────┬─────────┘
                             │
                             ▼ (Port 5173)
                    ┌──────────────────┐
                    │    Frontend      │
                    │ React / Vite SPA │
                    └────────┬─────────┘
                             │
                             ▼ (Port 4000)
                    ┌──────────────────┐
                    │     Backend      │
                    │ Express / Node   │
                    └───────┬──────────┘
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
        ┌────────────┐ ┌──────────┐ ┌───────────┐
        │ PostgreSQL │ │  Redis   │ │ ChromaDB  │
        │  Database  │ │  Cache   │ │  Vector   │
        │ (Port 5432)│ │(Port 6379│ │(Port 8000)│
        └────────────┘ └──────────┘ └───────────┘
```

### 2. Service Matrix

| Service | Container Name | Base Image | Port | Health Check | Persistent Volume |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | `tenderiq-postgres` | `postgres:16-alpine` | `5432` | `pg_isready -U tenderiq_user -d tenderiq_db` | `postgres_data` |
| **Redis** | `tenderiq-redis` | `redis:7-alpine` | `6379` | `redis-cli ping` | `redis_data` |
| **ChromaDB** | `tenderiq-chromadb` | `chromadb/chroma:latest` | `8000` | HTTP Ping | `chroma_data` |
| **Backend** | `tenderiq-backend` | Built from `Dockerfile` | `4000` | `wget -q http://localhost:4000/health` | `upload_storage` |
| **Frontend** | `tenderiq-frontend` | Built from `Dockerfile` | `5173` | Browser HTTP | — |

### 3. Docker Compose Orchestration Commands

```bash
# 1. Validate the Compose configuration
docker compose config

# 2. Build all container images
docker compose build

# 3. Start all services in detached mode
docker compose up -d

# 4. Check status of running containers
docker compose ps

# 5. Follow live logs across services
docker compose logs -f

# 6. Verify PostgreSQL database health
docker compose exec postgres pg_isready -U tenderiq_user -d tenderiq_db

# 7. Check backend API health and PostgreSQL connection
curl http://localhost:4000/health
```

---

## 🔄 Safe SQLite to PostgreSQL Data Migration

For existing installations that have stored records in local SQLite (`prisma/dev.db`), TenderIQ provides an automated, zero-data-loss migration pipeline.

### Migration Features
- **Strict Foreign-Key Ordering**: Migrates parent entities before dependent entities across all 16 models.
- **Idempotent Upserts**: Safely re-runnable without duplicate key violations.
- **UUID & Timestamp Preservation**: Preserves original UUID identifiers and ISO creation/update dates.

### Running the Data Migration

```bash
# Ensure target PostgreSQL is running and DATABASE_URL is set in .env
npm run db:migrate:data

# Or invoke directly via tsx
node node_modules/tsx/dist/cli.mjs scripts/migrateSqliteToPostgres.ts
```
