from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from fastapi.responses import StreamingResponse
from typing import List
import io
from app.shared.database.session import get_db
from app.modules.export.service import ExportService
from app.modules.export.schemas import ExportCreate, ExportResponse, ExportListResponse
from app.modules.export.models import ExportFormat
from app.shared.security.auth_dependencies import get_current_user, require_permission
from app.modules.authentication.models import User
from app.shared.security.permissions import Permission


router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def create_export(
    request: ExportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EXPORT_PDF)),
):
    service = ExportService(db)
    return await service.create_export(current_user.organization_id, current_user.user_id, request)


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EXPORT_PDF)),
):
    service = ExportService(db)
    return await service.get_export(export_id, current_user.organization_id)


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EXPORT_PDF)),
):
    service = ExportService(db)
    content = await service.download_export(export_id, current_user.organization_id)

    export = await service.get_export(export_id, current_user.organization_id)

    media_types = {
        ExportFormat.PDF: "application/pdf",
        ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.HTML: "text/html",
    }

    filename = export.file_path.split("/")[-1] if export.file_path else f"export_{export_id}"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_types.get(export.export_format, "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("", response_model=ExportListResponse)
async def list_exports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EXPORT_PDF)),
):
    service = ExportService(db)
    items, total = await service.list_exports(current_user.organization_id, page, page_size)
    return ExportListResponse(items=items, total=total, page=page, page_size=page_size)


@router.delete("/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EXPORT_PDF)),
):
    service = ExportService(db)
    await service.delete_export(export_id, current_user.organization_id)