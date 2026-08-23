from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import UUID
from app.ai.ingestion.embedding_generator import EmbeddingGenerator
from app.ai.ingestion.vector_indexer import VectorIndexer
from app.config import get_settings


class Retriever:
    def __init__(self):
        self.settings = get_settings()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_indexer = VectorIndexer()

    async def search(self, collection_name: str, query: str, top_k: int = 10,
                     filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        query_embedding = await self.embedding_generator.generate_query(query)
        return await self.vector_indexer.search(collection_name, query_embedding, top_k, filter_metadata)

    async def search_by_embedding(self, collection_name: str, query_embedding: List[float],
                                   top_k: int = 10, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        return await self.vector_indexer.search(collection_name, query_embedding, top_k, filter_metadata)

    async def get_context(self, collection_name: str, query: str, top_k: int = 10,
                          filter_metadata: Dict[str, Any] = None) -> str:
        results = await self.search(collection_name, query, top_k, filter_metadata)
        return "\n\n---\n\n".join([r["text"] for r in results])