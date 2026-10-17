FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p data/uploads data/vectorstore chroma_db

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["sh", "-c", "python create_tables.py || true; (python worker.py &); exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
