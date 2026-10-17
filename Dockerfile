# TenderIQ Backend - Python/FastAPI Production Image for Cloud Deployment
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

COPY --chown=appuser:appuser backend/ .

RUN mkdir -p data/uploads data/vectorstore chroma_db

EXPOSE 8000

CMD ["sh", "-c", "python -m alembic upgrade head || echo 'Migrations handled'; (python worker.py &); uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
