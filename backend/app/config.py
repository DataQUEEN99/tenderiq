import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TenderIQ"
    debug: bool = True
    api_prefix: str = "/api/v1"
    app_version: str = "1.0.0"

    database_url: str = os.getenv("DATABASE_URL") or (
        "postgresql+asyncpg://"
        + "tenderiq:tenderiq@localhost:5432/tenderiq"
    )
    database_echo: bool = False

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    secret_key: str = os.getenv("JWT_SECRET", "change-me-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_days: int = 7

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_chat_model: str = "gemini-1.5-pro"
    gemini_embedding_model: str = "models/embedding-001"

    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    chroma_mode: str = os.getenv("CHROMA_MODE", "http")
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8000"))
    chromadb_path: str = os.getenv("CHROMADB_PATH", "./chroma_db")
    chromadb_collection: str = os.getenv("CHROMA_COLLECTION_NAME", "tenderiq_documents")
    top_k: int = 5
    similarity_threshold: float = 0.7

    storage_type: str = os.getenv("STORAGE_TYPE", "local")
    storage_root: str = os.getenv("STORAGE_ROOT", "./data")
    storage_local_path: str = os.getenv("STORAGE_LOCAL_PATH", "./storage")
    max_file_size_mb: int = 50
    max_document_size: int = 52428800
    allowed_file_types: List[str] = ["application/pdf"]
    allowed_extensions: List[str] = [".pdf"]
    upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    chunk_size: int = 1000
    chunk_overlap: int = 200

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cors_origins: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
