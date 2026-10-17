# ==============================================================================
# TenderIQ - Complete All-In-One Self-Contained Docker Image
# Contains: React Frontend + FastAPI Backend + PostgreSQL + Redis + ChromaDB + Nginx
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend Assets (React + Vite + Tailwind)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Use pnpm 9 to match lockfileVersion 9.0
RUN corepack enable && corepack prepare pnpm@9 --activate

ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=${VITE_API_URL}

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --no-frozen-lockfile

COPY frontend/ ./
RUN pnpm run build

# ------------------------------------------------------------------------------
# Stage 2: Build Python Backend Virtual Environment
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS backend-builder

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 3: Self-Contained Runtime (Frontend + Backend + Postgres + Redis + Nginx)
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# Install all runtime system packages including PostgreSQL and Redis
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    postgresql \
    postgresql-contrib \
    redis-server \
    libpq5 \
    libmagic1 \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python virtual environment
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/backend"
ENV ENVIRONMENT="production"

# Copy pre-built frontend distribution to Nginx root
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy server & process manager configs
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy backend application code
COPY backend/ /app/backend/

# Copy entrypoint script and set executable permissions
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create data directories for persistence
RUN mkdir -p /app/backend/data/uploads \
             /app/backend/data/vectorstore \
             /app/backend/chroma_db \
             /var/log/supervisor

# Expose cloud web service port
EXPOSE 10000 8000

ENTRYPOINT ["/entrypoint.sh"]

