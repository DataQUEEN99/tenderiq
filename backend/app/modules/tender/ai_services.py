from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, List, Tuple, Dict, Any
from app.modules.tender.ai_repositories import (
    TenderSummaryRepository, EligibilityAnalysisRepository,
    ComplianceMatrixRepository, DocumentContentRepository,
    DocumentProcessingRepository
)
from app.modules.tender.models import TenderSummary, EligibilityAnalysis, ComplianceMatrix, Tender
from app.modules.document.models import DocumentContent, DocumentProcessing, DocumentStatus
from app.shared.exceptions.custom_exceptions import ResourceNotFoundException, ValidationException
from app.shared.logging.logger import app_logger


class TenderSummaryService:
    def __init__(self, session: AsyncSession):
        self.repo = TenderSummaryRepository(session)
        self.session = session

    async def create_summary(self, organization_id: UUID, tender_id: UUID, summary_type: str,
                             content: str, generation_model: str = None,
                             generation_prompt: str = None, metadata: dict = None) -> TenderSummary:
        # Verify tender exists and belongs to organization
        from app.modules.tender.repository import TenderRepository
        tender_repo = TenderRepository(self.session)
        tender = await tender_repo.get_by_id(tender_id)
        if not tender or tender.organization_id != organization_id:
            raise ResourceNotFoundException("Tender not found")

        summary = await self.repo.upsert(
            organization_id=organization_id,
            tender_id=tender_id,
            summary_type=summary_type,
            content=content,
            generation_model=generation_model,
            generation_prompt=generation_prompt,
            metadata=metadata,
        )
        app_logger.info(f"Tender summary created/updated", extra={
            "tender_id": str(tender_id),
            "summary_type": summary_type
        })
        return summary

    async def get_summary(self, organization_id: UUID, tender_id: UUID) -> Optional[TenderSummary]:
        summary = await self.repo.get_by_tender_id(tender_id)
        if summary and summary.organization_id != organization_id:
            return None
        return summary

    async def list_summaries(self, organization_id: UUID, page: int = 1,
                             page_size: int = 20) -> Tuple[List[TenderSummary], int]:
        return await self.repo.list_by_organization(organization_id, page, page_size)


class EligibilityAnalysisService:
    def __init__(self, session: AsyncSession):
        self.repo = EligibilityAnalysisRepository(session)
        self.session = session

    async def create_analysis(self, organization_id: UUID, tender_id: UUID,
                              company_profile_id: UUID, is_eligible: bool,
                              eligibility_score: int = None,
                              mandatory_requirements: list = None,
                              optional_requirements: list = None,
                              gaps: list = None, recommendations: list = None,
                              generation_model: str = None, generation_prompt: str = None,
                              metadata: dict = None) -> EligibilityAnalysis:
        # Verify tender exists and belongs to organization
        from app.modules.tender.repository import TenderRepository
        tender_repo = TenderRepository(self.session)
        tender = await tender_repo.get_by_id(tender_id)
        if not tender or tender.organization_id != organization_id:
            raise ResourceNotFoundException("Tender not found")

        # Verify company profile belongs to organization
        from app.modules.company.repository import CompanyRepository
        company_repo = CompanyRepository(self.session)
        company = await company_repo.get_by_id(company_profile_id)
        if not company or company.organization_id != organization_id:
            raise ValidationException("Company profile not found or not accessible")

        analysis = await self.repo.upsert(
            organization_id=organization_id,
            tender_id=tender_id,
            company_profile_id=company_profile_id,
            is_eligible=is_eligible,
            eligibility_score=eligibility_score,
            mandatory_requirements=mandatory_requirements,
            optional_requirements=optional_requirements,
            gaps=gaps,
            recommendations=recommendations,
            generation_model=generation_model,
            generation_prompt=generation_prompt,
            metadata=metadata,
        )
        app_logger.info(f"Eligibility analysis created/updated", extra={
            "tender_id": str(tender_id),
            "is_eligible": is_eligible
        })
        return analysis

    async def get_analysis(self, organization_id: UUID, tender_id: UUID) -> Optional[EligibilityAnalysis]:
        analysis = await self.repo.get_by_tender_id(tender_id)
        if analysis and analysis.organization_id != organization_id:
            return None
        return analysis

    async def list_analyses(self, organization_id: UUID, page: int = 1,
                            page_size: int = 20) -> Tuple[List[EligibilityAnalysis], int]:
        return await self.repo.list_by_organization(organization_id, page, page_size)


class ComplianceMatrixService:
    def __init__(self, session: AsyncSession):
        self.repo = ComplianceMatrixRepository(session)
        self.session = session

    async def create_matrix(self, organization_id: UUID, tender_id: UUID,
                            proposal_id: UUID, compliance_score: int,
                            requirements: list,
                            non_compliant_items: list = None,
                            partially_compliant_items: list = None,
                            generation_model: str = None, generation_prompt: str = None,
                            metadata: dict = None) -> ComplianceMatrix:
        # Verify tender exists and belongs to organization
        from app.modules.tender.repository import TenderRepository
        tender_repo = TenderRepository(self.session)
        tender = await tender_repo.get_by_id(tender_id)
        if not tender or tender.organization_id != organization_id:
            raise ResourceNotFoundException("Tender not found")

        # Verify proposal exists and belongs to organization
        from app.modules.proposal.repository import ProposalRepository
        proposal_repo = ProposalRepository(self.session)
        proposal = await proposal_repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id:
            raise ValidationException("Proposal not found or not accessible")

        # Verify proposal belongs to tender
        if proposal.tender_id != tender_id:
            raise ValidationException("Proposal does not belong to this tender")

        matrix = await self.repo.upsert(
            organization_id=organization_id,
            tender_id=tender_id,
            proposal_id=proposal_id,
            compliance_score=compliance_score,
            requirements=requirements,
            non_compliant_items=non_compliant_items,
            partially_compliant_items=partially_compliant_items,
            generation_model=generation_model,
            generation_prompt=generation_prompt,
            metadata=metadata,
        )
        app_logger.info(f"Compliance matrix created/updated", extra={
            "tender_id": str(tender_id),
            "proposal_id": str(proposal_id),
            "compliance_score": compliance_score
        })
        return matrix

    async def get_matrix(self, organization_id: UUID, tender_id: UUID) -> Optional[ComplianceMatrix]:
        matrix = await self.repo.get_by_tender_id(tender_id)
        if matrix and matrix.organization_id != organization_id:
            return None
        return matrix

    async def list_matrices(self, organization_id: UUID, page: int = 1,
                            page_size: int = 20) -> Tuple[List[ComplianceMatrix], int]:
        return await self.repo.list_by_organization(organization_id, page, page_size)


class DocumentContentService:
    def __init__(self, session: AsyncSession):
        self.repo = DocumentContentRepository(session)
        self.session = session

    async def save_content(self, document_id: UUID, organization_id: UUID, text_content: str,
                           page_count: int = None, char_count: int = None,
                           extraction_method: str = None, metadata: dict = None) -> DocumentContent:
        # Verify document exists and belongs to organization
        from app.modules.document.repository import DocumentRepository
        doc_repo = DocumentRepository(self.session)
        document = await doc_repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            raise ResourceNotFoundException("Document not found")

        content = await self.repo.upsert(
            document_id=document_id,
            text_content=text_content,
            page_count=page_count,
            char_count=char_count,
            extraction_method=extraction_method,
            metadata=metadata,
        )
        app_logger.info(f"Document content saved", extra={"document_id": str(document_id)})
        return content

    async def get_content(self, organization_id: UUID, document_id: UUID) -> Optional[DocumentContent]:
        from app.modules.document.repository import DocumentRepository
        doc_repo = DocumentRepository(self.session)
        document = await doc_repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            return None
        return await self.repo.get_by_document_id(document_id)


class DocumentProcessingService:
    def __init__(self, session: AsyncSession):
        self.repo = DocumentProcessingRepository(session)
        self.session = session

    async def start_processing(self, document_id: UUID, organization_id: UUID) -> DocumentProcessing:
        from app.modules.document.repository import DocumentRepository
        doc_repo = DocumentRepository(self.session)
        document = await doc_repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            raise ResourceNotFoundException("Document not found")

        from datetime import datetime, timezone
        processing = await self.repo.upsert(
            document_id=document_id,
            status=DocumentStatus.PROCESSING,
            processing_started_at=datetime.now(timezone.utc),
        )
        # Also update document status
        await doc_repo.update_status(document_id, DocumentStatus.PROCESSING)
        app_logger.info(f"Document processing started", extra={"document_id": str(document_id)})
        return processing

    async def complete_processing(self, document_id: UUID, organization_id: UUID,
                                  chunk_count: int, vector_collection: str,
                                  text_content: str = None, page_count: int = None,
                                  char_count: int = None, extraction_method: str = None) -> DocumentProcessing:
        from app.modules.document.repository import DocumentRepository
        doc_repo = DocumentRepository(self.session)
        document = await doc_repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            raise ResourceNotFoundException("Document not found")

        from datetime import datetime, timezone
        processing = await self.repo.upsert(
            document_id=document_id,
            status=DocumentStatus.PROCESSED,
            chunk_count=chunk_count,
            vector_collection=vector_collection,
            processing_completed_at=datetime.now(timezone.utc),
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
        await doc_repo.update_status(
            document_id, DocumentStatus.PROCESSED,
            chunk_count=chunk_count, vector_collection=vector_collection
        )

        app_logger.info(f"Document processing completed", extra={
            "document_id": str(document_id),
            "chunk_count": chunk_count
        })
        return processing

    async def fail_processing(self, document_id: UUID, organization_id: UUID,
                              error_message: str) -> DocumentProcessing:
        from app.modules.document.repository import DocumentRepository
        doc_repo = DocumentRepository(self.session)
        document = await doc_repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            raise ResourceNotFoundException("Document not found")

        from datetime import datetime, timezone
        processing = await self.repo.upsert(
            document_id=document_id,
            status=DocumentStatus.FAILED,
            error_message=error_message,
            processing_completed_at=datetime.now(timezone.utc),
        )

        # Update document status
        await doc_repo.update_status(document_id, DocumentStatus.FAILED, error_message=error_message)

        app_logger.error(f"Document processing failed", extra={
            "document_id": str(document_id),
            "error": error_message
        })
        return processing

    async def get_processing(self, organization_id: UUID, document_id: UUID) -> Optional[DocumentProcessing]:
        from app.modules.document.repository import DocumentRepository
        doc_repo = DocumentRepository(self.session)
        document = await doc_repo.get_by_id(document_id)
        if not document or document.organization_id != organization_id:
            return None
        return await self.repo.get_by_document_id(document_id)