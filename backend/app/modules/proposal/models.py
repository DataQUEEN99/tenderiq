from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum, Integer, DateTime, Boolean, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel
import uuid


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

    # Explicit PK
    proposal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(500), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(SQLEnum(ProposalStatus), nullable=False, default=ProposalStatus.DRAFT, index=True)
    executive_summary = Column(Text, nullable=True)
    compliance_score = Column(Integer, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.tender_id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    tender = relationship("Tender", back_populates="proposals")
    organization = relationship("Organization", back_populates="proposals")
    creator = relationship("User", back_populates="proposals")

    sections = relationship("ProposalSection", back_populates="proposal", cascade="all, delete-orphan", order_by="ProposalSection.order")
    documents = relationship("ProposalDocument", back_populates="proposal", cascade="all, delete-orphan")
    compliance_matrices = relationship("ComplianceMatrix", back_populates="proposal", cascade="all, delete-orphan")


class ProposalSection(BaseModel):
    __tablename__ = "proposal_sections"

    # Explicit PK
    proposal_section_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    order = Column(Integer, default=0, nullable=False)
    section_type = Column(String(50), nullable=True)
    is_generated = Column(Boolean, default=False, nullable=False)
    generation_prompt = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.proposal_id", ondelete="CASCADE"), nullable=False, index=True)

    proposal = relationship("Proposal", back_populates="sections")


class ProposalDocument(BaseModel):
    __tablename__ = "proposal_documents"

    # Explicit PK
    proposal_document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.proposal_id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)

    proposal = relationship("Proposal", back_populates="documents")
    document = relationship("Document", back_populates="proposal")


class ComplianceMatrix(BaseModel):
    __tablename__ = "compliance_matrices"
    __table_args__ = (
        Index("ix_compliance_matrices_tender_id", "tender_id"),
        Index("ix_compliance_matrices_organization_id", "organization_id"),
        Index("ix_compliance_matrices_proposal_id", "proposal_id"),
    )

    # Explicit PK
    compliance_matrix_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.tender_id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.proposal_id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    overall_compliance_score = Column(Integer, nullable=True)
    mandatory_met = Column(Integer, nullable=False, default=0)
    mandatory_total = Column(Integer, nullable=False, default=0)
    desirable_met = Column(Integer, nullable=False, default=0)
    desirable_total = Column(Integer, nullable=False, default=0)
    requirement_results = Column(JSONB, nullable=False)
    model_used = Column(String(100), nullable=False)
    prompt_hash = Column(String(64), nullable=False)
    tokens_used = Column(Integer, nullable=True)
    generation_latency_ms = Column(Integer, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tender = relationship("Tender")
    proposal = relationship("Proposal", back_populates="compliance_matrices")
    organization = relationship("Organization", back_populates="compliance_matrices")