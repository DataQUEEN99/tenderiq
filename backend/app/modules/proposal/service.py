from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Tuple, Optional
from app.modules.proposal.repository import ProposalRepository
from app.modules.proposal.models import Proposal, ProposalStatus, ProposalSection, ProposalDocument
from app.modules.proposal.schemas import (
    ProposalCreate, ProposalUpdate, ProposalStatusUpdate,
    ProposalSectionCreate, ProposalSectionUpdate,
    ProposalResponse, ProposalDetailResponse
)
from app.modules.tender.models import Tender
from app.modules.document.models import Document
from app.shared.exceptions.custom_exceptions import ValidationException, ResourceNotFoundException, BusinessRuleViolationException
from app.shared.logging.logger import app_logger
from app.ai.facade import AIFacade


class ProposalService:
    def __init__(self, session: AsyncSession):
        self.repo = ProposalRepository(session)
        self.session = session
        self.ai_facade = AIFacade()

    async def create(self, organization_id: UUID, created_by: UUID, request: ProposalCreate) -> ProposalResponse:
        from uuid import UUID as UUIDType
        tender_id = UUIDType(request.tender_id)

        from app.modules.tender.service import TenderService
        tender_service = TenderService(self.session)
        await tender_service.get_by_id(tender_id, organization_id)

        proposal = Proposal(
            title=request.title,
            tender_id=tender_id,
            organization_id=organization_id,
            created_by=created_by,
        )

        proposal = await self.repo.create(proposal)

        default_sections = [
            {"title": "Executive Summary", "order": 1, "section_type": "executive_summary"},
            {"title": "Technical Approach", "order": 2, "section_type": "technical"},
            {"title": "Team & Capabilities", "order": 3, "section_type": "team"},
            {"title": "Past Experience", "order": 4, "section_type": "experience"},
            {"title": "Commercial Proposal", "order": 5, "section_type": "commercial"},
            {"title": "Compliance Statement", "order": 6, "section_type": "compliance"},
        ]

        for sec in default_sections:
            section = ProposalSection(
                title=sec["title"],
                order=sec["order"],
                section_type=sec["section_type"],
                proposal_id=proposal.id,
            )
            await self.repo.add_section(section)

        app_logger.info(f"Proposal created", extra={"proposal_id": str(proposal.id), "tender_id": str(tender_id)})
        return ProposalResponse.model_validate(proposal)

    async def get_by_id(self, proposal_id: UUID, organization_id: UUID) -> ProposalResponse:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")
        return ProposalResponse.model_validate(proposal)

    async def get_detail(self, proposal_id: UUID, organization_id: UUID) -> ProposalDetailResponse:
        proposal = await self.repo.get_by_id_with_details(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        response = ProposalDetailResponse.model_validate(proposal)
        response.sections = [s for s in proposal.sections if not s.is_deleted]
        response.documents = [d.document for d in proposal.documents if not d.document.is_deleted]
        return response

    async def get_proposal_with_sections(self, proposal_id: UUID, organization_id: UUID) -> ProposalDetailResponse:
        return await self.get_detail(proposal_id, organization_id)

    async def update(self, proposal_id: UUID, organization_id: UUID, request: ProposalUpdate) -> ProposalResponse:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        if request.title:
            proposal.title = request.title
        if request.executive_summary is not None:
            proposal.executive_summary = request.executive_summary

        proposal = await self.repo.update(proposal)
        return ProposalResponse.model_validate(proposal)

    async def update_status(self, proposal_id: UUID, organization_id: UUID, request: ProposalStatusUpdate) -> ProposalResponse:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        valid_transitions = {
            ProposalStatus.DRAFT: [ProposalStatus.IN_REVIEW, ProposalStatus.ARCHIVED],
            ProposalStatus.IN_REVIEW: [ProposalStatus.FINALIZED, ProposalStatus.DRAFT, ProposalStatus.ARCHIVED],
            ProposalStatus.FINALIZED: [ProposalStatus.SUBMITTED, ProposalStatus.IN_REVIEW, ProposalStatus.ARCHIVED],
            ProposalStatus.SUBMITTED: [ProposalStatus.WON, ProposalStatus.LOST, ProposalStatus.ARCHIVED],
            ProposalStatus.WON: [ProposalStatus.ARCHIVED],
            ProposalStatus.LOST: [ProposalStatus.ARCHIVED],
        }

        if proposal.status in valid_transitions and request.status not in valid_transitions[proposal.status]:
            raise BusinessRuleViolationException(f"Invalid status transition from {proposal.status.value} to {request.status.value}")

        if request.status == ProposalStatus.SUBMITTED:
            from datetime import datetime
            proposal.submitted_at = datetime.utcnow()

        proposal.status = request.status
        proposal = await self.repo.update(proposal)
        return ProposalResponse.model_validate(proposal)

    async def create_section(self, proposal_id: UUID, organization_id: UUID, request: ProposalSectionCreate) -> ProposalSectionCreate:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        section = ProposalSection(
            title=request.title,
            content=request.content,
            order=request.order,
            section_type=request.section_type,
            proposal_id=proposal_id,
        )
        section = await self.repo.add_section(section)
        return ProposalSectionCreate.model_validate(section)

    async def update_section(self, proposal_id: UUID, organization_id: UUID, section_id: UUID, request: ProposalSectionUpdate):
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        section = await self.repo.get_section_by_id(section_id, proposal_id)
        if not section:
            raise ResourceNotFoundException("Section not found")

        if request.title:
            section.title = request.title
        if request.content is not None:
            section.content = request.content
        if request.order is not None:
            section.order = request.order
        if request.section_type:
            section.section_type = request.section_type

        section = await self.repo.update_section(section)
        return ProposalSectionCreate.model_validate(section)

    async def delete_section(self, proposal_id: UUID, organization_id: UUID, section_id: UUID) -> None:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        success = await self.repo.delete_section(section_id, proposal_id)
        if not success:
            raise ResourceNotFoundException("Section not found")

    async def generate(self, proposal_id: UUID, organization_id: UUID, company_profile: dict, requirements: List[str]) -> dict:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        result = await self.ai_facade.generate_proposal(
            organization_id=organization_id,
            tender_id=proposal.tender_id,
            company_profile=company_profile,
            requirements=requirements
        )

        sections = result.get("sections", [])
        for sec_data in sections:
            section = await self.repo.get_section_by_type(proposal_id, sec_data.get("section_type"))
            if section:
                section.content = sec_data.get("content")
                section.is_generated = True
                section.generation_prompt = f"AI generated for {sec_data.get('title')}"
                await self.repo.update_section(section)
            else:
                section = ProposalSection(
                    title=sec_data.get("title"),
                    content=sec_data.get("content"),
                    section_type=sec_data.get("section_type"),
                    is_generated=True,
                    proposal_id=proposal_id,
                )
                await self.repo.add_section(section)

        return result

    async def attach_documents(self, proposal_id: UUID, organization_id: UUID, document_ids: List[UUID]) -> List[str]:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        from app.modules.document.service import DocumentService
        doc_service = DocumentService(self.session)
        await doc_service.verify_documents_exist(organization_id, document_ids)

        existing = [d.document_id for d in proposal.documents if not d.is_deleted]
        for doc_id in document_ids:
            if doc_id in existing:
                raise ValidationException(f"Document {doc_id} already attached")

        await self.repo.attach_documents(proposal_id, document_ids)
        return [str(doc_id) for doc_id in document_ids]

    async def detach_document(self, proposal_id: UUID, organization_id: UUID, document_id: UUID) -> None:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id or proposal.is_deleted:
            raise ResourceNotFoundException("Proposal not found")

        success = await self.repo.detach_document(proposal_id, document_id)
        if not success:
            raise ResourceNotFoundException("Document not attached to this proposal")

    async def list(self, organization_id: UUID, page: int = 1, page_size: int = 20,
                   status: ProposalStatus = None, tender_id: UUID = None) -> Tuple[List[ProposalResponse], int]:
        items, total = await self.repo.list(organization_id, page, page_size, status, tender_id)
        return [ProposalResponse.model_validate(item) for item in items], total

    async def delete(self, proposal_id: UUID, organization_id: UUID) -> None:
        proposal = await self.repo.get_by_id(proposal_id)
        if not proposal or proposal.organization_id != organization_id:
            raise ResourceNotFoundException("Proposal not found")

        await self.repo.soft_delete(proposal_id)
        app_logger.info(f"Proposal deleted", extra={"proposal_id": str(proposal_id)})