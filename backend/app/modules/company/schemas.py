from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CompanyProfileCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    certifications: List[str] = []
    capabilities: List[str] = []
    past_experience: Optional[str] = None
    key_personnel: Optional[str] = None
    financial_info: Optional[str] = None


class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    certifications: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    past_experience: Optional[str] = None
    key_personnel: Optional[str] = None
    financial_info: Optional[str] = None


class CompanyProfileResponse(BaseModel):
    company_profile_id: str
    company_name: str
    industry: Optional[str]
    employee_count: Optional[str]
    annual_revenue: Optional[str]
    website: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    certifications: List[str]
    capabilities: List[str]
    past_experience: Optional[str]
    key_personnel: Optional[str]
    financial_info: Optional[str]
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyDocumentAttachRequest(BaseModel):
    document_id: str
    document_type: Optional[str] = "Company"


class CompanyDocumentResponse(BaseModel):
    company_document_id: str
    company_profile_id: str
    document_id: str
    document_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True