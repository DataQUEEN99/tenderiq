from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple, Dict, Any
from app.modules.tender.ai_repositories import (
    TenderSummaryRepository, EligibilityAnalysisRepository,
    ComplianceMatrixRepository
)
from app.modules.document.repository import DocumentContentRepository, DocumentProcessingRepository
from app.modules.tender.models import TenderSummary, EligibilityAnalysis, Tender
from app.modules.proposal.models import ComplianceMatrix
from app.modules.document.models import DocumentContent, DocumentProcessing, DocumentStatus
from app.shared.exceptions.custom_exceptions import ResourceNotFoundException, ValidationException
from app.shared.logging.logger import app_logger


class TenderSummaryService:
    def __init__(self, session: AsyncSession):
        self.repo = TenderSummaryRepository(session)
        self.session = session

    async def create_summary(self, organization_id: UUID, tender_id: UUID, summary_type: str,
                             summary_text: str, generation_model: str = None,
                             prompt_hash: str = None, tokens_used: int = None,
                             generation_latency_ms: int = None) -> TenderSummary:
        # Verify tender exists and belongs to organization
        from app.modules.tender.service import TenderService
        tender_service = TenderService(self.session)
        tender = await tender_service.get_by_id(tender_id, organization_id)
        if not tender:
            raise ResourceNotFoundException("Tender not found")

        summary = await self.repo.upsert(
            organization_id=organization_id,
            tender_id=tender_id,
            summary_type=summary_type,
            summary_text=summary_text,
            generation_model=generation_model,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        app_logger.info(f"Tender summary created/updated", extra={
            "tender_id": str(tender_id),
            "summary_type": summary_type
        })
        return summary

    async def get_summary(self, organization_id: UUID, tender_id: UUID) -> Optional[TenderSummary]:
        return await self.repo.get_by_tender_id(tender_id, organization_id)

    async def list_summaries(self, organization_id: UUID, page: int = 1,
                             page_size: int = 20) -> Tuple[List[TenderSummary], int]:
        return await self.repo.list_by_organization(organization_id, page, page_size)


class EligibilityAnalysisService:
    def __init__(self, session: AsyncSession):
        self.repo = EligibilityAnalysisRepository(session)
        self.session = session

    async def create_analysis(self, organization_id: UUID, tender_id: UUID,
                              company_profile_id: UUID, overall_eligible: bool,
                              eligibility_score: int = None,
                              criteria_results: list = None, missing_requirements: list = None,
                              generation_model: str = None, prompt_hash: str = None,
                              tokens_used: int = None, generation_latency_ms: int = None) -> EligibilityAnalysis:
        # Verify tender exists and belongs to organization
        from app.modules.tender.service import TenderService
        tender_service = TenderService(self.session)
        tender = await tender_service.get_by_id(tender_id, organization_id)
        if not tender:
            raise ResourceNotFoundException("Tender not found")

        # Verify company profile belongs to organization
        from app.modules.company.service import CompanyService
        company_service = CompanyService(self.session)
        company = await company_service.get_by_organization(organization_id)
        if not company or company.company_profile_id != company_profile_id:
            raise ValidationException("Company profile not found or not accessible")

        analysis = await self.repo.upsert(
            organization_id=organization_id,
            tender_id=tender_id,
            company_profile_id=company_profile_id,
            overall_eligible=overall_eligible,
            eligibility_score=eligibility_score,
            criteria_results=criteria_results,
            missing_requirements=missing_requirements,
            generation_model=generation_model,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        app_logger.info(f"Eligibility analysis created/updated", extra={
            "tender_id": str(tender_id),
            "overall_eligible": overall_eligible
        })
        return analysis

    async def get_analysis(self, organization_id: UUID, tender_id: UUID) -> Optional[EligibilityAnalysis]:
        return await self.repo.get_by_tender_id(tender_id, organization_id)

    async def list_analyses(self, organization_id: UUID, page: int = 1,
                            page_size: int = 20) -> Tuple[List[EligibilityAnalysis], int]:
        return await self.repo.list_by_organization(organization_id, page, page_size)


class ComplianceMatrixService:
    def __init__(self, session: AsyncSession):
        self.repo = ComplianceMatrixRepository(session)
        self.session = session

    async def create_matrix(self, organization_id: UUID, tender_id: UUID,
                            proposal_id: UUID, overall_compliance_score: int,
                            requirement_results: list,
                            mandatory_met: int = 0, mandatory_total: int = 0,
                            desirable_met: int = 0, desirable_total: int = 0,
                            generation_model: str = None, prompt_hash: str = None,
                            tokens_used: int = None, generation_latency_ms: int = None) -> ComplianceMatrix:
        # Verify tender exists and belongs to organization
        from app.modules.tender.service import TenderService
        tender_service = TenderService(self.session)
        tender = await tender_service.get_by_id(tender_id, organization_id)
        if not tender:
            raise ResourceNotFoundException("Tender not found")

        # Verify proposal exists and belongs to organization
        from app.modules.proposal.service import ProposalService
        proposal_service = ProposalService(self.session)
        proposal = await proposal_service.get_by_id(proposal_id, organization_id)
        if not proposal:
            raise ValidationException("Proposal not found or not accessible")

        # Verify proposal belongs to tender
        if proposal.tender_id != tender_id:
            raise ValidationException("Proposal does not belong to this tender")

        matrix = await self.repo.upsert(
            organization_id=organization_id,
            tender_id=tender_id,
            proposal_id=proposal_id,
            overall_compliance_score=overall_compliance_score,
            requirement_results=requirement_results,
            mandatory_met=mandatory_met,
            mandatory_total=mandatory_total,
            desirable_met=desirable_met,
            desirable_total=desirable_total,
            generation_model=generation_model,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        app_logger.info(f"Compliance matrix created/updated", extra={
            "tender_id": str(tender_id),
            "proposal_id": str(proposal_id),
            "overall_compliance_score": overall_compliance_score
        })
        return matrix

    async def get_matrix(self, organization_id: UUID, tender_id: UUID) -> Optional[ComplianceMatrix]:
        return await self.repo.get_by_tender_id(tender_id, organization_id)

    async def get_matrix_by_proposal_id(self, organization_id: UUID, proposal_id: UUID) -> Optional[ComplianceMatrix]:
        return await self.repo.get_by_proposal_id(proposal_id, organization_id)

    async def list_matrices(self, organization_id: UUID, page: int = 1,
                            page_size: int = 20) -> Tuple[List[ComplianceMatrix], int]:
        return await self.repo.list_by_organization(organization_id, page, page_size)


class DocumentContentService:
    def __init__(self, session: AsyncSession):
        self.repo = DocumentContentRepository(session)
        self.session = session

    async def save_content(self, document_id: UUID, organization_id: UUID, text_content: str,
                           page_count: int = None, char_count: int = None,
                           extraction_method: str = None) -> DocumentContent:
        # Verify document exists and belongs to organization
        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        document = await doc_service.get_by_id(document_id, organization_id)
        if not document:
            raise ResourceNotFoundException("Document not found")

        content = await self.repo.upsert(
            document_id=document_id,
            extracted_text=text_content,
            page_count=page_count,
            character_count=char_count,
            extraction_method=extraction_method,
            organization_id=organization_id,
        )
        app_logger.info(f"Document content saved", extra={"document_id": str(document_id)})
        return content

    async def get_content(self, organization_id: UUID, document_id: UUID) -> Optional[DocumentContent]:
        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        document = await doc_service.get_by_id(document_id, organization_id)
        if not document:
            return None
        return await self.repo.get_by_document_id(document_id, organization_id)


class DocumentProcessingService:
    def __init__(self, session: AsyncSession):
        self.repo = DocumentProcessingRepository(session)
        self.session = session

    async def start_processing(self, document_id: UUID, organization_id: UUID) -> DocumentProcessing:
        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        document = await doc_service.get_by_id(document_id, organization_id)
        if not document:
            raise ResourceNotFoundException("Document not found")

        from datetime import datetime, timezone
        processing = await self.repo.upsert(
            document_id=document_id,
            status="processing",
            started_at=datetime.now(timezone.utc),
            organization_id=organization_id,
        )
        # Also update document status
        await doc_service.update_status(document_id, organization_id, DocumentStatus.PROCESSING)
        app_logger.info(f"Document processing started", extra={"document_id": str(document_id)})
        return processing

    async def complete_processing(self, document_id: UUID, organization_id: UUID,
                                  chunk_count: int, vector_collection: str,
                                  text_content: str = None, page_count: int = None,
                                  char_count: int = None, extraction_method: str = None) -> DocumentProcessing:
        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        document = await doc_service.get_by_id(document_id, organization_id)
        if not document:
            raise ResourceNotFoundException("Document not found")

        from datetime import datetime, timezone
        processing = await self.repo.upsert(
            document_id=document_id,
            status="processed",
            completed_at=datetime.now(timezone.utc),
            organization_id=organization_id,
        )

        # Also save content if provided
        if text_content:
            content_service = DocumentContentService(self.session)
            await content_service.save_content(
                document_id=document_id,
                organization_id=organization_id,
                text_content=text_content,
                page_count=page_count,
                char_count=char_count,
                extraction_method=extraction_method,
            )

        # Update document status
        await doc_service.update_status(
            document_id, organization_id, DocumentStatus.PROCESSED,
            chunk_count=chunk_count, vector_collection=vector_collection
        )

        app_logger.info(f"Document processing completed", extra={
            "document_id": str(document_id),
            "chunk_count": chunk_count
        })
        return processing

    async def fail_processing(self, document_id: UUID, organization_id: UUID,
                              error_message: str) -> DocumentProcessing:
        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        document = await doc_service.get_by_id(document_id, organization_id)
        if not document:
            raise ResourceNotFoundException("Document not found")

        from datetime import datetime, timezone
        processing = await self.repo.upsert(
            document_id=document_id,
            status="failed",
            error_message=error_message,
            completed_at=datetime.now(timezone.utc),
            organization_id=organization_id,
        )

        # Update document status
        await doc_service.update_status(document_id, organization_id, DocumentStatus.FAILED, error_message=error_message)

        app_logger.error(f"Document processing failed", extra={
            "document_id": str(document_id),
            "error": error_message
        })
        return processing

    async def get_processing(self, organization_id: UUID, document_id: UUID) -> Optional[DocumentProcessing]:
        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        document = await doc_service.get_by_id(document_id, organization_id)
        if not document:
            return None
        return await self.repo.get_by_document_id(document_id, organization_id)