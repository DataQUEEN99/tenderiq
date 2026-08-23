from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.modules.tender.models import TenderStatus
from app.modules.document.schemas import DocumentResponse


class TenderCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    reference_number: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    issuing_authority: Optional[str] = Field(None, max_length=255)
    submission_deadline: Optional[datetime] = None
    estimated_value: Optional[str] = Field(None, max_length=100)
    currency: str = Field("USD", max_length=3)
    contract_duration: Optional[str] = Field(None, max_length=100)


class TenderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    reference_number: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    issuing_authority: Optional[str] = Field(None, max_length=255)
    submission_deadline: Optional[datetime] = None
    estimated_value: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, max_length=3)
    contract_duration: Optional[str] = Field(None, max_length=100)


class TenderStatusUpdate(BaseModel):
    status: TenderStatus


class TenderDocumentAttach(BaseModel):
    document_ids: List[str] = Field(..., min_length=1)


class TenderResponse(BaseModel):
    id: str
    title: str
    reference_number: str
    description: Optional[str]
    issuing_authority: Optional[str]
    submission_deadline: Optional[datetime]
    estimated_value: Optional[str]
    currency: str
    contract_duration: Optional[str]
    status: TenderStatus
    organization_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenderDetailResponse(TenderResponse):
    documents: List[DocumentResponse] = []


class TenderListResponse(BaseModel):
    items: List[TenderResponse]
    total: int
    page: int
    page_size: int