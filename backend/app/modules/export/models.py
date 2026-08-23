from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel


class ExportFormat(str, enum.Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    HTML = "HTML"


class ExportStatus(str, enum.Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


class Export(BaseModel):
    __tablename__ = "exports"

    export_format = Column(SQLEnum(ExportFormat), nullable=False)
    status = Column(SQLEnum(ExportStatus), nullable=False, default=ExportStatus.PENDING)
    file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)

    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    proposal = relationship("Proposal")
    organization = relationship("Organization")
    creator = relationship("User")