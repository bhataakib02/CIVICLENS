"""Local filesystem storage provider (dev/test).

Real filesystem persistence with HMAC-signed, time-limited local URLs that the
documents router validates before serving bytes. This is NOT public storage:
there is no web-served directory; downloads go through the authenticated API
which verifies the signature + ownership.

Path-traversal safety: the on-disk path is derived by hashing the storage_key,
NEVER by joining the (untrusted) key or a user filename onto the root. So even a
malicious key like "../../etc/passwd" maps to a hashed filename inside the root.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

from app.core.config import Settings, get_settings
from app.modules.documents.storage.provider import (
    ObjectMetadata,
    ObjectNotFoundError,
    SignatureError,
    SignedDownload,
    SignedUpload,
    StorageProvider,
)


class LocalStorageProvider(StorageProvider):
    name = "local"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        self._root = os.path.abspath(self._s.storage_local_root)
        os.makedirs(self._root, exist_ok=True)

    # --- path mapping (traversal-safe) ---
    def _disk_path(self, storage_key: str) -> str:
        digest = hashlib.sha256(storage_key.encode("utf-8")).hexdigest()
        # Two-level fan-out; filename is the hash, so untrusted keys can't escape.
        return os.path.join(self._root, digest[:2], digest[2:4], digest)

    # --- HMAC signing for local signed URLs ---
    def _sign(self, storage_key: str, action: str, expires_at: int) -> str:
        msg = f"{action}:{storage_key}:{expires_at}".encode("utf-8")
        return hmac.new(self._s.jwt_secret_key.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    def verify_signature(self, storage_key: str, action: str, expires_at: int, signature: str) -> None:
        if expires_at < int(time.time()):
            raise SignatureError("Signed URL has expired.")
        expected = self._sign(storage_key, action, expires_at)
        if not hmac.compare_digest(expected, signature or ""):
            raise SignatureError("Invalid signature.")

    def _signed_url(self, storage_key: str, action: str) -> tuple[str, int]:
        expires_at = int(time.time()) + self._s.signed_url_expiration_seconds
        sig = self._sign(storage_key, action, expires_at)
        qs = urlencode({"key": storage_key, "action": action, "expires": expires_at, "sig": sig})
        # Relative API path; the documents router serves/accepts it after auth.
        return f"/api/v1/documents/_local-object?{qs}", expires_at

    def create_upload_url(self, storage_key: str, content_type: str) -> SignedUpload:
        url, expires_at = self._signed_url(storage_key, "upload")
        return SignedUpload(
            url=url, method="PUT", headers={"Content-Type": content_type or "application/octet-stream"},
            storage_key=storage_key, expires_at=expires_at,
        )

    def create_download_url(self, storage_key: str) -> SignedDownload:
        url, expires_at = self._signed_url(storage_key, "download")
        return SignedDownload(url=url, expires_at=expires_at)

    def put_object(self, storage_key: str, data: bytes, content_type: str | None = None) -> None:
        path = self._disk_path(storage_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)

    def get_object(self, storage_key: str) -> bytes:
        path = self._disk_path(storage_key)
        if not os.path.exists(path):
            raise ObjectNotFoundError(storage_key)
        with open(path, "rb") as fh:
            return fh.read()

    def delete_object(self, storage_key: str) -> None:
        path = self._disk_path(storage_key)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass  # idempotent delete

    def object_exists(self, storage_key: str) -> bool:
        return os.path.exists(self._disk_path(storage_key))

    def get_object_metadata(self, storage_key: str) -> ObjectMetadata:
        path = self._disk_path(storage_key)
        if not os.path.exists(path):
            raise ObjectNotFoundError(storage_key)
        return ObjectMetadata(storage_key=storage_key, size_bytes=os.path.getsize(path), content_type=None)
