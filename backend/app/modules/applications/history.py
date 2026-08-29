"""Application status history writer (prompt §26).

Append-only. Records every state change with from/to/actor/reason/metadata.
Flushes into the caller's transaction (never commits) so history + the state
change commit atomically.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.application import ApplicationStatusHistory


class HistoryWriter:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        application_id: uuid.UUID,
        from_status: str | None,
        to_status: str,
        actor_user_id: uuid.UUID | None,
        note: str | None = None,
        metadata: dict | None = None,
    ) -> ApplicationStatusHistory:
        entry = ApplicationStatusHistory(
            application_id=application_id,
            from_status=from_status,
            to_status=to_status,
            actor_user_id=actor_user_id,
            note=note,
            meta=metadata,
        )
        self._session.add(entry)
        self._session.flush()
        return entry
