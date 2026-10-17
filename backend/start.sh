#!/bin/sh
set -e

echo "Starting TenderIQ Backend Service..."

# Run database migrations
echo "Applying database schema migrations..."
python -m alembic upgrade head || echo "Database migration warning/skipped"

# Optionally start Celery worker in background for unified deployment
if [ "${RUN_WORKER:-true}" = "true" ]; then
    echo "Starting Celery background worker..."
    python worker.py &
fi

APP_PORT="${PORT:-8000}"
echo "Launching Uvicorn on port ${APP_PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
