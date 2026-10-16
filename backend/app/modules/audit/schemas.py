from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.modules.audit.models import AuditAction


class AuditLogResponse(BaseModel):
    audit_log_id: str
    action: AuditAction
    resource_type: str
    resource_id: Optional[UUID]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    organization_id: UUID
    user_id: Optional[UUID]
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditFilterRequest(BaseModel):
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)