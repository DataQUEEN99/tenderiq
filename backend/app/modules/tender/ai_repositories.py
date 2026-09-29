from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.tender.models import TenderSummary, EligibilityAnalysis
from app.modules.proposal.models import ComplianceMatrix
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class TenderSummaryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tender_id(self, tender_id: UUID, organization_id: UUID = None) -> Optional[TenderSummary]:
        query = select(TenderSummary).where(TenderSummary.tender_id == tender_id)
        if organization_id is not None:
            query = query.where(TenderSummary.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, summary_id: UUID, organization_id: UUID = None) -> Optional[TenderSummary]:
        query = select(TenderSummary).where(TenderSummary.tender_summary_id == summary_id)
        if organization_id is not None:
            query = query.where(TenderSummary.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, summary: TenderSummary) -> TenderSummary:
        self.session.add(summary)
        await self.session.flush()
        await self.session.refresh(summary)
        return summary

    async def update(self, summary: TenderSummary) -> TenderSummary:
        await self.session.flush()
        await self.session.refresh(summary)
        return summary

    async def upsert(self, organization_id: UUID, tender_id: UUID, summary_type: str,
                     summary_text: str, generation_model: str = None, prompt_hash: str = None,
                     tokens_used: int = None, generation_latency_ms: int = None,
                     metadata: dict = None) -> TenderSummary:
        existing = await self.get_by_tender_id(tender_id, organization_id)
        if existing:
            existing.summary_type = summary_type
            existing.summary_text = summary_text
            existing.version += 1
            if generation_model:
                existing.model_used = generation_model
            if prompt_hash:
                existing.prompt_hash = prompt_hash
            if tokens_used is not None:
                existing.tokens_used = tokens_used
            if generation_latency_ms is not None:
                existing.generation_latency_ms = generation_latency_ms
            return await self.update(existing)

        summary = TenderSummary(
            organization_id=organization_id,
            tender_id=tender_id,
            summary_type=summary_type,
            summary_text=summary_text,
            version=1,
            model_used=generation_model,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        return await self.create(summary)

    async def list_by_organization(self, organization_id: UUID, page: int = 1,
                                    page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[TenderSummary], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(TenderSummary).where(
            TenderSummary.organization_id == organization_id
        ).order_by(TenderSummary.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(TenderSummary.tender_summary_id)).where(
            TenderSummary.organization_id == organization_id
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total

    async def delete(self, summary_id: UUID) -> bool:
        summary = await self.get_by_id(summary_id)
        if not summary:
            return False
        await self.session.delete(summary)
        await self.session.flush()
        return True
class EligibilityAnalysisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tender_id(self, tender_id: UUID, organization_id: UUID = None) -> Optional[EligibilityAnalysis]:
        query = select(EligibilityAnalysis).where(EligibilityAnalysis.tender_id == tender_id)
        if organization_id is not None:
            query = query.where(EligibilityAnalysis.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, analysis_id: UUID, organization_id: UUID = None) -> Optional[EligibilityAnalysis]:
        query = select(EligibilityAnalysis).where(EligibilityAnalysis.eligibility_analysis_id == analysis_id)
        if organization_id is not None:
            query = query.where(EligibilityAnalysis.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, analysis: EligibilityAnalysis) -> EligibilityAnalysis:
        self.session.add(analysis)
        await self.session.flush()
        await self.session.refresh(analysis)
        return analysis

    async def update(self, analysis: EligibilityAnalysis) -> EligibilityAnalysis:
        await self.session.flush()
        await self.session.refresh(analysis)
        return analysis

    async def upsert(self, organization_id: UUID, tender_id: UUID, company_profile_id: UUID,
                     overall_eligible: bool, eligibility_score: int = None,
                     criteria_results: list = None, missing_requirements: list = None,
                     generation_model: str = None, prompt_hash: str = None,
                     tokens_used: int = None, generation_latency_ms: int = None,
                     metadata: dict = None) -> EligibilityAnalysis:
        existing = await self.get_by_tender_id(tender_id, organization_id)
        if existing:
            existing.overall_eligible = overall_eligible
            if eligibility_score is not None:
                existing.eligibility_score = eligibility_score
            if criteria_results is not None:
                existing.criteria_results = criteria_results
            if missing_requirements is not None:
                existing.missing_requirements = missing_requirements
            existing.version += 1
            if generation_model:
                existing.model_used = generation_model
            if prompt_hash:
                existing.prompt_hash = prompt_hash
            if tokens_used is not None:
                existing.tokens_used = tokens_used
            if generation_latency_ms is not None:
                existing.generation_latency_ms = generation_latency_ms
            return await self.update(existing)

        analysis = EligibilityAnalysis(
            organization_id=organization_id,
            tender_id=tender_id,
            company_profile_id=company_profile_id,
            overall_eligible=overall_eligible,
            eligibility_score=eligibility_score,
            criteria_results=criteria_results,
            missing_requirements=missing_requirements,
            version=1,
            model_used=generation_model,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        return await self.create(analysis)

    async def list_by_organization(self, organization_id: UUID, page: int = 1,
                                    page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[EligibilityAnalysis], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(EligibilityAnalysis).where(
            EligibilityAnalysis.organization_id == organization_id
        ).order_by(EligibilityAnalysis.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(EligibilityAnalysis.eligibility_analysis_id)).where(
            EligibilityAnalysis.organization_id == organization_id
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total

    async def delete(self, analysis_id: UUID) -> bool:
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            return False
        await self.session.delete(analysis)
        await self.session.flush()
        return True


class ComplianceMatrixRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tender_id(self, tender_id: UUID, organization_id: UUID = None) -> Optional[ComplianceMatrix]:
        query = select(ComplianceMatrix).where(ComplianceMatrix.tender_id == tender_id)
        if organization_id is not None:
            query = query.where(ComplianceMatrix.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_proposal_id(self, proposal_id: UUID, organization_id: UUID = None) -> Optional[ComplianceMatrix]:
        query = select(ComplianceMatrix).where(ComplianceMatrix.proposal_id == proposal_id)
        if organization_id is not None:
            query = query.where(ComplianceMatrix.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, matrix_id: UUID, organization_id: UUID = None) -> Optional[ComplianceMatrix]:
        query = select(ComplianceMatrix).where(ComplianceMatrix.compliance_matrix_id == matrix_id)
        if organization_id is not None:
            query = query.where(ComplianceMatrix.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, matrix: ComplianceMatrix) -> ComplianceMatrix:
        self.session.add(matrix)
        await self.session.flush()
        await self.session.refresh(matrix)
        return matrix

    async def update(self, matrix: ComplianceMatrix) -> ComplianceMatrix:
        await self.session.flush()
        await self.session.refresh(matrix)
        return matrix

    async def upsert(self, organization_id: UUID, tender_id: UUID, proposal_id: UUID,
                     overall_compliance_score: int, requirement_results: list,
                     mandatory_met: int = 0, mandatory_total: int = 0,
                     desirable_met: int = 0, desirable_total: int = 0,
                     generation_model: str = None, prompt_hash: str = None,
                     tokens_used: int = None, generation_latency_ms: int = None,
                     metadata: dict = None) -> ComplianceMatrix:
        existing = await self.get_by_tender_id(tender_id, organization_id)
        if existing:
            existing.overall_compliance_score = overall_compliance_score
            existing.requirement_results = requirement_results
            existing.mandatory_met = mandatory_met
            existing.mandatory_total = mandatory_total
            existing.desirable_met = desirable_met
            existing.desirable_total = desirable_total
            existing.version += 1
            if generation_model:
                existing.model_used = generation_model
            if prompt_hash:
                existing.prompt_hash = prompt_hash
            if tokens_used is not None:
                existing.tokens_used = tokens_used
            if generation_latency_ms is not None:
                existing.generation_latency_ms = generation_latency_ms
            return await self.update(existing)

        matrix = ComplianceMatrix(
            organization_id=organization_id,
            tender_id=tender_id,
            proposal_id=proposal_id,
            overall_compliance_score=overall_compliance_score,
            requirement_results=requirement_results,
            mandatory_met=mandatory_met,
            mandatory_total=mandatory_total,
            desirable_met=desirable_met,
            desirable_total=desirable_total,
            version=1,
            model_used=generation_model,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        return await self.create(matrix)

    async def list_by_organization(self, organization_id: UUID, page: int = 1,
                                    page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[List[ComplianceMatrix], int]:
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        offset = (page - 1) * page_size

        query = select(ComplianceMatrix).where(
            ComplianceMatrix.organization_id == organization_id
        ).order_by(ComplianceMatrix.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        count_query = select(func.count(ComplianceMatrix.compliance_matrix_id)).where(
            ComplianceMatrix.organization_id == organization_id
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        return list(items), total

    async def delete(self, matrix_id: UUID) -> bool:
        matrix = await self.get_by_id(matrix_id)
        if not matrix:
            return False
        await self.session.delete(matrix)
        await self.session.flush()
        return True
