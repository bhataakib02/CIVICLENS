"""Storage provider factory + package exports.

Fail-closed: the local filesystem provider is dev/test only; selecting it while
ENVIRONMENT=production raises. Production must use the private, encrypted S3
provider.
"""
from __future__ import annotations

from app.core.config import Settings, get_settings
from app.modules.documents.storage.local import LocalStorageProvider
from app.modules.documents.storage.provider import (
    ObjectMetadata,
    ObjectNotFoundError,
    SignatureError,
    SignedDownload,
    SignedUpload,
    StorageError,
    StorageProvider,
    generate_storage_key,
)
from app.modules.documents.storage.s3 import S3StorageProvider

_singleton: dict[str, StorageProvider] = {}


def get_storage_provider(settings: Settings | None = None) -> StorageProvider:
    settings = settings or get_settings()
    provider = settings.storage_provider.lower()
    cache_key = f"{provider}:{settings.storage_local_root}:{settings.s3_bucket}"
    if cache_key in _singleton:
        return _singleton[cache_key]

    if provider == "local":
        if settings.is_production:
            raise StorageError(
                "The local storage provider must not be used in production. "
                "Configure STORAGE_PROVIDER=s3 with a private, encrypted bucket."
            )
        inst: StorageProvider = LocalStorageProvider(settings)
    elif provider == "s3":
        inst = S3StorageProvider(settings)
    else:
        raise StorageError(f"Unknown STORAGE_PROVIDER '{provider}'.")
    _singleton[cache_key] = inst
    return inst


def reset_storage_cache() -> None:
    _singleton.clear()


__all__ = [
    "StorageProvider",
    "LocalStorageProvider",
    "S3StorageProvider",
    "get_storage_provider",
    "reset_storage_cache",
    "generate_storage_key",
    "SignedUpload",
    "SignedDownload",
    "ObjectMetadata",
    "StorageError",
    "ObjectNotFoundError",
    "SignatureError",
]
