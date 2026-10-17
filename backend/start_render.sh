#!/bin/bash
set -x

echo "=== TenderIQ Cloud Bootloader ==="
echo "PORT: ${PORT}"

mkdir -p data/uploads data/vectorstore chroma_db

echo "=== Step 1: Initialize Database Tables ==="
python create_tables.py || echo "Table creation handled"

echo "=== Step 2: Launch Uvicorn ==="
LISTEN_PORT="${PORT:-10000}"
echo "Binding Uvicorn to 0.0.0.0:${LISTEN_PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${LISTEN_PORT}"
