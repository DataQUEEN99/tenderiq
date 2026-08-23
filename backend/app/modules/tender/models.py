from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Integer, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel


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

    title = Column(String(500), nullable=False)
    reference_number = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    issuing_authority = Column(String(255), nullable=True)
    submission_deadline = Column(DateTime(timezone=True), nullable=True)
    estimated_value = Column(String(100), nullable=True)
    currency = Column(String(3), default="USD")
    contract_duration = Column(String(100), nullable=True)
    status = Column(SQLEnum(TenderStatus), nullable=False, default=TenderStatus.DRAFT, index=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization", back_populates="tenders")
    creator = relationship("User", back_populates="tenders")

    documents = relationship("TenderDocument", back_populates="tender", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="tender")
    summaries = relationship("TenderSummary", back_populates="tender", cascade="all, delete-orphan")
    eligibility_analyses = relationship("EligibilityAnalysis", back_populates="tender", cascade="all, delete-orphan")


class TenderDocument(BaseModel):
    __tablename__ = "tender_documents"

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    tender = relationship("Tender", back_populates="documents")
    document = relationship("Document", back_populates="tender")


class TenderSummary(BaseModel):
    __tablename__ = "tender_summaries"

    summary_type = Column(String(50), nullable=False, default="executive")
    version = Column(Integer, default=1, nullable=False)
    content = Column(Text, nullable=False)
    structured_data = Column(JSON, nullable=True)

    # Generation metadata
    model = Column(String(100), nullable=True)
    prompt_hash = Column(String(64), nullable=True)
    tokens = Column(Integer, nullable=True)
    latency = Column(Float, nullable=True)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    tender = relationship("Tender", back_populates="summaries")
    organization = relationship("Organization")
    creator = relationship("User")


class EligibilityAnalysis(BaseModel):
    __tablename__ = "eligibility_analyses"

    version = Column(Integer, default=1, nullable=False)
    decision = Column(String(50), nullable=False, default="UNKNOWN")
    confidence = Column(Float, nullable=True)
    criteria_analysis = Column(JSON, nullable=True)
    missing_requirements = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)

    # Generation metadata
    model = Column(String(100), nullable=True)
    prompt_hash = Column(String(64), nullable=True)
    tokens = Column(Integer, nullable=True)
    latency = Column(Float, nullable=True)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    company_profile_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    tender = relationship("Tender", back_populates="eligibility_analyses")
    organization = relationship("Organization")
    creator = relationship("User")