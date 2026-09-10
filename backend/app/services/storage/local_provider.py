from pathlib import Path

from app.core.config import get_settings
from app.services.storage.base import StorageProvider

settings = get_settings()


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.upload_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        # Prevent path traversal: resolve and ensure the result stays under base_dir.
        candidate = (self.base_dir / relative_path).resolve()
        if self.base_dir not in candidate.parents and candidate != self.base_dir:
            raise ValueError("Invalid storage path")
        return candidate

    def save(self, data: bytes, relative_path: str) -> str:
        target = self._resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return relative_path

    def read(self, storage_path: str) -> bytes:
        target = self._resolve(storage_path)
        return target.read_bytes()

    def delete(self, storage_path: str) -> None:
        target = self._resolve(storage_path)
        if target.exists():
            target.unlink()


def get_storage_provider() -> StorageProvider:
    return LocalStorageProvider()
