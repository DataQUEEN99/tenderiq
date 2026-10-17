# TenderIQ - Production Deployment Guide

This guide details how to deploy **TenderIQ** so that the entire application—including the frontend, FastAPI backend, and AI layer (PDF text extraction, chunking, Gemini embeddings, ChromaDB vector indexing, and RAG chat)—works reliably in production.

---

## Architecture Overview

TenderIQ consists of two key layers:

1. **Frontend (Vite + React SPA)**:
   - Hosted on **Vercel** (Global Edge CDN, auto-SSL, instant preview deployments).
   - Configured via [vercel.json](file:///c:/Users/Rajkumar%20Pandey/Downloads/tenderiq-main/tenderiq-main/vercel.json) and [frontend/vercel.json](file:///c:/Users/Rajkumar%20Pandey/Downloads/tenderiq-main/tenderiq-main/frontend/vercel.json) for client-side SPA routing.

2. **Backend & AI Worker Layer (Docker / Containerized Stack)**:
   - **FastAPI API Server**: Handles REST endpoints, authentication, and user data.
   - **Celery Worker**: Background daemon processing large tender PDFs, computing embeddings, and indexing vectors.
   - **PostgreSQL 16**: Relational database for users, organizations, tenders, proposals, and audit logs.
   - **Redis 7**: Message broker for Celery tasks and session caching.
   - **ChromaDB**: Vector database storing document embeddings for semantic search and RAG retrieval.
   - **Google Gemini API**: Generates embeddings (`models/embedding-001` or `text-embedding-004`) and performs RAG analysis (`gemini-1.5-pro` or `gemini-1.5-flash`).

> [!IMPORTANT]
> **Why the Backend cannot run on Vercel alone:**
> Vercel is a serverless platform with a 10–15s execution timeout, an ephemeral read-only filesystem, and no daemon support. It cannot host PostgreSQL, Redis, persistent ChromaDB, or the background Celery worker required to process RFP documents.
> The industry-standard architecture is:
> - **Frontend** on **Vercel**
> - **Backend & AI Stack** on **Railway**, **Render**, or any **VPS (Docker Compose)**

---

## Step 1: Deploy Backend & AI Stack

You can deploy the backend using any of the following options:

### Option A: 1-Command Docker Compose on any VPS (Recommended)
(DigitalOcean Droplet, AWS Lightsail, Hetzner, or EC2 — costs ~$5–10/month)

1. SSH into your server:
   ```bash
   git clone https://github.com/ai-tender-rfp/tenderiq.git
   cd tenderiq
   ```

2. Create your `.env` file from the example:
   ```bash
   cp .env.docker.example .env
   ```

3. Set your secret keys and Gemini API key in `.env`:
   ```env
   SECRET_KEY=your-secure-random-secret-key-32-chars
   JWT_SECRET=your-secure-random-secret-key-32-chars
   POSTGRES_PASSWORD=your_secure_db_password
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
   LLM_PROVIDER=gemini
   ENVIRONMENT=production
   ```

4. Start the complete stack in the background:
   ```bash
   docker compose up -d --build
   ```

5. Verify services are healthy:
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```
   *The backend API will be live at `http://your-server-ip:8000/api/v1` (or your domain with HTTPS via Nginx/Caddy).*

---

### Option B: Deploy to Railway / Render

1. Create a **PostgreSQL** database service (or use Supabase / Neon).
2. Create a **Redis** service (or use Upstash Redis).
3. Create a **Web Service** pointing to `/backend` with Dockerfile:
   - Set environment variables:
     - `DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname`
     - `REDIS_URL=redis://default:pass@host:port`
     - `GEMINI_API_KEY=your_gemini_api_key`
     - `LLM_PROVIDER=gemini`
     - `CHROMA_MODE=local`
     - `CHROMADB_PATH=/app/data/chroma_db`
     - `STORAGE_ROOT=/app/data`
     - `SECRET_KEY=your_production_secret`
4. Create a **Background Worker Service** pointing to the same repo with start command:
   ```bash
   python worker.py
   ```

---

## Step 2: Deploy Frontend to Vercel

Once your backend is running and you have its public API URL (e.g., `https://api.yourdomain.com/api/v1` or `http://your-server-ip:8000/api/v1`):

### Method 1: Via Vercel Web Dashboard (Easiest)

1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **"Add New..."** > **"Project"**.
3. Import your GitHub repository: `https://github.com/ai-tender-rfp/tenderiq`.
4. In the Project Configuration:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click "Edit" and select `frontend` (or leave as `./`, both have `vercel.json` pre-configured).
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Under **Environment Variables**, add:
   | Key | Value | Description |
   |---|---|---|
   | `VITE_API_URL` | `https://api.yourdomain.com/api/v1` | URL to your deployed backend API |
   | `VITE_APP_NAME` | `TenderIQ` | App name |
   | `VITE_ENABLE_AI_CHAT` | `true` | Enables AI chat module |
   | `VITE_ENABLE_EXPORTS` | `true` | Enables PDF/Doc export |
6. Click **Deploy**.

---

### Method 2: Via Vercel CLI

1. Install Vercel CLI locally (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. From your project root, deploy the frontend:
   ```bash
   cd frontend
   vercel --prod
   ```

3. Set the environment variable via CLI:
   ```bash
   vercel env add VITE_API_URL production
   # Enter your backend URL when prompted, e.g., https://api.yourdomain.com/api/v1
   ```

4. Redeploy to apply environment variables:
   ```bash
   vercel --prod
   ```

---

## Step 3: Verifying the AI Layer

Once both frontend and backend are deployed:

1. **Open your Vercel URL** (e.g. `https://tenderiq-xxx.vercel.app`).
2. Register an organization or log in.
3. **Upload a Tender RFP Document** (PDF):
   - Check that the document upload status advances from `PENDING` -> `PROCESSING` -> `INDEXED`.
   - Celery worker extracts the PDF text, splits into chunks, and computes Gemini embeddings.
4. **Test AI Features**:
   - **AI Chat**: Ask questions regarding the tender; verify citations and sources.
   - **Executive Summary**: Click "Generate Summary" to test Gemini generation.
   - **Compliance Matrix**: Verify clause extraction and compliance checks.
   - **Proposal Draft**: Generate proposal sections using the indexed tender context.
