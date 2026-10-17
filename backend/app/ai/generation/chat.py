from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import logging
from app.ai.providers.base import get_llm
from app.ai.retrieval.retriever import Retriever
from app.ai.prompts import get_prompt
from app.config import get_settings

logger = logging.getLogger(__name__)


def _trim_context(results: List[Dict[str, Any]], max_chars: int = 2500) -> str:
    """Trim retrieved chunks so prompt fits comfortably within Groq TPM limit."""
    trimmed = []
    current_len = 0
    for r in results[:4]:
        text = (r.get("text") or "").strip()
        if not text:
            continue
        if current_len + len(text) > max_chars:
            allowed = max(0, max_chars - current_len)
            if allowed > 100:
                trimmed.append(text[:allowed] + "...")
            break
        trimmed.append(text)
        current_len += len(text)
    return "\n\n---\n\n".join(trimmed)


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

        results = []
        try:
            results = await self.retriever.search(collection, message, 4, filter_metadata)
        except Exception as e:
            logger.warning(f"Vector search failed, proceeding with direct answer: {e}")

        if results:
            context = _trim_context(results, max_chars=2500)
            prompt = get_prompt("qa", context=context, question=message)
        else:
            prompt = f"""You are TenderIQ AI, an expert assistant for procurement, RFP analysis, and tender proposals.

Question: {message}

Instructions:
- Provide a helpful, clear, and professional response to the user's question based on tender and RFP best practices.
- If appropriate, mention that uploading tender/RFP documents (via the Documents or Tenders tab) will unlock exact section citations and deep document analysis.
- Maintain a professional, executive tone.

Answer:"""

        try:
            llm = get_llm(temperature=0.2, max_tokens=800)
            chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
            response = await chain.ainvoke({"prompt": prompt})
        except Exception as err:
            logger.error(f"LLM call failed: {err}")
            # If rate limit exceeded, retry with condensed prompt
            if "rate_limit" in str(err).lower() or "413" in str(err) or "429" in str(err):
                try:
                    short_prompt = f"You are TenderIQ AI. Answer concisely in 2-3 paragraphs:\n\nQuestion: {message}\n\nAnswer:"
                    llm = get_llm(temperature=0.2, max_tokens=400)
                    chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
                    response = await chain.ainvoke({"prompt": short_prompt})
                except Exception as e2:
                    logger.error(f"Fallback LLM call failed: {e2}")
                    response = "I am currently experiencing high query volume against the AI model tier. Please try asking again in a few moments."
            else:
                response = "I encountered an issue processing your request. Please try again shortly."

        sources = []
        for r in results[:4]:
            sources.append({
                "document_id": r.get("metadata", {}).get("document_id"),
                "chunk_index": r.get("metadata", {}).get("chunk_index"),
                "text_preview": r.get("text", "")[:200],
                "score": r.get("score", 0.0)
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

        results = []
        try:
            results = await self.retriever.search(collection, message, 4, filter_metadata)
        except Exception as e:
            logger.warning(f"Vector search failed, proceeding without docs: {e}")

        history_text = "\n".join([f"{m['role']}: {m['content'][:300]}" for m in conversation_history[-4:]])

        if results:
            context = _trim_context(results, max_chars=2000)
            full_prompt = f"""Previous conversation:
{history_text}

Current question: {message}

Context documents:
{context}

Answer the current question based on the context and conversation history. Be specific and cite relevant information."""
        else:
            full_prompt = f"""Previous conversation:
{history_text}

Current question: {message}

You are TenderIQ AI. Answer helpfully and professionally based on general tender/procurement expertise."""

        try:
            llm = get_llm(temperature=0.2, max_tokens=800)
            chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
            response = await chain.ainvoke({"prompt": full_prompt})
        except Exception as err:
            logger.error(f"LLM continue_conversation failed: {err}")
            response = "I am currently experiencing temporary rate limits. Please try asking again in a moment."

        sources = []
        for r in results[:4]:
            sources.append({
                "document_id": r.get("metadata", {}).get("document_id"),
                "chunk_index": r.get("metadata", {}).get("chunk_index"),
                "text_preview": r.get("text", "")[:200],
                "score": r.get("score", 0.0)
            })

        return {
            "answer": response.strip(),
            "sources": sources,
            "confidence": sum(r["score"] for r in results) / len(results) if results else 0.0
        }