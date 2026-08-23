import magic
from app.shared.exceptions.custom_exceptions import ValidationException
from app.config import get_settings

settings = get_settings()


def validate_file_type(file_content: bytes, allowed_types: list = None) -> bool:
    if allowed_types is None:
        allowed_types = settings.allowed_file_types
    mime = magic.from_buffer(file_content, mime=True)
    return mime in allowed_types


def validate_file_size(file_size: int, max_size_mb: int = None) -> bool:
    if max_size_mb is None:
        max_size_mb = settings.max_file_size_mb
    return file_size <= max_size_mb * 1024 * 1024


def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain digit"
    return True, ""