"""Notification API response/request schemas (Pydantic)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: str
    type: str
    channel: str
    category: str
    priority: str
    status: str
    title: str | None = None
    body: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    read: bool = False
    created_at: str | None = None


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int


class UnreadCountOut(BaseModel):
    unread: int


class NotificationPreferencesOut(BaseModel):
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    application_updates: bool
    document_updates: bool
    scheme_updates: bool
    security_alerts: bool


class NotificationPreferencesUpdate(BaseModel):
    # security_alerts is intentionally NOT accepted (mandatory; prompt §16).
    model_config = ConfigDict(extra="forbid")

    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    push_enabled: bool | None = None
    in_app_enabled: bool | None = None
    application_updates: bool | None = None
    document_updates: bool | None = None
    scheme_updates: bool | None = None


class MarkAllReadOut(BaseModel):
    marked_read: int
