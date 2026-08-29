"""Applications persistence layer.

Paginated list queries use joinedload to avoid N+1 (prompt §53). The submit
path locks the application row (SELECT ... FOR UPDATE) for concurrency safety
(prompt §18), and the DB partial-unique index guarantees at most one live
submission.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.application import (
    Application,
    ApplicationAction,
    ApplicationAssignment,
    ApplicationSubmission,
)
from app.models.enums import ActionRequiredStatus, ApplicationStatus, SubmissionStatus


class ApplicationsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, application: Application) -> Application:
        self._session.add(application)
        self._session.flush()
        return application

    def get(self, application_id: uuid.UUID) -> Application | None:
        return self._session.get(Application, application_id)

    def get_with_related(self, application_id: uuid.UUID) -> Application | None:
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(
                joinedload(Application.history),
                joinedload(Application.documents),
                joinedload(Application.submissions),
                joinedload(Application.actions),
            )
        )
        return self._session.scalars(stmt).unique().first()

    def get_for_update(self, application_id: uuid.UUID) -> Application | None:
        """Row-lock the application for the transactional submit path."""
        stmt = select(Application).where(Application.id == application_id).with_for_update()
        return self._session.scalars(stmt).first()

    def number_exists(self, application_number: str) -> bool:
        return (
            self._session.scalar(
                select(func.count()).select_from(Application).where(
                    Application.application_number == application_number
                )
            )
            or 0
        ) > 0

    def _scoped(
        self, stmt: Select, *, citizen_profile_id, assigned_case_worker_id, status
    ) -> Select:
        if citizen_profile_id is not None:
            stmt = stmt.where(Application.citizen_profile_id == citizen_profile_id)
        if assigned_case_worker_id is not None:
            stmt = stmt.where(Application.assigned_case_worker_id == assigned_case_worker_id)
        if status is not None:
            stmt = stmt.where(Application.status == status)
        return stmt

    def count(self, *, citizen_profile_id=None, assigned_case_worker_id=None, status=None) -> int:
        stmt = self._scoped(
            select(func.count()).select_from(Application),
            citizen_profile_id=citizen_profile_id,
            assigned_case_worker_id=assigned_case_worker_id, status=status,
        )
        return int(self._session.scalar(stmt) or 0)

    def list(
        self, *, citizen_profile_id=None, assigned_case_worker_id=None, status=None,
        limit: int, offset: int,
    ) -> list[Application]:
        stmt = self._scoped(
            select(Application), citizen_profile_id=citizen_profile_id,
            assigned_case_worker_id=assigned_case_worker_id, status=status,
        ).order_by(Application.created_at.desc(), Application.id).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    # --- submissions ---
    def live_submission(self, application_id: uuid.UUID) -> ApplicationSubmission | None:
        stmt = select(ApplicationSubmission).where(
            ApplicationSubmission.application_id == application_id,
            ApplicationSubmission.status != SubmissionStatus.FAILED,
        )
        return self._session.scalars(stmt).first()

    def submission_by_idempotency(
        self, application_id: uuid.UUID, idempotency_key: str
    ) -> ApplicationSubmission | None:
        stmt = select(ApplicationSubmission).where(
            ApplicationSubmission.application_id == application_id,
            ApplicationSubmission.idempotency_key == idempotency_key,
        )
        return self._session.scalars(stmt).first()

    def add_submission(self, submission: ApplicationSubmission) -> ApplicationSubmission:
        self._session.add(submission)
        self._session.flush()
        return submission

    # --- assignments / actions ---
    def add_assignment(self, assignment: ApplicationAssignment) -> None:
        self._session.add(assignment)
        self._session.flush()

    def add_action(self, action: ApplicationAction) -> ApplicationAction:
        self._session.add(action)
        self._session.flush()
        return action

    def open_actions(self, application_id: uuid.UUID) -> list[ApplicationAction]:
        stmt = select(ApplicationAction).where(
            ApplicationAction.application_id == application_id,
            ApplicationAction.status == ActionRequiredStatus.OPEN,
        )
        return list(self._session.scalars(stmt))
