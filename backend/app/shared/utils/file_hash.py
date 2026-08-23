import hashlib


def compute_sha256(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()


def generate_storage_path(organization_id: str, filename: str) -> str:
    import uuid
    ext = filename.split(".")[-1] if "." in filename else ""
    storage_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    return f"organizations/{organization_id}/documents/{storage_name}"