from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.shared.exceptions.handlers import register_exception_handlers
from app.shared.middleware.request_id import RequestIDMiddleware
from app.shared.middleware.logging import LoggingMiddleware
import celery_app

# Modular domain routers
from app.modules.authentication.api import router as auth_router
from app.modules.user_management.api import router as user_router
from app.modules.organization.api import router as org_router
from app.modules.company.api import router as company_router
from app.modules.document.api import router as doc_router
from app.modules.tender.api import router as tender_router
from app.modules.proposal.api import router as proposal_router
from app.modules.chat.api import router as chat_router
from app.modules.export.api import router as export_router
from app.modules.audit.api import router as audit_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Register all modular domain routers under the api prefix
api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(org_router)
api_router.include_router(company_router)
api_router.include_router(doc_router)
api_router.include_router(tender_router)
api_router.include_router(proposal_router)
api_router.include_router(chat_router)
api_router.include_router(export_router)
api_router.include_router(audit_router)

app.include_router(api_router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup():
    print(f"{settings.app_name} backend engine online and ready.")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}