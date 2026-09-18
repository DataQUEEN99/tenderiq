from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Tuple, Optional
from app.modules.tender.repository import TenderRepository
from app.modules.tender.models import Tender, TenderStatus, TenderDocument
from app.modules.tender.schemas import TenderCreate, TenderUpdate, TenderStatusUpdate, TenderResponse, TenderDetailResponse
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
        if not tender or tender.is_deleted:
            raise ResourceNotFoundException("Tender not found")
        return TenderResponse.model_validate(tender)

    async def get_detail(self, tender_id: UUID, organization_id: UUID) -> TenderDetailResponse:
        tender = await self.repo.get_by_id_with_docs(tender_id, organization_id)
        if not tender or tender.is_deleted:
            raise ResourceNotFoundException("Tender not found")

        response = TenderDetailResponse.model_validate(tender)
        response.documents = [doc.document for doc in tender.documents if not doc.document.is_deleted]
        return response

    async def update(self, tender_id: UUID, organization_id: UUID, request: TenderUpdate) -> TenderResponse:
        tender = await self.repo.get_by_id(tender_id, organization_id)
        if not tender or tender.is_deleted:
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
        if not tender or tender.is_deleted:
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
        if not tender or tender.is_deleted:
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
        if not tender or tender.is_deleted:
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