from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.modules.company.repository import CompanyRepository, CompanyDocumentRepository
from app.modules.company.models import CompanyProfile
from app.modules.company.schemas import (
    CompanyProfileCreate, CompanyProfileUpdate, CompanyProfileResponse,
    CompanyDocumentAttachRequest, CompanyDocumentResponse
)
from app.shared.exceptions.custom_exceptions import ValidationException, ResourceNotFoundException
from app.shared.logging.logger import app_logger


class CompanyService:
    def __init__(self, session: AsyncSession):
        self.repo = CompanyRepository(session)
        self.doc_repo = CompanyDocumentRepository(session)

    async def create(self, organization_id: UUID, request: CompanyProfileCreate) -> CompanyProfileResponse:
        existing = await self.repo.get_by_organization(organization_id)
        if existing:
            raise ValidationException("Company profile already exists for this organization")

        profile = CompanyProfile(
            organization_id=organization_id,
            **request.model_dump()
        )
        profile = await self.repo.create(profile)
        app_logger.info(f"Company profile created", extra={"organization_id": str(organization_id)})
        return CompanyProfileResponse.model_validate(profile)

    async def get_by_organization(self, organization_id: UUID) -> CompanyProfileResponse:
        profile = await self.repo.get_by_organization(organization_id)
        if not profile:
            raise ResourceNotFoundException("Company profile not found")
        return CompanyProfileResponse.model_validate(profile)

    async def update(self, organization_id: UUID, request: CompanyProfileUpdate) -> CompanyProfileResponse:
        profile = await self.repo.get_by_organization(organization_id)
        if not profile:
            raise ResourceNotFoundException("Company profile not found")

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        profile = await self.repo.update(profile)
        return CompanyProfileResponse.model_validate(profile)

    async def upsert(self, organization_id: UUID, request: CompanyProfileCreate) -> CompanyProfileResponse:
        profile = await self.repo.get_by_organization(organization_id)
        if profile:
            update_request = CompanyProfileUpdate(**request.model_dump())
            return await self.update(organization_id, update_request)
        return await self.create(organization_id, request)

    async def attach_document(self, organization_id: UUID, user_id: UUID,
                              request: CompanyDocumentAttachRequest) -> CompanyDocumentResponse:
        profile = await self.repo.get_by_organization(organization_id)
        if not profile:
            raise ResourceNotFoundException("Company profile not found")
        link = await self.doc_repo.attach_document(
            profile.company_profile_id,
            organization_id,
            UUID(request.document_id),
            user_id,
            request.document_type,
        )
        return CompanyDocumentResponse.model_validate(link)

    async def list_documents(self, organization_id: UUID) -> List[CompanyDocumentResponse]:
        profile = await self.repo.get_by_organization(organization_id)
        if not profile:
            raise ResourceNotFoundException("Company profile not found")
        docs = await self.doc_repo.get_documents(profile.company_profile_id, organization_id)
        return [CompanyDocumentResponse.model_validate(d) for d in docs]

    async def detach_document(self, organization_id: UUID, document_id: UUID) -> bool:
        profile = await self.repo.get_by_organization(organization_id)
        if not profile:
            raise ResourceNotFoundException("Company profile not found")
        return await self.doc_repo.detach_document(profile.company_profile_id, organization_id, document_id)