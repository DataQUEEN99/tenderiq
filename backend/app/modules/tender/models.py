from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Integer, Boolean, Index, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel
import uuid


class TenderStatus(str, enum.Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    IN_PROGRESS = "In Progress"
    SUBMITTED = "Submitted"
    AWARDED = "Awarded"
    LOST = "Lost"
    ARCHIVED = "Archived"


class Tender(BaseModel):
    __tablename__ = "tenders"

    # Explicit PK
    tender_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(500), nullable=False)
    reference_number = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    issuing_authority = Column(String(255), nullable=True)
    submission_deadline = Column(DateTime(timezone=True), nullable=True)
    estimated_value = Column(String(100), nullable=True)
    currency = Column(String(3), default="USD")
    contract_duration = Column(String(100), nullable=True)
    status = Column(SQLEnum(TenderStatus), nullable=False, default=TenderStatus.DRAFT, index=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    organization = relationship("Organization", back_populates="tenders")
    creator = relationship("User", back_populates="tenders")

    documents = relationship("TenderDocument", back_populates="tender", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="tender")
    summaries = relationship("TenderSummary", back_populates="tender", cascade="all, delete-orphan")
    eligibility_analyses = relationship("EligibilityAnalysis", back_populates="tender", cascade="all, delete-orphan")


class TenderDocument(BaseModel):
    __tablename__ = "tender_documents"

    # Explicit PK
    tender_document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.tender_id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)

    tender = relationship("Tender", back_populates="documents")
    document = relationship("Document", back_populates="tender")


class TenderSummary(BaseModel):
    __tablename__ = "tender_summaries"
    __table_args__ = (
        Index("ix_tender_summaries_tender_id", "tender_id"),
        Index("ix_tender_summaries_organization_id", "organization_id"),
    )

    # Explicit PK
    tender_summary_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.tender_id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    summary_text = Column(Text, nullable=False)
    summary_type = Column(String(30), nullable=False)
    model_used = Column(String(100), nullable=False)
    prompt_hash = Column(String(64), nullable=False)
    tokens_used = Column(Integer, nullable=True)
    generation_latency_ms = Column(Integer, nullable=True)
    source_document_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tender = relationship("Tender", back_populates="summaries")
    organization = relationship("Organization", back_populates="tender_summaries")


class EligibilityAnalysis(BaseModel):
    __tablename__ = "eligibility_analyses"
    __table_args__ = (
        Index("ix_eligibility_analyses_tender_id", "tender_id"),
        Index("ix_eligibility_analyses_organization_id", "organization_id"),
        Index("ix_eligibility_analyses_company_profile_id", "company_profile_id"),
    )

    # Explicit PK
    eligibility_analysis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.tender_id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False)
    company_profile_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.company_profile_id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    overall_eligible = Column(Boolean, nullable=False)
    eligibility_score = Column(Integer, nullable=True)
    criteria_results = Column(JSONB, nullable=False)
    missing_requirements = Column(JSONB, default=[], nullable=False)
    model_used = Column(String(100), nullable=False)
    prompt_hash = Column(String(64), nullable=False)
    tokens_used = Column(Integer, nullable=True)
    generation_latency_ms = Column(Integer, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tender = relationship("Tender", back_populates="eligibility_analyses")
    organization = relationship("Organization", back_populates="eligibility_analyses")
    company_profile = relationship("CompanyProfile")