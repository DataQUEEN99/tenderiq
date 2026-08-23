import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from sqlalchemy.dialects.postgresql import UUID
from app.config import get_settings


class VectorIndexer:
    def __init__(self):
        self.settings = get_settings()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        return self._client

    def _get_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    async def index(self, collection_name: str, chunks: List[str], embeddings: List[List[float]],
                    document_id: UUID, organization_id: UUID) -> None:
        collection = self._get_collection(collection_name)

        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": str(document_id),
                "organization_id": str(organization_id),
                "chunk_index": i,
                "text": chunk[:500]
            }
            for i, chunk in enumerate(chunks)
        ]

        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )

    async def delete_document(self, collection_name: str, document_id: UUID) -> None:
        collection = self._get_collection(collection_name)
        results = collection.get(where={"document_id": str(document_id)})
        if results["ids"]:
            collection.delete(ids=results["ids"])

    async def search(self, collection_name: str, query_embedding: List[float],
                     top_k: int, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        collection = self._get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )

        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i]
                })

        return formatted

    async def list_collections(self) -> List[str]:
        return [c.name for c in self.client.list_collections()]