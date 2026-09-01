from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple
from app.modules.tender.models import TenderSummary, EligibilityAnalysis, ComplianceMatrix
from app.shared.database.base import BaseModel
from app.shared.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class TenderSummaryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tender_id(self, tender_id: UUID) -> Optional[TenderSummary]:
        result = await self.session.execute(
            select(TenderSummary).where(TenderSummary.tender_id == tender_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, summary_id: UUID) -> Optional[TenderSummary]:
        result = await self.session.execute(
            select(TenderSummary).where(TenderSummary.tender_summary_id == summary_id)
        )
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
                     content: str, generation_model: str = None, generation_prompt: str = None,
                     metadata: dict = None) -> TenderSummary:
        existing = await self.get_by_tender_id(tender_id)
        if existing:
            existing.summary_type = summary_type
            existing.content = content
            existing.version += 1
            if generation_model:
                existing.generation_model = generation_model
            if generation_prompt:
                existing.generation_prompt = generation_prompt
            if metadata:
                existing.metadata = metadata
            return await self.update(existing)

        summary = TenderSummary(
            organization_id=organization_id,
            tender_id=tender_id,
            summary_type=summary_type,
            content=content,
            version=1,
            generation_model=generation_model,
            generation_prompt=generation_prompt,
            metadata=metadata,
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

    async def get_by_tender_id(self, tender_id: UUID) -> Optional[EligibilityAnalysis]:
        result = await self.session.execute(
            select(EligibilityAnalysis).where(EligibilityAnalysis.tender_id == tender_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, analysis_id: UUID) -> Optional[EligibilityAnalysis]:
        result = await self.session.execute(
            select(EligibilityAnalysis).where(EligibilityAnalysis.eligibility_analysis_id == analysis_id)
        )
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
                     is_eligible: bool, eligibility_score: int = None,
                     mandatory_requirements: list = None, optional_requirements: list = None,
                     gaps: list = None, recommendations: list = None,
                     generation_model: str = None, generation_prompt: str = None,
                     metadata: dict = None) -> EligibilityAnalysis:
        existing = await self.get_by_tender_id(tender_id)
        if existing:
            existing.is_eligible = is_eligible
            if eligibility_score is not None:
                existing.eligibility_score = eligibility_score
            if mandatory_requirements is not None:
                existing.mandatory_requirements = mandatory_requirements
            if optional_requirements is not None:
                existing.optional_requirements = optional_requirements
            if gaps is not None:
                existing.gaps = gaps
            if recommendations is not None:
                existing.recommendations = recommendations
            existing.version += 1
            if generation_model:
                existing.generation_model = generation_model
            if generation_prompt:
                existing.generation_prompt = generation_prompt
            if metadata:
                existing.metadata = metadata
            return await self.update(existing)

        analysis = EligibilityAnalysis(
            organization_id=organization_id,
            tender_id=tender_id,
            company_profile_id=company_profile_id,
            is_eligible=is_eligible,
            eligibility_score=eligibility_score,
            mandatory_requirements=mandatory_requirements,
            optional_requirements=optional_requirements,
            gaps=gaps,
            recommendations=recommendations,
            version=1,
            generation_model=generation_model,
            generation_prompt=generation_prompt,
            metadata=metadata,
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

    async def get_by_tender_id(self, tender_id: UUID) -> Optional[ComplianceMatrix]:
        result = await self.session.execute(
            select(ComplianceMatrix).where(ComplianceMatrix.tender_id == tender_id)
        )
        return result.scalar_one_or_none()

    async def get_by_proposal_id(self, proposal_id: UUID) -> Optional[ComplianceMatrix]:
        result = await self.session.execute(
            select(ComplianceMatrix).where(ComplianceMatrix.proposal_id == proposal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, matrix_id: UUID) -> Optional[ComplianceMatrix]:
        result = await self.session.execute(
            select(ComplianceMatrix).where(ComplianceMatrix.compliance_matrix_id == matrix_id)
        )
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
                     compliance_score: int, requirements: list,
                     non_compliant_items: list = None, partially_compliant_items: list = None,
                     generation_model: str = None, generation_prompt: str = None,
                     metadata: dict = None) -> ComplianceMatrix:
        existing = await self.get_by_tender_id(tender_id)
        if existing:
            existing.compliance_score = compliance_score
            existing.requirements = requirements
            if non_compliant_items is not None:
                existing.non_compliant_items = non_compliant_items
            if partially_compliant_items is not None:
                existing.partially_compliant_items = partially_compliant_items
            existing.version += 1
            if generation_model:
                existing.generation_model = generation_model
            if generation_prompt:
                existing.generation_prompt = generation_prompt
            if metadata:
                existing.metadata = metadata
            return await self.update(existing)

        matrix = ComplianceMatrix(
            organization_id=organization_id,
            tender_id=tender_id,
            proposal_id=proposal_id,
            compliance_score=compliance_score,
            requirements=requirements,
            non_compliant_items=non_compliant_items,
            partially_compliant_items=partially_compliant_items,
            version=1,
            generation_model=generation_model,
            generation_prompt=generation_prompt,
            metadata=metadata,
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