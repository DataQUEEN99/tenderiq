from typing import List
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import OllamaEmbeddings, GoogleGenerativeAIEmbeddings
from app.config import get_settings


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
        elif self.provider == "gemini":
            return GoogleGenerativeAIEmbeddings(
                model=self.settings.gemini_embedding_model,
                google_api_key=self.settings.gemini_api_key
            )
        else:
            raise ValueError(f"Unknown embeddings provider: {self.provider}")

    async def generate(self, texts: List[str]) -> List[List[float]]:
        return await self.embeddings.aembed_documents(texts)

    async def generate_query(self, text: str) -> List[float]:
        return await self.embeddings.aembed_query(text)

    def generate_sync(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def generate_query_sync(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)