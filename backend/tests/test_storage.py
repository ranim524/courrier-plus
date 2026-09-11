from unittest.mock import MagicMock, patch

from app.services.storage import get_storage_provider
from app.services.storage.database_provider import DatabaseStorageProvider
from app.services.storage.local_provider import LocalStorageProvider
from tests.conftest import TestingSessionLocal


def test_factory_returns_local_provider_by_default():
    provider = get_storage_provider()
    assert isinstance(provider, LocalStorageProvider)


def test_factory_returns_r2_provider_when_configured():
    from app.services.storage import settings as storage_settings

    with patch.object(storage_settings, "storage_provider", "r2"):
        with patch("boto3.client") as mock_boto_client:
            mock_boto_client.return_value = MagicMock()
            from app.services.storage.r2_provider import R2StorageProvider

            provider = get_storage_provider()
            assert isinstance(provider, R2StorageProvider)


def test_factory_returns_database_provider_when_configured():
    from app.services.storage import settings as storage_settings
    from app.services.storage.database_provider import DatabaseStorageProvider

    with patch.object(storage_settings, "storage_provider", "database"):
        provider = get_storage_provider()
        assert isinstance(provider, DatabaseStorageProvider)


def test_r2_provider_save_read_delete_use_the_configured_bucket():
    with patch("boto3.client") as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_object.return_value = {"Body": MagicMock(read=lambda: b"file-bytes")}

        from app.services.storage.r2_provider import R2StorageProvider

        provider = R2StorageProvider()

        provider.save(b"file-bytes", "2026/doc.pdf")
        mock_client.put_object.assert_called_once()
        _, kwargs = mock_client.put_object.call_args
        assert kwargs["Key"] == "2026/doc.pdf"
        assert kwargs["Body"] == b"file-bytes"

        data = provider.read("2026/doc.pdf")
        assert data == b"file-bytes"

        provider.delete("2026/doc.pdf")
        mock_client.delete_object.assert_called_once()


def test_database_provider_save_read_delete_round_trip():
    # Uses the test database directly (not mocked) via an injected session
    # factory -- DatabaseStorageProvider commits on its own, independent of
    # the per-test rollback transaction, so it must be pointed at the test
    # DB explicitly rather than the app's real dev/prod database.
    provider = DatabaseStorageProvider(session_factory=TestingSessionLocal)
    path = "2026/round-trip-test.pdf"

    provider.save(b"hello world", path)
    assert provider.read(path) == b"hello world"

    provider.delete(path)
    try:
        provider.read(path)
        assert False, "expected FileNotFoundError after delete"
    except FileNotFoundError:
        pass


def test_database_provider_save_overwrites_existing_blob():
    provider = DatabaseStorageProvider(session_factory=TestingSessionLocal)
    path = "2026/overwrite-test.pdf"

    provider.save(b"version one", path)
    provider.save(b"version two", path)

    assert provider.read(path) == b"version two"

    provider.delete(path)
