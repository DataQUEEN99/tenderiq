from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.modules.proposal.models import ProposalStatus
from app.modules.document.schemas import DocumentResponse


class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    tender_id: str


class ProposalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    executive_summary: Optional[str] = None


class ProposalStatusUpdate(BaseModel):
    status: ProposalStatus


class ProposalSectionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    order: int = Field(0, ge=0)
    section_type: Optional[str] = Field(None, max_length=50)


class ProposalSectionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    order: Optional[int] = Field(None, ge=0)
    section_type: Optional[str] = Field(None, max_length=50)


class ProposalSectionResponse(BaseModel):
    proposal_section_id: str
    title: str
    content: Optional[str]
    order: int
    section_type: Optional[str]
    is_generated: bool
    generation_prompt: Optional[str]
    version: int
    is_current: bool
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProposalGenerateRequest(BaseModel):
    company_profile: dict
    requirements: List[str] = []


class ProposalResponse(BaseModel):
    proposal_id: str
    title: str
    version: int
    status: ProposalStatus
    executive_summary: Optional[str]
    compliance_score: Optional[int]
    submitted_at: Optional[datetime]
    tender_id: str
    organization_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProposalDetailResponse(ProposalResponse):
    sections: List[ProposalSectionResponse] = []
    documents: List[DocumentResponse] = []


class ProposalListResponse(BaseModel):
    items: List[ProposalResponse]
    total: int
    page: int
    page_size: int