from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Abstraction over document storage so local filesystem can be swapped for
    S3-compatible cloud storage later without touching callers."""

    @abstractmethod
    def save(self, data: bytes, relative_path: str) -> str:
        """Persists bytes and returns the storage path to keep in the DB."""

    @abstractmethod
    def read(self, storage_path: str) -> bytes:
        """Reads bytes back given a stored path."""

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        """Deletes the stored object, if present."""
