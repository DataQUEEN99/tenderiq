from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Tuple, Optional
from app.modules.tender.repository import TenderRepository
from app.modules.tender.models import Tender, TenderStatus, TenderDocument
from app.modules.tender.schemas import TenderCreate, TenderUpdate, TenderStatusUpdate, TenderResponse, TenderDetailResponse
from app.modules.tender.ai_services import TenderSummaryService, EligibilityAnalysisService, ComplianceMatrixService
from app.modules.document.models import Document
from app.shared.exceptions.custom_exceptions import ValidationException, ResourceNotFoundException, BusinessRuleViolationException
from app.shared.logging.logger import app_logger


class TenderService:
    def __init__(self, session: AsyncSession):
        self.repo = TenderRepository(session)
        self.session = session

    async def create(self, organization_id: UUID, created_by: UUID, request: TenderCreate) -> TenderResponse:
        existing = await self.repo.get_by_reference(organization_id, request.reference_number)
        if existing:
            raise ValidationException("Tender reference number already exists in this organization")

        tender = Tender(
            title=request.title,
            reference_number=request.reference_number,
            description=request.description,
            issuing_authority=request.issuing_authority,
            submission_deadline=request.submission_deadline,
            estimated_value=request.estimated_value,
            currency=request.currency,
            contract_duration=request.contract_duration,
            organization_id=organization_id,
            created_by=created_by,
        )

        tender = await self.repo.create(tender)
        app_logger.info(f"Tender created", extra={"tender_id": str(tender.tender_id), "reference": tender.reference_number})
        return TenderResponse.model_validate(tender)

    async def get_by_id(self, tender_id: UUID, organization_id: UUID) -> TenderResponse:
        tender = await self.repo.get_by_id(tender_id, organization_id)
        if not tender or tender.status == TenderStatus.ARCHIVED:
            raise ResourceNotFoundException("Tender not found")
        return TenderResponse.model_validate(tender)

    async def get_detail(self, tender_id: UUID, organization_id: UUID) -> TenderDetailResponse:
        tender = await self.repo.get_by_id_with_docs(tender_id, organization_id)
        if not tender or tender.status == TenderStatus.ARCHIVED:
            raise ResourceNotFoundException("Tender not found")

        response = TenderDetailResponse.model_validate(tender)
        response.documents = [doc.document for doc in tender.documents if doc.document and doc.document.status != DocumentStatus.DELETED]
        return response

    async def update(self, tender_id: UUID, organization_id: UUID, request: TenderUpdate) -> TenderResponse:
        tender = await self.repo.get_by_id(tender_id, organization_id)
        if not tender or tender.status == TenderStatus.ARCHIVED:
            raise ResourceNotFoundException("Tender not found")

        if request.reference_number and request.reference_number != tender.reference_number:
            existing = await self.repo.get_by_reference(organization_id, request.reference_number)
            if existing:
                raise ValidationException("Tender reference number already exists in this organization")
            tender.reference_number = request.reference_number

        if request.title:
            tender.title = request.title
        if request.description is not None:
            tender.description = request.description
        if request.issuing_authority is not None:
            tender.issuing_authority = request.issuing_authority
        if request.submission_deadline is not None:
            tender.submission_deadline = request.submission_deadline
        if request.estimated_value is not None:
            tender.estimated_value = request.estimated_value
        if request.currency is not None:
            tender.currency = request.currency
        if request.contract_duration is not None:
            tender.contract_duration = request.contract_duration

        tender = await self.repo.update(tender)
        app_logger.info(f"Tender updated", extra={"tender_id": str(tender_id)})
        return TenderResponse.model_validate(tender)

    async def update_status(self, tender_id: UUID, organization_id: UUID, request: TenderStatusUpdate) -> TenderResponse:
        tender = await self.repo.get_by_id(tender_id, organization_id)
        if not tender or tender.status == TenderStatus.ARCHIVED:
            raise ResourceNotFoundException("Tender not found")

        valid_transitions = {
            TenderStatus.DRAFT: [TenderStatus.PUBLISHED, TenderStatus.ARCHIVED],
            TenderStatus.PUBLISHED: [TenderStatus.IN_PROGRESS, TenderStatus.ARCHIVED],
            TenderStatus.IN_PROGRESS: [TenderStatus.SUBMITTED, TenderStatus.ARCHIVED],
            TenderStatus.SUBMITTED: [TenderStatus.AWARDED, TenderStatus.LOST, TenderStatus.ARCHIVED],
            TenderStatus.AWARDED: [TenderStatus.ARCHIVED],
            TenderStatus.LOST: [TenderStatus.ARCHIVED],
        }

        if tender.status in valid_transitions and request.status not in valid_transitions[tender.status]:
            raise BusinessRuleViolationException(f"Invalid status transition from {tender.status.value} to {request.status.value}")

        tender.status = request.status
        tender = await self.repo.update(tender)
        app_logger.info(f"Tender status updated", extra={"tender_id": str(tender_id), "status": request.status.value})
        return TenderResponse.model_validate(tender)

    async def attach_documents(self, tender_id: UUID, organization_id: UUID, document_ids: List[UUID]) -> List[str]:
        tender = await self.repo.get_by_id(tender_id, organization_id)
        if not tender or tender.status == TenderStatus.ARCHIVED:
            raise ResourceNotFoundException("Tender not found")

        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        await doc_service.verify_documents_exist(organization_id, document_ids)

        existing = await self.repo.get_attached_documents(tender_id, organization_id)
        for doc_id in document_ids:
            if any(d.document_id == doc_id for d in existing):
                raise ValidationException(f"Document {doc_id} already attached to this tender")

        await self.repo.attach_documents(tender_id, organization_id, document_ids)
        attached = [str(doc_id) for doc_id in document_ids]

        app_logger.info(f"Documents attached to tender", extra={"tender_id": str(tender_id), "count": len(attached)})
        return attached

    async def detach_document(self, tender_id: UUID, organization_id: UUID, document_id: UUID) -> None:
        tender = await self.repo.get_by_id(tender_id, organization_id)
        if not tender or tender.status == TenderStatus.ARCHIVED:
            raise ResourceNotFoundException("Tender not found")

        success = await self.repo.detach_document(tender_id, organization_id, document_id)
        if not success:
            raise ResourceNotFoundException("Document not attached to this tender")

        app_logger.info(f"Document detached from tender", extra={"tender_id": str(tender_id), "document_id": str(document_id)})

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = 20,
                   status: TenderStatus = None, search: str = None) -> Tuple[List[TenderResponse], int]:
        items, total = await self.repo.list(organization_id, page, page_size, status, search)
        return [TenderResponse.model_validate(item) for item in items], total

    async def delete(self, tender_id: UUID, organization_id: UUID) -> None:
        tender = await self.repo.get_by_id(tender_id, organization_id)
        if not tender:
            raise ResourceNotFoundException("Tender not found")

        await self.repo.soft_delete(tender_id, organization_id)
        app_logger.info(f"Tender deleted", extra={"tender_id": str(tender_id)})

    # TenderSummary delegation
    async def create_summary(self, organization_id: UUID, tender_id: UUID,
                             summary_type: str, summary_text: str,
                             model_used: str = None, prompt_hash: str = None,
                             tokens_used: int = None, generation_latency_ms: int = None,
                             source_document_ids: list = None) -> 'TenderSummaryResponse':
        """Delegate to TenderSummaryService."""
        from app.modules.tender.schemas import TenderSummaryResponse
        service = TenderSummaryService(self.session)
        summary = await service.create_summary(
            organization_id=organization_id,
            tender_id=tender_id,
            summary_type=summary_type,
            summary_text=summary_text,
            generation_model=model_used,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        return TenderSummaryResponse.model_validate(summary)

    async def get_summary(self, organization_id: UUID, tender_id: UUID) -> 'TenderSummaryResponse':
        """Delegate to TenderSummaryService."""
        from app.modules.tender.schemas import TenderSummaryResponse
        service = TenderSummaryService(self.session)
        summary = await service.get_summary(organization_id, tender_id)
        if not summary:
            raise ResourceNotFoundException("Tender summary not found")
        return TenderSummaryResponse.model_validate(summary)

    # EligibilityAnalysis delegation
    async def create_eligibility_analysis(self, organization_id: UUID, tender_id: UUID,
                                          company_profile_id: UUID, overall_eligible: bool,
                                          eligibility_score: int = None,
                                          criteria_results: list = None, missing_requirements: list = None,
                                          model_used: str = None, prompt_hash: str = None,
                                          tokens_used: int = None, generation_latency_ms: int = None) -> 'EligibilityAnalysisResponse':
        """Delegate to EligibilityAnalysisService."""
        from app.modules.tender.schemas import EligibilityAnalysisResponse
        service = EligibilityAnalysisService(self.session)
        analysis = await service.create_analysis(
            organization_id=organization_id,
            tender_id=tender_id,
            company_profile_id=company_profile_id,
            overall_eligible=overall_eligible,
            eligibility_score=eligibility_score,
            criteria_results=criteria_results,
            missing_requirements=missing_requirements,
            generation_model=model_used,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        return EligibilityAnalysisResponse.model_validate(analysis)

    async def get_eligibility_analysis(self, organization_id: UUID, tender_id: UUID) -> 'EligibilityAnalysisResponse':
        """Delegate to EligibilityAnalysisService."""
        from app.modules.tender.schemas import EligibilityAnalysisResponse
        service = EligibilityAnalysisService(self.session)
        analysis = await service.get_analysis(organization_id, tender_id)
        if not analysis:
            raise ResourceNotFoundException("Eligibility analysis not found")
        return EligibilityAnalysisResponse.model_validate(analysis)

    # ComplianceMatrix delegation
    async def create_compliance_matrix(self, organization_id: UUID, tender_id: UUID,
                                       proposal_id: UUID, overall_compliance_score: int,
                                       mandatory_met: int = 0, mandatory_total: int = 0,
                                       desirable_met: int = 0, desirable_total: int = 0,
                                       requirement_results: list = None,
                                       model_used: str = None, prompt_hash: str = None,
                                       tokens_used: int = None, generation_latency_ms: int = None) -> 'ComplianceMatrixResponse':
        """Delegate to ComplianceMatrixService."""
        from app.modules.tender.schemas import ComplianceMatrixResponse
        service = ComplianceMatrixService(self.session)
        matrix = await service.create_matrix(
            organization_id=organization_id,
            tender_id=tender_id,
            proposal_id=proposal_id,
            overall_compliance_score=overall_compliance_score,
            requirement_results=requirement_results,
            mandatory_met=mandatory_met,
            mandatory_total=mandatory_total,
            desirable_met=desirable_met,
            desirable_total=desirable_total,
            generation_model=model_used,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            generation_latency_ms=generation_latency_ms,
        )
        return ComplianceMatrixResponse.model_validate(matrix)

    async def get_compliance_matrix(self, organization_id: UUID, tender_id: UUID) -> 'ComplianceMatrixResponse':
        """Delegate to ComplianceMatrixService."""
        from app.modules.tender.schemas import ComplianceMatrixResponse
        service = ComplianceMatrixService(self.session)
        matrix = await service.get_matrix(organization_id, tender_id)
        if not matrix:
            raise ResourceNotFoundException("Compliance matrix not found")
        return ComplianceMatrixResponse.model_validate(matrix)