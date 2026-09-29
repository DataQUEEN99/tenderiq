from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Integer, Text, Index, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel
import uuid


class DocumentStatus(str, enum.Enum):
    UPLOADING = "Uploading"
    PROCESSING = "Processing"
    PROCESSED = "Processed"
    FAILED = "Failed"
    DELETED = "Deleted"


class DocumentType(str, enum.Enum):
    TENDER = "Tender"
    PROPOSAL = "Proposal"
    COMPANY = "Company"
    REFERENCE = "Reference"
    OTHER = "Other"


class Document(BaseModel):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_org_hash", "organization_id", "file_hash"),
    )

    # Override BaseModel.id with explicit PK name
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    extension = Column(String(20), nullable=False)

    document_type = Column(SQLEnum(DocumentType), nullable=False, default=DocumentType.OTHER)
    status = Column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADING)
    error_message = Column(Text, nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    chunk_count = Column(Integer, default=0)
    vector_collection = Column(String(100), nullable=True)

    organization = relationship("Organization", back_populates="documents")
    uploader = relationship("User", back_populates="documents")

    tender = relationship("TenderDocument", back_populates="document", uselist=False)
    proposal = relationship("ProposalDocument", back_populates="document", uselist=False)
    company_profile = relationship("CompanyDocument", back_populates="document", uselist=False)
    content = relationship("DocumentContent", back_populates="document", uselist=False, cascade="all, delete-orphan")
    processing = relationship("DocumentProcessing", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentContent(BaseModel):
    __tablename__ = "document_contents"

    # Override BaseModel.id with explicit PK name
    document_content_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    extracted_text = Column(Text, nullable=True)
    extraction_method = Column(String(50), nullable=False)
    extraction_status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    extracted_at = Column(DateTime(timezone=True), nullable=True)

    document = relationship("Document", back_populates="content")


class DocumentProcessing(BaseModel):
    __tablename__ = "document_processing"

    # Override BaseModel.id with explicit PK name
    document_processing_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, nullable=False, default=0, server_default="0")  # 0-100 percentage
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    processing_metadata = Column("metadata", JSONB, default={}, nullable=False)

    document = relationship("Document", back_populates="processing")

    __table_args__ = (
        Index("ix_document_processing_document_stage", "document_id", "stage"),
    )