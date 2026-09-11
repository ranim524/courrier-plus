from app.core.config import get_settings
from app.services.storage.base import StorageProvider
from app.services.storage.local_provider import LocalStorageProvider

settings = get_settings()


def get_storage_provider() -> StorageProvider:
    if settings.storage_provider == "r2":
        from app.services.storage.r2_provider import R2StorageProvider

        return R2StorageProvider()
    if settings.storage_provider == "database":
        from app.services.storage.database_provider import DatabaseStorageProvider

        return DatabaseStorageProvider()
    return LocalStorageProvider()
