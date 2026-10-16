# Run and deploy TenderIQ without Docker

TenderIQ can run without Docker. Docker Compose is only one way to start the
supporting services. The application still requires a PostgreSQL database,
Redis, and a ChromaDB service (or a configured local vector-store mode).

## Local development on Windows

### 1. Install prerequisites

- Python 3.11
- Node.js 20 or newer
- PostgreSQL 14 or newer
- Redis 7 or newer
- A ChromaDB HTTP service, because Python 3.13 uses the lightweight
  `chromadb-client` package

PostgreSQL, Redis, and ChromaDB may be installed locally or replaced with
development instances from their respective hosted providers. Do not put
production credentials in Git.

### 2. Configure the backend

```powershell
cd D:\Projects\Internship\tenderiq\backend
Copy-Item .env.example .env
```

Set at least these values in `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE
REDIS_URL=redis://HOST:6379/0
CHROMA_MODE=http
CHROMA_HOST=HOST
CHROMA_PORT=8000
GEMINI_API_KEY=your-key
JWT_SECRET=replace-with-a-long-random-value
ALLOWED_ORIGINS=http://localhost:5173
```

Use `CHROMA_HOST` and `CHROMA_PORT` for a hosted ChromaDB HTTP service and
preserve the collection name. The `chromadb-client` dependency does not
provide a local persistent Chroma server.

### 3. Install and start the backend

```powershell
cd D:\Projects\Internship\tenderiq\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The helper script `backend/start.ps1` performs the migration and starts the
same server.

Verify the backend at:

```text
http://localhost:8000/health
http://localhost:8000/api/v1/docs
```

### 4. Install and start the frontend

The repository uses pnpm because it includes `pnpm-lock.yaml`. Install pnpm
once if it is not already available:

```powershell
corepack enable
corepack prepare pnpm@9 --activate
```

Then run:

```powershell
cd D:\Projects\Internship\tenderiq\frontend
pnpm install
Copy-Item .env.example .env
```

Set this in `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Start the frontend:

```powershell
pnpm dev --host 0.0.0.0 --port 5173
```

The helper script `frontend/start.ps1` runs the same Vite command after
dependencies have been installed.

## Free deployment without Docker

Use separate services:

1. Deploy `frontend/` to Vercel or Cloudflare Pages.
2. Deploy `backend/` to a native Python web service such as Render.
3. Use a hosted PostgreSQL database such as Neon or Supabase.
4. Use a hosted Redis service such as Upstash.
5. Use a hosted ChromaDB/vector service, or accept that local vector data on a
   free web service may be lost when the service restarts.

### Backend service settings

Set the backend service root directory to `backend` and use:

```text
Build command: pip install -r requirements.txt
Start command: python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check path: /health
```

Set these environment variables in the provider dashboard:

```env
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
CHROMA_MODE=http
CHROMA_HOST=...
CHROMA_PORT=...
GEMINI_API_KEY=...
JWT_SECRET=...
ALLOWED_ORIGINS=https://your-frontend-domain.example
```

Do not run the Celery worker in the web process. If document processing uses
background tasks, deploy a separate worker service with:

```text
python worker.py
```

Free plans may not provide a continuously running worker, persistent disks,
or enough memory for document processing. In that case, use the synchronous
processing path for a demo or upgrade the worker service.

### Frontend service settings

Set the frontend root directory to `frontend`:

```text
Build command: pnpm install --frozen-lockfile && pnpm build
Output directory: dist
```

Set:

```env
VITE_API_URL=https://your-backend-domain.example/api/v1
```

After the frontend receives its final public URL, update the backend
`ALLOWED_ORIGINS` value and redeploy the backend.

## Current limitations

- The free setup is suitable for a demo, not production data.
- Free services can sleep and may have ephemeral storage.
- Uploaded files and local ChromaDB data need persistent storage for a real
  deployment.
- Gemini, PostgreSQL, Redis, and vector-service quotas depend on the provider.
