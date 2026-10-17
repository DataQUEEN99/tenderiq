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

RUN chmod +x start_render.sh && \
    mkdir -p data/uploads data/vectorstore chroma_db

ENV PYTHONPATH=/app
EXPOSE 10000

CMD ["./start_render.sh"]
