from typing import List
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import OllamaEmbeddings
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError:
    GoogleGenerativeAIEmbeddings = None
from app.config import get_settings


class ChromaDefaultEmbeddings(Embeddings):
    """Local offline embeddings using ChromaDB's default embedding function."""
    def __init__(self):
        try:
            from chromadb.utils import embedding_functions
            self._ef = embedding_functions.DefaultEmbeddingFunction()
        except Exception:
            self._ef = None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._ef:
            return [list(e) for e in self._ef(texts)]
        return [[0.0] * 384 for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        return self.embed_query(text)


class EmbeddingGenerator:
    def __init__(self, provider: str = None):
        self.settings = get_settings()
        self.provider = provider or self.settings.llm_provider
        self._embeddings = None

    @property
    def embeddings(self) -> Embeddings:
        if self._embeddings is None:
            self._embeddings = self._create_embeddings()
        return self._embeddings

    def _create_embeddings(self) -> Embeddings:
        if self.provider == "ollama":
            return OllamaEmbeddings(
                model=self.settings.ollama_embedding_model,
                base_url=self.settings.ollama_base_url
            )
        elif self.provider == "gemini" and self.settings.gemini_api_key:
            return GoogleGenerativeAIEmbeddings(
                model=self.settings.gemini_embedding_model,
                google_api_key=self.settings.gemini_api_key
            )
        else:
            return ChromaDefaultEmbeddings()

    async def generate(self, texts: List[str]) -> List[List[float]]:
        return await self.embeddings.aembed_documents(texts)

    async def generate_query(self, text: str) -> List[float]:
        return await self.embeddings.aembed_query(text)

    def generate_sync(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def generate_query_sync(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)