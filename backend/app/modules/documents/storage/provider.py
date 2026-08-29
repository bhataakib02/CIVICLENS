"""Storage provider abstraction (prompt §8, §9, ADR-005).

The application depends on StorageProvider, never on a vendor SDK directly.
File bytes live in object storage; the DB holds only a non-guessable
storage_key. Access is always via short-lived signed URLs after an
authorization check — objects are never public or predictably keyed.

Operations:
    create_upload_url(storage_key, content_type) -> signed upload target
    create_download_url(storage_key)             -> short-lived signed download
    put_object(storage_key, data, content_type)  -> direct server-side store
    get_object(storage_key)                       -> bytes (for processing)
    delete_object(storage_key)
    object_exists(storage_key)
    get_object_metadata(storage_key)
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass


class StorageError(Exception):
    pass


class ObjectNotFoundError(StorageError):
    pass


class SignatureError(StorageError):
    """Signed URL invalid or expired."""


@dataclass
class SignedUpload:
    url: str
    method: str
    headers: dict[str, str]
    storage_key: str
    expires_at: int


@dataclass
class SignedDownload:
    url: str
    expires_at: int


@dataclass
class ObjectMetadata:
    storage_key: str
    size_bytes: int
    content_type: str | None


def generate_storage_key(*, citizen_profile_id: uuid.UUID, document_id: uuid.UUID, ext: str) -> str:
    """Non-guessable, non-citizen-derived key. Never built from user filenames.

    Layout groups by profile for lifecycle rules but uses opaque UUIDs, so keys
    are neither public nor predictable (threat-model #1/#2).
    """
    safe_ext = "".join(c for c in (ext or "").lower() if c.isalnum())[:8]
    suffix = f".{safe_ext}" if safe_ext else ""
    # A random component prevents key guessing even if ids leak.
    rand = uuid.uuid4().hex
    return f"documents/{citizen_profile_id}/{document_id}/{rand}{suffix}"


class StorageProvider(ABC):
    name = "abstract"

    @abstractmethod
    def create_upload_url(self, storage_key: str, content_type: str) -> SignedUpload: ...

    @abstractmethod
    def create_download_url(self, storage_key: str) -> SignedDownload: ...

    @abstractmethod
    def put_object(self, storage_key: str, data: bytes, content_type: str | None = None) -> None: ...

    @abstractmethod
    def get_object(self, storage_key: str) -> bytes: ...

    @abstractmethod
    def delete_object(self, storage_key: str) -> None: ...

    @abstractmethod
    def object_exists(self, storage_key: str) -> bool: ...

    @abstractmethod
    def get_object_metadata(self, storage_key: str) -> ObjectMetadata: ...
