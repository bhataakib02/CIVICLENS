"""Admin service layer.

Business logic for admin operations. All authorization is enforced here,
never in the router alone. The service layer is the single point of truth
for permission checks on admin operations.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from app.core.security import hash_password, validate_password_policy
from app.models.enums import NotificationStatus, UserRole, UserStatus
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import (
    AuditLogOut,
    AuditLogPage,
    CitizenDetailAdmin,
    CitizenSummaryAdmin,
    CitizenSummaryPage,
    ConsentOutAdmin,
    DashboardMetrics,
    NotificationOpsOut,
    NotificationOpsPage,
    SystemHealth,
    UserCreateInput,
    UserOut,
    UserPage,
    UserUpdateInput,
)
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.repository import AuthRepository


_STAFF_ROLES = {UserRole.ADMIN.value, UserRole.SCHEME_ADMIN.value, UserRole.AGENT.value}
_ADMIN_ONLY = {UserRole.ADMIN.value}


class AdminService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = AdminRepository(session)
        self._audit = AuditService(session)

    # ─── Authorization helpers ──────────────────────────────────────────── #
    @staticmethod
    def _require_admin(current: CurrentUser) -> None:
        if current.role not in (UserRole.ADMIN.value, UserRole.SCHEME_ADMIN.value, UserRole.AGENT.value):
            raise PermissionDeniedError("Admin privileges required.")

    @staticmethod
    def _require_staff(current: CurrentUser) -> None:
        if current.role not in _STAFF_ROLES:
            raise PermissionDeniedError()

    # ─── Dashboard ──────────────────────────────────────────────────────── #
    def dashboard(self, current: CurrentUser) -> DashboardMetrics:
        self._require_staff(current)
        metrics = self._repo.dashboard_metrics()
        return DashboardMetrics(**metrics)

    # ─── Audit logs ─────────────────────────────────────────────────────── #
    def list_audit_logs(
        self,
        current: CurrentUser,
        *,
        actor_id: uuid.UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogPage:
        self._require_admin(current)
        rows, total = self._repo.list_audit_logs(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            date_from=date_from,
            date_to=date_to,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        items = [
            AuditLogOut(
                id=str(r.id),
                actor_user_id=str(r.actor_user_id) if r.actor_user_id else None,
                action=r.action,
                entity_type=r.entity_type,
                entity_id=str(r.entity_id) if r.entity_id else None,
                diff=r.diff,
                created_at=r.created_at,
            )
            for r in rows
        ]
        return AuditLogPage(items=items, total=total, page=page, page_size=page_size)

    # ─── Citizen management ─────────────────────────────────────────────── #
    def search_citizens(
        self,
        current: CurrentUser,
        *,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CitizenSummaryPage:
        self._require_staff(current)
        users, total = self._repo.search_citizens(q=q, page=page, page_size=page_size)
        items = [
            CitizenSummaryAdmin(
                user_id=str(u.id),
                email=u.email,
                phone_number_masked=AdminRepository.mask_phone(u.phone_number),
                role=u.role.value,
                status=u.status.value,
                created_at=u.created_at,
                profile_completeness=(
                    u.profile.profile_completeness if u.profile else 0.0
                ),
            )
            for u in users
        ]
        return CitizenSummaryPage(items=items, total=total, page=page, page_size=page_size)

    def get_citizen(
        self, current: CurrentUser, user_id: uuid.UUID
    ) -> CitizenDetailAdmin:
        self._require_staff(current)
        user = self._repo.get_citizen_user(user_id)
        if user is None or user.role != UserRole.CITIZEN:
            raise NotFoundError("Citizen not found.")

        profile = self._repo.get_citizen_profile(user_id)
        apps_count = 0
        docs_count = 0
        consents_count = 0
        profile_dict = None

        if profile is not None:
            apps = self._repo.citizen_applications(profile.id)
            docs = self._repo.citizen_documents(profile.id)
            consents = self._repo.citizen_consents(profile.id)
            apps_count = len(apps)
            docs_count = len(docs)
            consents_count = sum(1 for c in consents if c.revoked_at is None)
            profile_dict = {
                "id": str(profile.id),
                "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
                "gender": profile.gender,
                "category": profile.category,
                "occupation": profile.occupation,
                "declared_annual_income": float(profile.declared_annual_income) if profile.declared_annual_income else None,
                "disability_status": profile.disability_status,
                "family_size": profile.family_size,
                "profile_completeness": profile.profile_completeness,
                "current_version_no": profile.current_version_no,
            }

        # Record audit event for sensitive data access
        self._audit.record(
            action="admin.citizen_viewed",
            entity_type="user",
            entity_id=user_id,
            actor_user_id=current.id,
        )
        self._session.commit()

        return CitizenDetailAdmin(
            user_id=str(user.id),
            email=user.email,
            phone_number_masked=AdminRepository.mask_phone(user.phone_number),
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            profile=profile_dict,
            applications_count=apps_count,
            documents_count=docs_count,
            active_consents_count=consents_count,
        )

    def citizen_consents(
        self, current: CurrentUser, user_id: uuid.UUID
    ) -> list[ConsentOutAdmin]:
        self._require_staff(current)
        user = self._repo.get_citizen_user(user_id)
        if user is None or user.role != UserRole.CITIZEN:
            raise NotFoundError("Citizen not found.")
        profile = self._repo.get_citizen_profile(user_id)
        if profile is None:
            return []
        consents = self._repo.citizen_consents(profile.id)
        return [
            ConsentOutAdmin(
                id=str(c.id),
                citizen_id=str(c.citizen_id),
                consent_type=c.consent_type.value,
                purpose=c.purpose,
                scope=c.scope,
                version=c.version,
                agent_id=str(c.agent_id) if c.agent_id else None,
                granted_at=c.granted_at,
                revoked_at=c.revoked_at,
            )
            for c in consents
        ]

    def update_citizen(
        self, current: CurrentUser, user_id: uuid.UUID, data: dict
    ) -> CitizenDetailAdmin:
        self._require_staff(current)
        user = self._repo.get_citizen_user(user_id)
        if user is None:
            raise NotFoundError("Citizen not found.")
        
        if "email" in data and data["email"] is not None:
            user.email = data["email"]
        if "phone_number" in data and data["phone_number"] is not None:
            user.phone_number = data["phone_number"]
        if "password" in data and data["password"]:
            user.password_hash = hash_password(data["password"])
        if "status" in data and data["status"]:
            from app.models.user import UserStatus
            user.status = UserStatus(data["status"].lower())
            
        self._audit.record(
            action="admin.citizen_updated",
            entity_type="user",
            entity_id=user_id,
            actor_user_id=current.id,
        )
        self._session.commit()
        return self.get_citizen(current, user_id)

    def send_citizen_otp(self, current: CurrentUser, user_id: uuid.UUID) -> dict:
        self._require_staff(current)
        user = self._repo.get_citizen_user(user_id)
        if user is None:
            raise NotFoundError("Citizen not found.")
        
        target = user.email or user.phone_number
        if not target:
            raise ValidationError("Citizen has no registered email or phone number.")
            
        from app.modules.auth.otp_service import OTPService
        otp_service = OTPService(self._session)
        otp_service.request_otp(target=target)
        
        self._audit.record(
            action="admin.citizen_otp_dispatched",
            entity_type="user",
            entity_id=user_id,
            actor_user_id=current.id,
            diff={"target": target},
        )
        self._session.commit()
        return {
            "success": True,
            "message": f"Real 6-digit OTP dispatched to {target}.",
            "target": target,
        }

    def delete_citizen(
        self, current: CurrentUser, user_id: uuid.UUID
    ) -> dict:
        self._require_staff(current)
        user = self._repo.get_citizen_user(user_id)
        if user is None:
            raise NotFoundError("Citizen not found.")
            
        self._session.delete(user)
        self._audit.record(
            action="admin.citizen_deleted",
            entity_type="user",
            entity_id=user_id,
            actor_user_id=current.id,
        )
        self._session.commit()
        return {"success": True, "message": "Citizen record deleted."}

    def update_citizen_profile(
        self, current: CurrentUser, user_id: uuid.UUID, data: dict
    ) -> CitizenDetailAdmin:
        self._require_staff(current)
        profile = self._repo.get_citizen_profile(user_id)
        if profile is None:
            from app.models.profile import CitizenProfile
            profile = CitizenProfile(user_id=user_id)
            self._session.add(profile)
            
        if "category" in data and data["category"] is not None:
            profile.category = data["category"]
        if "occupation" in data and data["occupation"] is not None:
            profile.occupation = data["occupation"]
        if "gender" in data and data["gender"] is not None:
            profile.gender = data["gender"]
        if "declared_annual_income" in data and data["declared_annual_income"] is not None:
            profile.declared_annual_income = data["declared_annual_income"]
        if "disability_status" in data and data["disability_status"] is not None:
            profile.disability_status = data["disability_status"]
        if "family_size" in data and data["family_size"] is not None:
            profile.family_size = data["family_size"]
            
        self._audit.record(
            action="admin.citizen_profile_updated",
            entity_type="profile",
            entity_id=profile.id,
            actor_user_id=current.id,
        )
        self._session.commit()
        return self.get_citizen(current, user_id)

    # ─── Notification operations ────────────────────────────────────────── #
    def list_notifications(
        self,
        current: CurrentUser,
        *,
        status: str | None = None,
        channel: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> NotificationOpsPage:
        self._require_admin(current)
        rows, total = self._repo.list_notifications_ops(
            status=status, channel=channel, page=page, page_size=page_size
        )
        items = [
            NotificationOpsOut(
                id=str(n.id),
                user_id=str(n.user_id) if n.user_id else None,
                channel=n.channel.value,
                category=n.category.value,
                priority=n.priority.value,
                status=n.status.value,
                title=n.title or n.subject,
                entity_type=n.entity_type,
                entity_id=str(n.entity_id) if n.entity_id else None,
                created_at=n.created_at,
                sent_at=n.sent_at,
                failure_code=n.failure_code,
                attempts=n.attempts or 0,
            )
            for n in rows
        ]
        return NotificationOpsPage(items=items, total=total, page=page, page_size=page_size)

    def retry_notification(
        self, current: CurrentUser, notification_id: uuid.UUID
    ) -> NotificationOpsOut:
        self._require_admin(current)
        n = self._repo.get_notification(notification_id)
        if n is None:
            raise NotFoundError("Notification not found.")
        if n.status != NotificationStatus.FAILED:
            raise ConflictError("Only failed notifications can be retried.")
        n.status = NotificationStatus.PENDING
        n.attempts = (n.attempts or 0)  # reset won't change attempt count, just re-queue
        self._audit.record(
            action="admin.notification_retry",
            entity_type="notification",
            entity_id=n.id,
            actor_user_id=current.id,
        )
        self._session.commit()
        self._session.refresh(n)
        return NotificationOpsOut(
            id=str(n.id),
            user_id=str(n.user_id) if n.user_id else None,
            channel=n.channel.value,
            category=n.category.value,
            priority=n.priority.value,
            status=n.status.value,
            title=n.title or n.subject,
            entity_type=n.entity_type,
            entity_id=str(n.entity_id) if n.entity_id else None,
            created_at=n.created_at,
            sent_at=n.sent_at,
            failure_code=n.failure_code,
            attempts=n.attempts or 0,
        )

    # ─── User management ────────────────────────────────────────────────── #
    def list_users(
        self,
        current: CurrentUser,
        *,
        role: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserPage:
        self._require_admin(current)
        rows, total = self._repo.list_users(role=role, page=page, page_size=page_size)
        items = [
            UserOut(
                id=str(u.id),
                email=u.email,
                phone_number_masked=AdminRepository.mask_phone(u.phone_number),
                role=u.role.value,
                status=u.status.value,
                last_login_at=u.last_login_at,
                created_at=u.created_at,
            )
            for u in rows
        ]
        return UserPage(items=items, total=total, page=page, page_size=page_size)

    def create_user(
        self,
        current: CurrentUser,
        body: UserCreateInput,
        *,
        ip: str | None = None,
    ) -> UserOut:
        self._require_admin(current)

        # Validate role
        try:
            role = UserRole(body.role)
        except ValueError:
            raise ValidationError(f"Invalid role: {body.role}")
        if role == UserRole.CITIZEN:
            raise ValidationError("Citizens register through the citizen flow, not admin creation.")

        validate_password_policy(body.password)

        # Check uniqueness
        auth_repo = AuthRepository(self._session)
        if auth_repo.get_user_by_email(body.email):
            raise ConflictError("A user with this email already exists.")

        from app.models.user import User

        user = User(
            email=body.email.lower().strip(),
            password_hash=hash_password(body.password),
            role=role,
            status=UserStatus.ACTIVE,
        )
        self._session.add(user)
        self._audit.record(
            action="admin.user_created",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=current.id,
            diff={"role": role.value, "email": body.email},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(user)
        return UserOut(
            id=str(user.id),
            email=user.email,
            phone_number_masked=None,
            role=user.role.value,
            status=user.status.value,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )

    def update_user(
        self,
        current: CurrentUser,
        user_id: uuid.UUID,
        body: UserUpdateInput,
        *,
        ip: str | None = None,
    ) -> UserOut:
        self._require_admin(current)
        user = self._repo.get_user(user_id)
        if user is None:
            raise NotFoundError("User not found.")

        diff: dict = {}
        if body.role is not None:
            try:
                new_role = UserRole(body.role)
            except ValueError:
                raise ValidationError(f"Invalid role: {body.role}")
            diff["role"] = {"from": user.role.value, "to": new_role.value}
            user.role = new_role

        if body.status is not None:
            try:
                new_status = UserStatus(body.status)
            except ValueError:
                raise ValidationError(f"Invalid status: {body.status}")
            diff["status"] = {"from": user.status.value, "to": new_status.value}
            user.status = new_status

        if diff:
            self._audit.record(
                action="admin.user_updated",
                entity_type="user",
                entity_id=user.id,
                actor_user_id=current.id,
                diff=diff,
                ip=ip,
            )
            self._session.commit()
            self._session.refresh(user)

        return UserOut(
            id=str(user.id),
            email=user.email,
            phone_number_masked=AdminRepository.mask_phone(user.phone_number),
            role=user.role.value,
            status=user.status.value,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )

    def delete_user(self, current: CurrentUser, user_id: uuid.UUID) -> dict:
        self._require_admin(current)
        user = self._repo.get_user(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        self._session.delete(user)
        self._audit.record(
            action="admin.user_deleted",
            entity_type="user",
            entity_id=user_id,
            actor_user_id=current.id,
        )
        self._session.commit()
        return {"success": True, "message": "User deleted successfully."}

    # ─── System health ──────────────────────────────────────────────────── #
    def system_health(self, current: CurrentUser) -> SystemHealth:
        self._require_admin(current)
        from sqlalchemy import text

        db_ok = "ok"
        try:
            self._session.execute(text("SELECT 1"))
        except Exception:
            db_ok = "unavailable"

        redis_ok = "not_configured"
        try:
            from app.core.config import get_settings

            settings = get_settings()
            if settings.redis_url:
                import redis

                client = redis.Redis.from_url(settings.redis_url)
                client.ping()
                redis_ok = "ok"
        except Exception:
            redis_ok = "unavailable"

        overall = "healthy" if db_ok == "ok" else "degraded"
        return SystemHealth(database=db_ok, redis=redis_ok, overall=overall)

    # ─── Agent consent-scoped access ────────────────────────────────────── #
    def agent_citizens(self, current: CurrentUser) -> list[dict]:
        if current.role not in (UserRole.AGENT.value, UserRole.ADMIN.value, UserRole.SCHEME_ADMIN.value):
            raise PermissionDeniedError()
        return self._repo.agent_authorized_citizens(current.id)

    def agent_citizen_detail(
        self, current: CurrentUser, citizen_user_id: uuid.UUID
    ) -> CitizenDetailAdmin:
        if current.role not in (UserRole.AGENT.value, UserRole.ADMIN.value, UserRole.SCHEME_ADMIN.value):
            raise PermissionDeniedError()

        user = self._repo.get_citizen_user(citizen_user_id)
        if user is None or user.role != UserRole.CITIZEN:
            raise NotFoundError("Citizen not found.")

        profile = self._repo.get_citizen_profile(citizen_user_id)
        if profile is None:
            raise NotFoundError("Citizen profile not found.")

        # Verify consent
        if not self._repo.agent_has_active_consent(current.id, profile.id):
            raise PermissionDeniedError("No active consent for this citizen.")

        # Delegate to the same detail builder but record agent-specific audit
        self._audit.record(
            action="agent.citizen_viewed",
            entity_type="user",
            entity_id=citizen_user_id,
            actor_user_id=current.id,
        )
        self._session.commit()

        apps = self._repo.citizen_applications(profile.id)
        docs = self._repo.citizen_documents(profile.id)

        profile_dict = {
            "id": str(profile.id),
            "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
            "gender": profile.gender,
            "category": profile.category,
            "occupation": profile.occupation,
            "disability_status": profile.disability_status,
            "family_size": profile.family_size,
            "profile_completeness": profile.profile_completeness,
            "current_version_no": profile.current_version_no,
        }

        return CitizenDetailAdmin(
            user_id=str(user.id),
            email=user.email,
            phone_number_masked=AdminRepository.mask_phone(user.phone_number),
            role=user.role.value,
            status=user.status.value,
            created_at=user.created_at,
            profile=profile_dict,
            applications_count=len(apps),
            documents_count=len(docs),
        )
