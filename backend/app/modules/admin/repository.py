"""Admin data-access layer.

Read-only queries for admin dashboards, audit-log retrieval, citizen search,
notification operations, and user management. Never exposes raw storage
keys or PII beyond what the caller is authorized to see.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.citizen_profile import CitizenProfile
from app.models.consent import ConsentRecord
from app.models.document import Document
from app.models.enums import (
    ApplicationStatus,
    DocumentStatus,
    IngestionJobStatus,
    NotificationStatus,
    SchemeVersionStatus,
    UserRole,
    VerificationStatus,
)
from app.models.knowledge import KnowledgeSource
from app.models.notification import Notification
from app.models.scheme import SchemeVersion
from app.models.user import User


def _mask_phone(phone: str | None) -> str | None:
    if not phone or len(phone) < 4:
        return None
    return "X" * (len(phone) - 4) + phone[-4:]


class AdminRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    # ─── Dashboard ──────────────────────────────────────────────────────── #
    def dashboard_metrics(self) -> dict[str, int]:
        s = self._s
        return {
            "applications_pending_review": s.scalar(
                select(func.count(Application.id)).where(
                    Application.status == ApplicationStatus.SUBMITTED
                )
            )
            or 0,
            "applications_action_required": s.scalar(
                select(func.count(Application.id)).where(
                    Application.status.in_(
                        [ApplicationStatus.ACTION_REQUIRED, ApplicationStatus.INFO_REQUESTED]
                    )
                )
            )
            or 0,
            "documents_verification_required": s.scalar(
                select(func.count(Document.id)).where(
                    Document.status == DocumentStatus.VERIFICATION_REQUIRED
                )
            )
            or 0,
            "scheme_drafts_awaiting_review": s.scalar(
                select(func.count(SchemeVersion.id)).where(
                    SchemeVersion.status == SchemeVersionStatus.IN_REVIEW
                )
            )
            or 0,
            "knowledge_sources_pending": s.scalar(
                select(func.count(KnowledgeSource.id)).where(
                    KnowledgeSource.verification_status == VerificationStatus.PENDING
                )
            )
            or 0,
            "notifications_failed": s.scalar(
                select(func.count(Notification.id)).where(
                    Notification.status == NotificationStatus.FAILED
                )
            )
            or 0,
            "total_citizens": s.scalar(
                select(func.count(User.id)).where(User.role == UserRole.CITIZEN)
            )
            or 0,
            "total_applications": s.scalar(select(func.count(Application.id))) or 0,
        }

    # ─── Audit logs ─────────────────────────────────────────────────────── #
    def _audit_query(
        self,
        *,
        actor_id: uuid.UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> Select:
        q = select(AuditLog).order_by(AuditLog.created_at.desc())
        if actor_id:
            q = q.where(AuditLog.actor_user_id == actor_id)
        if action:
            q = q.where(AuditLog.action == action)
        if entity_type:
            q = q.where(AuditLog.entity_type == entity_type)
        if date_from:
            q = q.where(AuditLog.created_at >= date_from)
        if date_to:
            q = q.where(AuditLog.created_at <= date_to)
        return q

    def list_audit_logs(
        self,
        *,
        actor_id: uuid.UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        base = self._audit_query(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            date_from=date_from,
            date_to=date_to,
        )
        total = self._s.scalar(
            select(func.count()).select_from(base.subquery())
        ) or 0
        rows = list(self._s.scalars(base.limit(limit).offset(offset)))
        return rows, total

    # ─── Citizen management ─────────────────────────────────────────────── #
    def search_citizens(
        self,
        *,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        base = select(User).where(User.role == UserRole.CITIZEN)
        if q:
            pattern = f"%{q}%"
            base = base.where(
                or_(
                    User.email.ilike(pattern),
                    User.phone_number.ilike(pattern),
                )
            )
        base = base.order_by(User.created_at.desc())
        total = self._s.scalar(
            select(func.count()).select_from(base.subquery())
        ) or 0
        rows = list(
            self._s.scalars(base.limit(page_size).offset((page - 1) * page_size))
        )
        return rows, total

    def get_citizen_user(self, user_id: uuid.UUID) -> User | None:
        return self._s.get(User, user_id)

    def get_citizen_profile(self, user_id: uuid.UUID) -> CitizenProfile | None:
        return self._s.scalar(
            select(CitizenProfile).where(CitizenProfile.user_id == user_id)
        )

    def citizen_applications(self, profile_id: uuid.UUID) -> list[Application]:
        return list(
            self._s.scalars(
                select(Application)
                .where(Application.citizen_profile_id == profile_id)
                .order_by(Application.created_at.desc())
            )
        )

    def citizen_documents(self, profile_id: uuid.UUID) -> list[Document]:
        return list(
            self._s.scalars(
                select(Document)
                .where(Document.citizen_profile_id == profile_id)
                .order_by(Document.created_at.desc())
            )
        )

    def citizen_consents(self, citizen_id: uuid.UUID) -> list[ConsentRecord]:
        return list(
            self._s.scalars(
                select(ConsentRecord)
                .where(ConsentRecord.citizen_id == citizen_id)
                .order_by(ConsentRecord.granted_at.desc())
            )
        )

    # ─── Notification operations ────────────────────────────────────────── #
    def list_notifications_ops(
        self,
        *,
        status: str | None = None,
        channel: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        base = select(Notification).order_by(Notification.created_at.desc())
        if status:
            try:
                ns = NotificationStatus(status)
                base = base.where(Notification.status == ns)
            except ValueError:
                pass
        if channel:
            base = base.where(Notification.channel == channel)
        total = self._s.scalar(
            select(func.count()).select_from(base.subquery())
        ) or 0
        rows = list(
            self._s.scalars(base.limit(page_size).offset((page - 1) * page_size))
        )
        return rows, total

    def get_notification(self, notification_id: uuid.UUID) -> Notification | None:
        return self._s.get(Notification, notification_id)

    # ─── User management ────────────────────────────────────────────────── #
    def list_users(
        self,
        *,
        role: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        base = select(User).order_by(User.created_at.desc())
        if role:
            try:
                r = UserRole(role)
                base = base.where(User.role == r)
            except ValueError:
                pass
        total = self._s.scalar(
            select(func.count()).select_from(base.subquery())
        ) or 0
        rows = list(
            self._s.scalars(base.limit(page_size).offset((page - 1) * page_size))
        )
        return rows, total

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self._s.get(User, user_id)

    # ─── Agent consent-scoped access ────────────────────────────────────── #
    def agent_authorized_citizens(
        self, agent_user_id: uuid.UUID
    ) -> list[dict]:
        """Return citizens for whom this agent has active (non-revoked) consent."""
        consents = list(
            self._s.scalars(
                select(ConsentRecord).where(
                    and_(
                        ConsentRecord.agent_id == agent_user_id,
                        ConsentRecord.revoked_at.is_(None),
                    )
                )
            )
        )
        results = []
        seen_citizen_ids: set[uuid.UUID] = set()
        for c in consents:
            if c.citizen_id in seen_citizen_ids:
                continue
            seen_citizen_ids.add(c.citizen_id)
            profile = self._s.get(CitizenProfile, c.citizen_id)
            if profile is None:
                continue
            user = self._s.get(User, profile.user_id) if profile else None
            results.append({
                "citizen_id": str(c.citizen_id),
                "user_id": str(profile.user_id) if profile else None,
                "consent_status": "active",
                "consent_id": str(c.id),
                "phone_number_masked": _mask_phone(user.phone_number) if user else None,
                "email": user.email if user else None,
                "profile_completeness": profile.profile_completeness if profile else 0,
            })
        return results

    def agent_has_active_consent(
        self, agent_user_id: uuid.UUID, citizen_profile_id: uuid.UUID
    ) -> bool:
        """Check whether the agent has active consent for this citizen."""
        return (
            self._s.scalar(
                select(func.count(ConsentRecord.id)).where(
                    and_(
                        ConsentRecord.agent_id == agent_user_id,
                        ConsentRecord.citizen_id == citizen_profile_id,
                        ConsentRecord.revoked_at.is_(None),
                    )
                )
            )
            or 0
        ) > 0

    @staticmethod
    def mask_phone(phone: str | None) -> str | None:
        return _mask_phone(phone)
