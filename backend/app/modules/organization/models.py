from sqlalchemy import Column, String, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel
import uuid


class OrganizationStatus(str, enum.Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    DISABLED = "Disabled"


class Organization(BaseModel):
    __tablename__ = "organizations"

    # Override BaseModel.id with explicit PK name
    organization_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(OrganizationStatus), nullable=False, default=OrganizationStatus.ACTIVE)
    is_deleted = Column(Boolean, default=False, nullable=False)

    users = relationship("User", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
    tenders = relationship("Tender", back_populates="organization")
    proposals = relationship("Proposal", back_populates="organization")
    company_profile = relationship("CompanyProfile", back_populates="organization", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="organization")
    tender_summaries = relationship("TenderSummary", back_populates="organization")
    eligibility_analyses = relationship("EligibilityAnalysis", back_populates="organization")
    compliance_matrices = relationship("ComplianceMatrix", back_populates="organization")