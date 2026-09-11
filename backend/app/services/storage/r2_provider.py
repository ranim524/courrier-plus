import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.services.storage.base import StorageProvider

settings = get_settings()


class R2StorageProvider(StorageProvider):
    """Stores documents in a Cloudflare R2 bucket via its S3-compatible API.

    The bucket is never made public: only the backend holds the R2 API
    credentials, and callers only ever reach documents through an authorized
    route (admin JWT or a valid recipient access token) -- R2 itself is just
    the disk behind that, same access model as LocalStorageProvider.
    """

    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=BotoConfig(signature_version="s3v4"),
            region_name="auto",
        )
        self._bucket = settings.r2_bucket_name

    def save(self, data: bytes, relative_path: str) -> str:
        self._client.put_object(Bucket=self._bucket, Key=relative_path, Body=data)
        return relative_path

    def read(self, storage_path: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=storage_path)
        return response["Body"].read()

    def delete(self, storage_path: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=storage_path)
        except ClientError:
            pass
