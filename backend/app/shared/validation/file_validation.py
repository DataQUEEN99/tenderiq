from app.shared.exceptions.custom_exceptions import ValidationException
from app.shared.validation.validators import validate_file_type, validate_file_size
from app.config import get_settings

settings = get_settings()


def validate_upload_file(file_content: bytes, filename: str, file_size: int) -> None:
    if not validate_file_size(file_size):
        raise ValidationException(f"File size exceeds {settings.max_file_size_mb}MB limit")

    if not validate_file_type(file_content):
        raise ValidationException(f"File type not allowed. Allowed: {settings.allowed_file_types}")

    if not filename.lower().endswith(".pdf"):
        raise ValidationException("Only PDF files are supported")