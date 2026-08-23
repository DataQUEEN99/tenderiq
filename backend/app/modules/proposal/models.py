from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum, Integer, DateTime, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel


class ProposalStatus(str, enum.Enum):
    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    FINALIZED = "Finalized"
    SUBMITTED = "Submitted"
    WON = "Won"
    LOST = "Lost"
    ARCHIVED = "Archived"


class Proposal(BaseModel):
    __tablename__ = "proposals"

    title = Column(String(500), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(SQLEnum(ProposalStatus), nullable=False, default=ProposalStatus.DRAFT, index=True)
    executive_summary = Column(Text, nullable=True)
    compliance_score = Column(Integer, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    tender = relationship("Tender", back_populates="proposals")
    organization = relationship("Organization", back_populates="proposals")
    creator = relationship("User", back_populates="proposals")

    sections = relationship("ProposalSection", back_populates="proposal", cascade="all, delete-orphan", order_by="ProposalSection.order")
    documents = relationship("ProposalDocument", back_populates="proposal", cascade="all, delete-orphan")
    compliance_matrices = relationship("ComplianceMatrix", back_populates="proposal", cascade="all, delete-orphan")


class ProposalSection(BaseModel):
    __tablename__ = "proposal_sections"

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    order = Column(Integer, default=0, nullable=False)
    section_type = Column(String(50), nullable=True)
    is_generated = Column(Boolean, default=False, nullable=False)
    generation_prompt = Column(Text, nullable=True)

    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)

    proposal = relationship("Proposal", back_populates="sections")


class ProposalDocument(BaseModel):
    __tablename__ = "proposal_documents"

    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    proposal = relationship("Proposal", back_populates="documents")
    document = relationship("Document", back_populates="proposal")


class ComplianceMatrix(BaseModel):
    __tablename__ = "compliance_matrices"

    version = Column(Integer, default=1, nullable=False)
    overall_score = Column(Float, nullable=True)
    summary = Column(JSON, nullable=True)
    matrix = Column(JSON, nullable=True)
    gaps = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)

    # Generation metadata
    model = Column(String(100), nullable=True)
    prompt_hash = Column(String(64), nullable=True)
    tokens = Column(Integer, nullable=True)
    latency = Column(Float, nullable=True)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    tender = relationship("Tender")
    proposal = relationship("Proposal", back_populates="compliance_matrices")
    organization = relationship("Organization")
    creator = relationship("User")