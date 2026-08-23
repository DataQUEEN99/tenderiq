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
from app.modules.tender.models import EligibilityAnalysis


class EligibilityAnalyzer:
    def __init__(self):
        self.settings = get_settings()
        self.retriever = Retriever()

    async def analyze(
        self,
        organization_id: UUID,
        tender_id: UUID,
        company_profile: Dict[str, Any],
        company_profile_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        collection = f"org_{organization_id}"
        results = await self.retriever.search(
            collection,
            "eligibility criteria qualification requirements mandatory minimum",
            20,
            {"document_id": str(tender_id)}
        )

        tender_context = "\n\n---\n\n".join([r["text"] for r in results if "text" in r]) if results else "Tender requirements and qualification guidelines."
        org_profile_text = self._build_org_profile_text(company_profile)

        prompt = get_prompt(
            "eligibility",
            tender_context=tender_context,
            company_profile=org_profile_text
        )

        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        model_name = self.settings.gemini_chat_model if self.settings.llm_provider == "gemini" else self.settings.ollama_chat_model

        start_time = time.perf_counter()
        llm = get_llm(temperature=0.1)
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        response = await chain.ainvoke({"prompt": prompt})
        latency = round(time.perf_counter() - start_time, 3)

        parsed_result = self._parse_response(response)
        tokens = len(prompt.split()) + len(response.split())

        parsed_result["generation_metadata"] = {
            "model": model_name,
            "prompt_hash": prompt_hash,
            "tokens": tokens,
            "latency": latency,
        }

        # Persist to database with versioning if db is provided
        if db:
            version_stmt = select(func.coalesce(func.max(EligibilityAnalysis.version), 0)).where(
                EligibilityAnalysis.tender_id == tender_id,
                EligibilityAnalysis.organization_id == organization_id,
            )
            version_res = await db.execute(version_stmt)
            next_version = version_res.scalar_one() + 1

            record = EligibilityAnalysis(
                tender_id=tender_id,
                organization_id=organization_id,
                company_profile_id=company_profile_id,
                version=next_version,
                decision=parsed_result.get("decision", "UNKNOWN"),
                confidence=float(parsed_result.get("confidence", 0.0) or 0.0),
                criteria_analysis=parsed_result.get("criteria_analysis", []),
                missing_requirements=parsed_result.get("missing_requirements", []),
                recommendations=parsed_result.get("recommendations", []),
                reasoning=parsed_result.get("reasoning", ""),
                created_by=user_id,
                model=model_name,
                prompt_hash=prompt_hash,
                tokens=tokens,
                latency=latency,
            )
            db.add(record)
            await db.flush()

        return parsed_result

    def _build_org_profile_text(self, profile: Dict[str, Any]) -> str:
        parts = []
        for key, value in profile.items():
            if value:
                if isinstance(value, list):
                    parts.append(f"{key.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}")
                else:
                    parts.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(parts) if parts else "No company profile provided."

    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {
                "decision": "UNKNOWN",
                "confidence": 0.0,
                "criteria_analysis": [],
                "missing_requirements": [],
                "recommendations": ["Failed to parse eligibility assessment"],
                "reasoning": "Could not parse AI response"
            }