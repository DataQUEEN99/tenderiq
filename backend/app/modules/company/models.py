from sqlalchemy import Column, String, Text, ARRAY, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel


class CompanyProfile(BaseModel):
    __tablename__ = "company_profiles"

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

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True, index=True)

    organization = relationship("Organization", back_populates="company_profile")
    documents = relationship("CompanyDocument", back_populates="company_profile", cascade="all, delete-orphan")


class CompanyDocument(BaseModel):
    __tablename__ = "company_documents"

    company_profile_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=True)

    company_profile = relationship("CompanyProfile", back_populates="documents")
    document = relationship("Document")