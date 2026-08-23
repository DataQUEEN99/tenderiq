import hashlib
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.ai.providers.base import get_llm
from app.ai.retrieval.retriever import Retriever
from app.ai.prompts import get_prompt
from app.config import get_settings
from app.modules.tender.models import TenderSummary


class SummaryGenerator:
    def __init__(self):
        self.settings = get_settings()
        self.retriever = Retriever()

    async def generate(
        self,
        organization_id: UUID,
        document_ids: List[UUID],
        summary_type: str = "executive",
        tender_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> str:
        if not document_ids and not tender_id:
            return "No documents provided for summarization."

        context_parts = []
        target_doc_ids = list(document_ids) if document_ids else []
        if tender_id and not target_doc_ids:
            target_doc_ids.append(tender_id)

        for doc_id in target_doc_ids:
            collection = f"org_{organization_id}"
            results = await self.retriever.search(
                collection,
                "overview summary requirements",
                5,
                {"document_id": str(doc_id)}
            )
            context_parts.extend([r["text"] for r in results if "text" in r])

        if not context_parts:
            context = "General tender document analysis and executive overview."
        else:
            context = "\n\n---\n\n".join(context_parts[:10])

        if summary_type == "executive":
            prompt = get_prompt("executive_summary",
                                tender_title="Document Set",
                                tender_ref="Multiple Documents",
                                issuing_authority="Various",
                                deadline="N/A",
                                context=context)
        elif summary_type == "key_points":
            prompt = get_prompt("key_points", document_text=context, max_points=10)
        else:
            prompt = get_prompt("document_summary",
                                document_title="Document Summary",
                                document_text=context,
                                focus=summary_type,
                                max_words=500)

        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        model_name = self.settings.gemini_chat_model if self.settings.llm_provider == "gemini" else self.settings.ollama_chat_model

        start_time = time.perf_counter()
        llm = get_llm(temperature=0.2)
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        result = await chain.ainvoke({"prompt": prompt})
        latency = round(time.perf_counter() - start_time, 3)

        summary_text = result.strip()
        tokens = len(prompt.split()) + len(summary_text.split())

        # Persist to database with versioning if db and tender_id are provided
        if db and tender_id:
            version_stmt = select(func.coalesce(func.max(TenderSummary.version), 0)).where(
                TenderSummary.tender_id == tender_id,
                TenderSummary.organization_id == organization_id,
                TenderSummary.summary_type == summary_type,
            )
            version_res = await db.execute(version_stmt)
            next_version = version_res.scalar_one() + 1

            summary_record = TenderSummary(
                tender_id=tender_id,
                organization_id=organization_id,
                summary_type=summary_type,
                version=next_version,
                content=summary_text,
                created_by=user_id,
                model=model_name,
                prompt_hash=prompt_hash,
                tokens=tokens,
                latency=latency,
            )
            db.add(summary_record)
            await db.flush()

        return summary_text