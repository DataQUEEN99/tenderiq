from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.shared.exceptions.handlers import register_exception_handlers
from app.shared.middleware.request_id import RequestIDMiddleware
from app.shared.middleware.logging import LoggingMiddleware

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
    allow_origins=settings.cors_origins,
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
    """Run database migrations on startup.

    Migration failure must never let the API start against an incompatible database.
    """
    import sys
    import os
    import subprocess

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Run alembic migrations
    result = subprocess.run([
        sys.executable, "-m", "alembic", "upgrade", "head"
    ], cwd=backend_dir, capture_output=True, text=True)

    if result.returncode != 0:
        error_msg = f"Migration failed on startup: {result.stderr}"
        print(error_msg, file=sys.stderr)
        # Fail application startup - do not run against incompatible database
        raise RuntimeError(error_msg)
    else:
        print("Database migrations completed on startup")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}