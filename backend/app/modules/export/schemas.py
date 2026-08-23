from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.modules.export.models import ExportFormat, ExportStatus


class ExportCreate(BaseModel):
    proposal_id: str
    export_format: ExportFormat = ExportFormat.PDF


class ExportResponse(BaseModel):
    id: str
    export_format: ExportFormat
    status: ExportStatus
    file_path: Optional[str]
    error_message: Optional[str]
    proposal_id: str
    organization_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExportListResponse(BaseModel):
    items: List[ExportResponse]
    total: int
    page: int
    page_size: int