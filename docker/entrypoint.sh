#!/bin/bash
set -e

echo "======================================================================"
echo "          TenderIQ - All-In-One Self-Contained Container             "
echo "======================================================================"

# Ensure directories exist
mkdir -p /app/backend/data/uploads \
         /app/backend/data/vectorstore \
         /app/backend/chroma_db \
         /var/log/supervisor \
         /var/log/redis \
         /var/run/redis

# 1. Start Internal Redis if not pointing to an external Redis
if [ -z "$REDIS_URL" ] || [[ "$REDIS_URL" == *"127.0.0.1"* ]] || [[ "$REDIS_URL" == *"localhost"* ]]; then
    echo "[TenderIQ] Starting internal Redis service..."
    service redis-server start || /etc/init.d/redis-server start || echo "[TenderIQ] Redis service start handled"
    export REDIS_URL="redis://127.0.0.1:6379/0"
fi

# 2. Start Internal PostgreSQL if not pointing to an external PostgreSQL
if [ -z "$DATABASE_URL" ] || [[ "$DATABASE_URL" == *"127.0.0.1"* ]] || [[ "$DATABASE_URL" == *"localhost"* ]]; then
    echo "[TenderIQ] Starting internal PostgreSQL service..."
    service postgresql start || /etc/init.d/postgresql start || echo "[TenderIQ] PostgreSQL service start handled"

    # Wait for PostgreSQL to become ready
    until su - postgres -c "pg_isready" > /dev/null 2>&1; do
        echo "[TenderIQ] Waiting for internal PostgreSQL to start..."
        sleep 1
    done

    # Ensure user 'tenderiq' and database 'tenderiq' exist
    echo "[TenderIQ] Configuring internal database and credentials..."
    su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='tenderiq'\" | grep -q 1 || psql -c \"CREATE USER tenderiq WITH PASSWORD 'tenderiq_secure_password' SUPERUSER CREATEDB;\""
    su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='tenderiq'\" | grep -q 1 || psql -c \"CREATE DATABASE tenderiq OWNER tenderiq;\""
    su - postgres -c "psql -d tenderiq -c \"GRANT ALL PRIVILEGES ON DATABASE tenderiq TO tenderiq;\""

    export DATABASE_URL="postgresql+asyncpg://tenderiq:tenderiq_secure_password@127.0.0.1:5432/tenderiq"
fi

# 3. Default Chroma mode to local embedded if not specified
if [ -z "$CHROMA_MODE" ]; then
    export CHROMA_MODE="local"
    export CHROMADB_PATH="/app/backend/chroma_db"
fi

# 4. Run database migrations to create all tables
echo "[TenderIQ] Running database schema migrations (Alembic)..."
cd /app/backend
if /opt/venv/bin/python -m alembic upgrade head; then
    echo "[TenderIQ] Database migrations successfully applied!"
else
    echo "[TenderIQ] Note: Migration finished with status $?."
fi

# 5. Background Celery worker for background document ingestion & AI pipeline
if [ "${ENABLE_WORKER:-true}" = "true" ]; then
    echo "[TenderIQ] Launching background Celery worker..."
    /opt/venv/bin/python worker.py > /var/log/worker.log 2>&1 &
fi

echo "======================================================================"
echo " Web UI running on : http://localhost"
echo " API running on    : http://localhost/api/v1"
echo " API Docs on       : http://localhost/docs"
echo "======================================================================"

# Configure Nginx to listen on cloud-assigned PORT (e.g. Render, Railway)
if [ -n "$PORT" ] && [ "$PORT" != "80" ]; then
    echo "[TenderIQ] Updating Nginx configuration to listen on port ${PORT}..."
    sed -i "s/listen 80;/listen ${PORT};/g" /etc/nginx/nginx.conf
fi

# Start Supervisor to run Nginx and FastAPI
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

