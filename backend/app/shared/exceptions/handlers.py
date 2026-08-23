from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from app.shared.exceptions.custom_exceptions import (
    TenderIQException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    BusinessRuleViolationException,
    AIProcessingException,
    StorageException,
    InternalServerException,
)
from app.shared.logging.logger import app_logger


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(TenderIQException)
    async def tenderiq_exception_handler(request: Request, exc: TenderIQException):
        app_logger.error(f"{exc.code}: {exc.message}", extra={"path": request.url.path})
        status_map = {
            "VALIDATION_ERROR": 400,
            "AUTHENTICATION_ERROR": 401,
            "AUTHORIZATION_ERROR": 403,
            "NOT_FOUND": 404,
            "BUSINESS_RULE_VIOLATION": 400,
            "AI_PROCESSING_ERROR": 500,
            "STORAGE_ERROR": 500,
            "INTERNAL_SERVER_ERROR": 500,
            "INTERNAL_ERROR": 500,
        }
        return JSONResponse(
            status_code=status_map.get(exc.code, 500),
            content={"success": False, "error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        app_logger.exception(f"Unhandled exception: {exc}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}},
        )