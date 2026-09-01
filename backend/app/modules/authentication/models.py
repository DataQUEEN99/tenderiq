from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.shared.database.base import BaseModel
import uuid


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    MEMBER = "Member"
    VIEWER = "Viewer"


class User(BaseModel):
    __tablename__ = "users"

    # Override BaseModel.id with explicit PK name
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.MEMBER)
    is_active = Column(Boolean, default=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id"), nullable=False, index=True)

    organization = relationship("Organization", back_populates="users")