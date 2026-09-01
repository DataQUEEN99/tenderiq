from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.modules.tender.models import TenderStatus
from app.modules.document.schemas import DocumentResponse
from uuid import UUID


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
    tender_id: str
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


# TenderSummary schemas
class TenderSummaryBase(BaseModel):
    summary_type: str = Field(..., min_length=1, max_length=50)
    summary_text: str = Field(..., min_length=1)
    model_used: str = Field(..., max_length=100)
    prompt_hash: str = Field(..., max_length=64)
    tokens_used: Optional[int] = None
    generation_latency_ms: Optional[int] = None
    source_document_ids: Optional[List[UUID]] = None
    is_current: bool = True


class TenderSummaryCreate(BaseModel):
    summary_type: str = Field(..., min_length=1, max_length=50)
    summary_text: str = Field(..., min_length=1)
    model_used: str = Field(..., max_length=100)
    prompt_hash: str = Field(..., max_length=64)
    tokens_used: Optional[int] = None
    generation_latency_ms: Optional[int] = None
    source_document_ids: Optional[List[UUID]] = None


class TenderSummaryResponse(TenderSummaryBase):
    tender_summary_id: str
    tender_id: str
    organization_id: str
    version: int
    is_current: bool
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# EligibilityAnalysis schemas
class EligibilityAnalysisBase(BaseModel):
    company_profile_id: str
    overall_eligible: bool
    eligibility_score: Optional[int] = Field(None, ge=0, le=100)
    criteria_results: List[Dict[str, Any]] = Field(..., min_length=1)
    missing_requirements: List[Dict[str, Any]] = []
    model_used: str = Field(..., max_length=100)
    prompt_hash: str = Field(..., max_length=64)
    tokens_used: Optional[int] = None
    generation_latency_ms: Optional[int] = None
    is_current: bool = True


class EligibilityAnalysisCreate(BaseModel):
    company_profile_id: str
    overall_eligible: bool
    eligibility_score: Optional[int] = Field(None, ge=0, le=100)
    criteria_results: List[Dict[str, Any]] = Field(..., min_length=1)
    missing_requirements: List[Dict[str, Any]] = []
    model_used: str = Field(..., max_length=100)
    prompt_hash: str = Field(..., max_length=64)
    tokens_used: Optional[int] = None
    generation_latency_ms: Optional[int] = None


class EligibilityAnalysisResponse(EligibilityAnalysisBase):
    eligibility_analysis_id: str
    tender_id: str
    organization_id: str
    version: int
    is_current: bool
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ComplianceMatrix schemas
class ComplianceMatrixBase(BaseModel):
    proposal_id: str
    overall_compliance_score: Optional[int] = Field(None, ge=0, le=100)
    mandatory_met: int = 0
    mandatory_total: int = 0
    desirable_met: int = 0
    desirable_total: int = 0
    requirement_results: List[Dict[str, Any]] = Field(..., min_length=1)
    model_used: str = Field(..., max_length=100)
    prompt_hash: str = Field(..., max_length=64)
    tokens_used: Optional[int] = None
    generation_latency_ms: Optional[int] = None
    is_current: bool = True


class ComplianceMatrixCreate(BaseModel):
    proposal_id: str
    overall_compliance_score: Optional[int] = Field(None, ge=0, le=100)
    mandatory_met: int = 0
    mandatory_total: int = 0
    desirable_met: int = 0
    desirable_total: int = 0
    requirement_results: List[Dict[str, Any]] = Field(..., min_length=1)
    model_used: str = Field(..., max_length=100)
    prompt_hash: str = Field(..., max_length=64)
    tokens_used: Optional[int] = None
    generation_latency_ms: Optional[int] = None


class ComplianceMatrixResponse(ComplianceMatrixBase):
    compliance_matrix_id: str
    tender_id: str
    organization_id: str
    proposal_id: str
    version: int
    is_current: bool
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True