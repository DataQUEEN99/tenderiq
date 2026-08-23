import os
import shutil
from typing import BinaryIO
from app.config import get_settings
from app.shared.exceptions.custom_exceptions import StorageException


class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.storage_type = getattr(self.settings, "storage_type", "local")
        self.local_root = self.settings.storage_root

    async def save(self, path: str, content: bytes) -> str:
        if self.storage_type == "local":
            return await self._save_local(path, content)
        else:
            raise StorageException(f"Unsupported storage type: {self.storage_type}")

    async def _save_local(self, path: str, content: bytes) -> str:
        full_path = os.path.join(self.local_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "wb") as f:
                f.write(content)
            return full_path
        except Exception as e:
            raise StorageException(f"Failed to save file: {str(e)}")

    async def read(self, path: str) -> bytes:
        if self.storage_type == "local":
            return await self._read_local(path)
        else:
            raise StorageException(f"Unsupported storage type: {self.storage_type}")

    async def _read_local(self, path: str) -> bytes:
        full_path = os.path.join(self.local_root, path)
        try:
            with open(full_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            raise StorageException(f"File not found: {path}")
        except Exception as e:
            raise StorageException(f"Failed to read file: {str(e)}")

    async def delete(self, path: str) -> bool:
        if self.storage_type == "local":
            return await self._delete_local(path)
        else:
            raise StorageException(f"Unsupported storage type: {self.storage_type}")

    async def _delete_local(self, path: str) -> bool:
        full_path = os.path.join(self.local_root, path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            raise StorageException(f"Failed to delete file: {str(e)}")

    async def exists(self, path: str) -> bool:
        if self.storage_type == "local":
            full_path = os.path.join(self.local_root, path)
            return os.path.exists(full_path)
        else:
            raise StorageException(f"Unsupported storage type: {self.storage_type}")

    def get_full_path(self, path: str) -> str:
        return os.path.join(self.local_root, path)