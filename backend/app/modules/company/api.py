from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from app.shared.database.session import get_db
from app.modules.company.service import CompanyService
from app.modules.company.schemas import (
    CompanyProfileCreate, CompanyProfileUpdate, CompanyProfileResponse,
    CompanyDocumentAttachRequest, CompanyDocumentResponse
)
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission


router = APIRouter(prefix="/company", tags=["Company Profile"])


@router.post("/profile", response_model=CompanyProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    request: CompanyProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COMPANY_UPDATE)),
):
    service = CompanyService(db)
    return await service.create(current_user.organization_id, request)


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COMPANY_READ)),
):
    service = CompanyService(db)
    return await service.get_by_organization(current_user.organization_id)


@router.put("/profile", response_model=CompanyProfileResponse)
async def update_company_profile(
    request: CompanyProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COMPANY_UPDATE)),
):
    service = CompanyService(db)
    return await service.update(current_user.organization_id, request)


@router.post("/documents", response_model=CompanyDocumentResponse, status_code=status.HTTP_201_CREATED)
async def attach_company_document(
    request: CompanyDocumentAttachRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COMPANY_DOC_UPLOAD)),
):
    service = CompanyService(db)
    return await service.attach_document(current_user.organization_id, current_user.user_id, request)


@router.get("/documents", response_model=List[CompanyDocumentResponse])
async def list_company_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COMPANY_READ)),
):
    service = CompanyService(db)
    return await service.list_documents(current_user.organization_id)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_company_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.COMPANY_DOC_DELETE)),
):
    service = CompanyService(db)
    await service.detach_document(current_user.organization_id, document_id)