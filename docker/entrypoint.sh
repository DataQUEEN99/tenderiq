#!/bin/bash
set -e

echo "======================================================================"
echo "          TenderIQ - Cloud Backend & AI Worker Container              "
echo "======================================================================"

mkdir -p /app/backend/data/uploads \
         /app/backend/data/vectorstore \
         /app/backend/chroma_db

cd /app/backend

# 1. Run migrations / table creation
echo "[TenderIQ] Initializing database schema..."
/opt/venv/bin/python -m alembic upgrade head || echo "[TenderIQ] Alembic upgrade completed or handled"

# 2. Launch background Celery worker
if [ "${RUN_WORKER:-true}" = "true" ]; then
    echo "[TenderIQ] Launching background Celery worker..."
    /opt/venv/bin/python worker.py &
fi

# 3. Launch FastAPI directly on cloud $PORT
APP_PORT="${PORT:-10000}"
echo "[TenderIQ] Starting FastAPI on 0.0.0.0:${APP_PORT}..."
exec /opt/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
