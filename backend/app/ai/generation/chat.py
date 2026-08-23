from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
from app.ai.providers.base import get_llm
from app.ai.retrieval.retriever import Retriever
from app.ai.prompts import get_prompt
from app.config import get_settings


class ChatEngine:
    def __init__(self):
        self.settings = get_settings()
        self.retriever = Retriever()

    async def chat(self, organization_id: UUID, message: str,
                   conversation_id: Optional[UUID] = None,
                   context_document_ids: Optional[List[UUID]] = None,
                   db: AsyncSession = None) -> Dict[str, Any]:
        collection = f"org_{organization_id}"

        filter_metadata = {"organization_id": str(organization_id)}
        if context_document_ids:
            filter_metadata["document_id"] = {"$in": [str(d) for d in context_document_ids]}

        results = await self.retriever.search(collection, message, 10, filter_metadata)

        context = "\n\n---\n\n".join([r["text"] for r in results]) if results else "No relevant documents found."

        prompt = get_prompt("qa", context=context, question=message)

        llm = get_llm(temperature=0.2)
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        response = await chain.ainvoke({"prompt": prompt})

        sources = []
        for r in results[:5]:
            sources.append({
                "document_id": r["metadata"].get("document_id"),
                "chunk_index": r["metadata"].get("chunk_index"),
                "text_preview": r["text"][:200],
                "score": r["score"]
            })

        return {
            "answer": response.strip(),
            "sources": sources,
            "confidence": sum(r["score"] for r in results) / len(results) if results else 0.0
        }

    async def continue_conversation(self, organization_id: UUID, conversation_history: List[Dict[str, str]],
                                    message: str, context_document_ids: Optional[List[UUID]] = None,
                                    db: AsyncSession = None) -> Dict[str, Any]:
        collection = f"org_{organization_id}"

        filter_metadata = {"organization_id": str(organization_id)}
        if context_document_ids:
            filter_metadata["document_id"] = {"$in": [str(d) for d in context_document_ids]}

        results = await self.retriever.search(collection, message, 10, filter_metadata)

        context = "\n\n---\n\n".join([r["text"] for r in results]) if results else "No relevant documents found."

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history[-10:]])

        full_prompt = f"""Previous conversation:
{history_text}

Current question: {message}

Context documents:
{context}

Answer the current question based on the context and conversation history. Be specific and cite relevant information."""

        llm = get_llm(temperature=0.2)
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        response = await chain.ainvoke({"prompt": full_prompt})

        sources = []
        for r in results[:5]:
            sources.append({
                "document_id": r["metadata"].get("document_id"),
                "chunk_index": r["metadata"].get("chunk_index"),
                "text_preview": r["text"][:200],
                "score": r["score"]
            })

        return {
            "answer": response.strip(),
            "sources": sources,
            "confidence": sum(r["score"] for r in results) / len(results) if results else 0.0
        }