from sqlalchemy import Column, String, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel


class OrganizationStatus(str, enum.Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    DISABLED = "Disabled"


class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(OrganizationStatus), nullable=False, default=OrganizationStatus.ACTIVE)
    is_deleted = Column(Boolean, default=False, nullable=False)

    users = relationship("User", back_populates="organization")