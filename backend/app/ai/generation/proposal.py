from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
from app.ai.providers.base import get_llm
from app.ai.retrieval.retriever import Retriever
from app.ai.prompts import get_prompt
from app.config import get_settings


class ProposalGenerator:
    def __init__(self):
        self.settings = get_settings()
        self.retriever = Retriever()

    async def generate(self, organization_id: UUID, tender_id: UUID,
                       company_profile: Dict[str, Any], requirements: List[str],
                       db: AsyncSession = None) -> Dict[str, Any]:
        collection = f"org_{organization_id}"

        req_results = await self.retriever.search(collection,
            "requirements scope deliverables evaluation criteria",
            20, {"document_id": str(tender_id)})

        if not req_results:
            return {
                "sections": [],
                "notes": "Could not retrieve tender requirements for proposal generation"
            }

        requirements_context = "\n\n---\n\n".join([r["text"] for r in req_results])

        reusable_results = await self.retriever.search(collection,
            "past experience case studies capabilities methodology team",
            15, {"document_type": "company"})

        reusable_content = "\n\n---\n\n".join([r["text"] for r in reusable_results]) if reusable_results else "No reusable content available."

        org_capabilities = self._build_capabilities_text(company_profile)

        prompt = get_prompt("proposal_draft",
                           requirements=requirements_context[:15000],
                           reusable_content=reusable_content[:10000],
                           company_capabilities=org_capabilities)

        llm = get_llm(temperature=0.3)
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        response = await chain.ainvoke({"prompt": prompt})

        sections = self._parse_sections(response)

        return {
            "sections": sections,
            "raw_draft": response
        }

    async def generate_section(self, organization_id: UUID, tender_id: UUID,
                               section_title: str, section_type: str,
                               requirements: List[str], company_profile: Dict[str, Any],
                               word_limit: int = 500, db: AsyncSession = None) -> str:
        collection = f"org_{organization_id}"

        req_results = await self.retriever.search(collection,
            " ".join(requirements),
            10, {"document_id": str(tender_id)})

        requirements_context = "\n\n---\n\n".join([r["text"] for r in req_results]) if req_results else "No specific requirements found."

        reusable_results = await self.retriever.search(collection,
            "past experience capabilities methodology",
            10, {"document_type": "company"})

        reusable_content = "\n\n---\n\n".join([r["text"] for r in reusable_results]) if reusable_results else "No reusable content available."

        org_capabilities = self._build_capabilities_text(company_profile)

        prompt = get_prompt("proposal_section",
                           section_title=section_title,
                           section_type=section_type,
                           requirements=requirements_context,
                           reusable_content=reusable_content,
                           company_capabilities=org_capabilities,
                           word_limit=word_limit)

        llm = get_llm(temperature=0.3)
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        response = await chain.ainvoke({"prompt": prompt})

        return response.strip()

    def _build_capabilities_text(self, profile: Dict[str, Any]) -> str:
        parts = []
        for key, value in profile.items():
            if value:
                if isinstance(value, list):
                    parts.append(f"{key.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}")
                else:
                    parts.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(parts) if parts else "Company profile not provided."

    def _parse_sections(self, response: str) -> List[Dict[str, str]]:
        sections = []
        current_section = None
        current_content = []

        for line in response.split("\n"):
            if line.startswith("#") or line.startswith("##"):
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": "\n".join(current_content).strip()
                    })
                current_section = line.lstrip("#").strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections.append({
                "title": current_section,
                "content": "\n".join(current_content).strip()
            })

        return sections