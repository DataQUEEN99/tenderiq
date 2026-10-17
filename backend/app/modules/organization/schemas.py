from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.modules.organization.models import OrganizationStatus


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)


class OrganizationStatusUpdate(BaseModel):
    status: OrganizationStatus


class OrganizationResponse(BaseModel):
    organization_id: UUID | str
    name: str
    slug: str
    status: OrganizationStatus
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    items: list[OrganizationResponse]
    total: int
    page: int
    page_size: int