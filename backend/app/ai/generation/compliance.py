import hashlib
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
from app.ai.providers.base import get_llm
from app.ai.retrieval.retriever import Retriever
from app.ai.prompts import get_prompt
from app.config import get_settings
from app.modules.proposal.models import ComplianceMatrix
from datetime import datetime, timezone


class ComplianceChecker:
    def __init__(self):
        self.settings = get_settings()
        self.retriever = Retriever()

    async def check(
        self,
        organization_id: UUID,
        tender_id: UUID,
        proposal_id: UUID,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        collection = f"org_{organization_id}"

        req_results = await self.retriever.search(
            collection,
            "requirements mandatory shall must deliverables specification evaluation criteria",
            30,
            {"document_id": str(tender_id)}
        )

        requirements_context = "\n\n---\n\n".join([r["text"] for r in req_results if "text" in r]) if req_results else "Tender requirements, specifications and deliverables."

        prop_results = await self.retriever.search(
            collection,
            "proposal content approach methodology",
            30,
            {"document_id": str(proposal_id)}
        )

        proposal_context = "\n\n---\n\n".join([r["text"] for r in prop_results if "text" in r]) if prop_results else "Proposal content and responses."

        prompt = get_prompt(
            "compliance_matrix",
            requirements_context=requirements_context,
            proposal_context=proposal_context
        )

        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        model_name = self.settings.gemini_chat_model if self.settings.llm_provider == "gemini" else self.settings.ollama_chat_model

        start_time = time.perf_counter()
        llm = get_llm(temperature=0.1)
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        response = await chain.ainvoke({"prompt": prompt})
        latency = round(time.perf_counter() - start_time, 3)

        matrix = self._parse_matrix(response)

        total = len(matrix)
        compliant = sum(1 for m in matrix if m.get("status") == "COMPLIANT")
        partial = sum(1 for m in matrix if m.get("status") == "PARTIAL")
        non_compliant = sum(1 for m in matrix if m.get("status") == "NON-COMPLIANT")
        not_addressed = sum(1 for m in matrix if m.get("status") == "NOT ADDRESSED")

        mandatory = [m for m in matrix if m.get("category") == "Mandatory"]
        desirable = [m for m in matrix if m.get("category") == "Desirable"]
        mandatory_total = len(mandatory)
        desirable_total = len(desirable)
        mandatory_met = sum(1 for m in mandatory if m.get("status") == "COMPLIANT")
        desirable_met = sum(1 for m in desirable if m.get("status") == "COMPLIANT")

        overall_score = round((compliant + 0.5 * partial) / total * 100, 1) if total > 0 else 0.0
        mandatory_score = round(mandatory_met / mandatory_total * 100, 1) if mandatory_total > 0 else 0.0

        summary_data = {
            "total_requirements": total,
            "compliant": compliant,
            "partial": partial,
            "non_compliant": non_compliant,
            "not_addressed": not_addressed,
            "overall_score": overall_score,
            "mandatory_total": mandatory_total,
            "mandatory_compliant": mandatory_met,
            "mandatory_score": mandatory_score,
            "desirable_total": desirable_total,
            "desirable_met": desirable_met,
        }

        gaps = [
            {
                "requirement_id": m.get("requirement_id"),
                "requirement": m.get("requirement_text"),
                "gap": m.get("evidence", ""),
                "recommendation": m.get("notes", "")
            }
            for m in matrix if m.get("status") in ("PARTIAL", "NON-COMPLIANT", "NOT ADDRESSED")
        ]

        recommendations = [
            "Address all non-compliant mandatory requirements before submission",
            "Strengthen partial compliance items with additional evidence",
            "Ensure all mandatory documents are included",
            "Review evaluation criteria alignment"
        ]

        tokens = len(prompt.split()) + len(response.split())

        result = {
            "summary": summary_data,
            "matrix": matrix,
            "gaps": gaps,
            "recommendations": recommendations,
            "generation_metadata": {
                "model": model_name,
                "prompt_hash": prompt_hash,
                "tokens": tokens,
                "latency": latency,
            }
        }

        # Persist to compliance_matrices with versioning if db is provided
        if db:
            version_stmt = select(func.coalesce(func.max(ComplianceMatrix.version), 0)).where(
                ComplianceMatrix.tender_id == tender_id,
                ComplianceMatrix.proposal_id == proposal_id,
                ComplianceMatrix.organization_id == organization_id,
            )
            version_res = await db.execute(version_stmt)
            next_version = version_res.scalar_one() + 1

            record = ComplianceMatrix(
                tender_id=tender_id,
                proposal_id=proposal_id,
                organization_id=organization_id,
                version=next_version,
                overall_compliance_score=int(overall_score),
                mandatory_met=mandatory_met,
                mandatory_total=mandatory_total,
                desirable_met=desirable_met,
                desirable_total=desirable_total,
                requirement_results=matrix,
                model_used=model_name,
                prompt_hash=prompt_hash,
                tokens_used=tokens,
                generation_latency_ms=int(latency * 1000),
                is_current=True,
                generated_at=datetime.now(timezone.utc),
            )
            db.add(record)
            await db.flush()

        return result

    def _parse_matrix(self, response: str) -> List[Dict[str, Any]]:
        try:
            matrix = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    matrix = json.loads(json_match.group())
                except json.JSONDecodeError:
                    matrix = []
            else:
                matrix = []

        for i, item in enumerate(matrix):
            if "requirement_id" not in item:
                item["requirement_id"] = f"REQ-{i+1:03d}"

        return matrix