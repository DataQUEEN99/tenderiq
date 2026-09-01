from sqlalchemy import Column, String, Text, ARRAY, ForeignKey, Enum as SQLEnum, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel
import uuid


class CompanyProfile(BaseModel):
    __tablename__ = "company_profiles"

    # Explicit PK
    company_profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    employee_count = Column(String(50), nullable=True)
    annual_revenue = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    certifications = Column(ARRAY(String), default=[])
    capabilities = Column(ARRAY(String), default=[])
    past_experience = Column(Text, nullable=True)
    key_personnel = Column(Text, nullable=True)
    financial_info = Column(Text, nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    organization = relationship("Organization", back_populates="company_profile")
    documents = relationship("CompanyDocument", back_populates="company_profile", cascade="all, delete-orphan")


class CompanyDocument(BaseModel):
    __tablename__ = "company_documents"
    __table_args__ = (
        Index("ix_company_documents_company_profile_id", "company_profile_id"),
        Index("ix_company_documents_document_id", "document_id"),
    )

    # Explicit PK
    company_document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_profile_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.company_profile_id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, default="primary")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    company_profile = relationship("CompanyProfile", back_populates="documents")
    document = relationship("Document", back_populates="company_profile")