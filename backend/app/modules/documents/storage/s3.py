"""S3-compatible storage provider (production seam, ADR-005).

Uses boto3 if available/configured to issue real presigned PUT/GET URLs against
a PRIVATE, encrypted bucket. boto3 is not a bundled dependency in this slice, so
the provider imports it lazily and raises a clear error if unavailable — the
factory only selects S3 when STORAGE_PROVIDER=s3 is explicitly configured.

Presigned URLs are short-lived (settings.signed_url_expiration_seconds).
Bucket names / endpoints are never returned to clients (only the opaque
presigned URL is).
"""
from __future__ import annotations

from app.core.config import Settings, get_settings
from app.modules.documents.storage.provider import (
    ObjectMetadata,
    ObjectNotFoundError,
    SignedDownload,
    SignedUpload,
    StorageError,
    StorageProvider,
)


class S3StorageProvider(StorageProvider):
    name = "s3"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        if not self._s.s3_bucket:
            raise StorageError("S3_BUCKET must be configured for the S3 storage provider.")
        try:
            import boto3  # noqa: F401
        except Exception as exc:  # pragma: no cover - boto3 not bundled here
            raise StorageError(
                "boto3 is required for the S3 storage provider but is not installed."
            ) from exc
        import boto3

        self._client = boto3.client(
            "s3",
            region_name=self._s.s3_region or None,
            endpoint_url=self._s.s3_endpoint or None,
        )
        self._bucket = self._s.s3_bucket
        self._expiry = self._s.signed_url_expiration_seconds

    def create_upload_url(self, storage_key: str, content_type: str) -> SignedUpload:
        url = self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": storage_key, "ContentType": content_type,
                    "ServerSideEncryption": "AES256"},
            ExpiresIn=self._expiry,
        )
        import time

        return SignedUpload(
            url=url, method="PUT", headers={"Content-Type": content_type},
            storage_key=storage_key, expires_at=int(time.time()) + self._expiry,
        )

    def create_download_url(self, storage_key: str) -> SignedDownload:
        url = self._client.generate_presigned_url(
            "get_object", Params={"Bucket": self._bucket, "Key": storage_key}, ExpiresIn=self._expiry,
        )
        import time

        return SignedDownload(url=url, expires_at=int(time.time()) + self._expiry)

    def put_object(self, storage_key: str, data: bytes, content_type: str | None = None) -> None:
        self._client.put_object(
            Bucket=self._bucket, Key=storage_key, Body=data,
            ContentType=content_type or "application/octet-stream", ServerSideEncryption="AES256",
        )

    def get_object(self, storage_key: str) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=storage_key)
            return resp["Body"].read()
        except Exception as exc:
            raise ObjectNotFoundError(storage_key) from exc

    def delete_object(self, storage_key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=storage_key)

    def object_exists(self, storage_key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=storage_key)
            return True
        except Exception:
            return False

    def get_object_metadata(self, storage_key: str) -> ObjectMetadata:
        try:
            head = self._client.head_object(Bucket=self._bucket, Key=storage_key)
        except Exception as exc:
            raise ObjectNotFoundError(storage_key) from exc
        return ObjectMetadata(
            storage_key=storage_key,
            size_bytes=int(head.get("ContentLength", 0)),
            content_type=head.get("ContentType"),
        )
