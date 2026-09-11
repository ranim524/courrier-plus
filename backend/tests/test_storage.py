from unittest.mock import MagicMock, patch

from app.services.storage import get_storage_provider
from app.services.storage.local_provider import LocalStorageProvider


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
