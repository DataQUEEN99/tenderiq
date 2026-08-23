from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel


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

    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    extension = Column(String(20), nullable=False)

    document_type = Column(SQLEnum(DocumentType), nullable=False, default=DocumentType.OTHER)
    status = Column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADING)
    error_message = Column(Text, nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    chunk_count = Column(Integer, default=0)
    vector_collection = Column(String(100), nullable=True)

    organization = relationship("Organization", back_populates="documents")
    uploader = relationship("User", back_populates="documents")

    tender = relationship("TenderDocument", back_populates="document", uselist=False)
    proposal = relationship("ProposalDocument", back_populates="document", uselist=False)