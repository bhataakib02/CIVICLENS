"""Application workflow — the transactional domain operations (prompt §16, §42).

Each mutating operation is transactional: it flushes all effects then commits
once (or rolls back). The submit path locks the application row, validates
eligibility + documents + state, creates exactly one submission (DB
partial-unique index is the final guard), transitions status via the state
machine, writes history + audit + an outbox event, then commits.

This module owns state changes; service.py handles authorization + view
assembly and calls into here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.application import (
    Application,
    ApplicationAction,
    ApplicationAssignment,
    ApplicationSubmission,
)
from app.models.enums import (
    ActionRequiredStatus,
    ApplicationStatus,
    AssignmentAction,
    ReviewAction,
    SubmissionStatus,
)
from app.modules.applications import state_machine as sm
from app.modules.applications.history import HistoryWriter
from app.modules.applications.repository import ApplicationsRepository
from app.modules.applications.submission import (
    SubmissionFailedError,
    get_submission_provider,
)
from app.modules.applications.validators import (
    ApplicationAlreadySubmittedError,
    SubmissionFailedAppError,
    validate_documents,
    validate_eligibility,
    validate_submittable_state,
)
from app.modules.audit.service import AuditAction, AuditService
from app.modules.notifications.service import OutboxWriter

logger = get_logger("civiclens.applications.workflow")


class ApplicationWorkflow:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._s = settings or get_settings()
        self._repo = ApplicationsRepository(session)
        self._history = HistoryWriter(session)
        self._audit = AuditService(session)
        self._outbox = OutboxWriter(session)

    # ------------------------------------------------------------------ #
    def _transition(self, app: Application, target: ApplicationStatus, *, actor_id, role,
                    note=None, metadata=None) -> None:
        sm.assert_transition(app.status, target, role=role)
        from_status = app.status.value
        app.status = target
        self._history.record(
            application_id=app.id, from_status=from_status, to_status=target.value,
            actor_user_id=actor_id, note=note, metadata=metadata,
        )

    def _emit(self, app: Application, event_type: str, subject: str, *, actor_id=None) -> None:
        # PII-free outbox payload (ids + status + subject only). Typed envelope.
        from app.models.enums import DomainEventType

        etype = DomainEventType(event_type)
        self._outbox.enqueue_simple(
            event_type=etype, aggregate_type="APPLICATION", aggregate_id=app.id,
            actor_id=actor_id,
            payload={
                "application_id": str(app.id),
                "citizen_profile_id": str(app.citizen_profile_id),
                "application_number": app.application_number,
                "status": app.status.value,
                "subject": subject,
            },
        )

    # ------------------------------------------------------------------ #
    def mark_ready(self, app: Application, *, actor_id, role) -> Application:
        self._transition(app, ApplicationStatus.READY_FOR_SUBMISSION, actor_id=actor_id, role=role,
                         note="All requirements satisfied.")
        self._audit.record(action=AuditAction.APPLICATION_UPDATED, entity_type="application",
                           entity_id=app.id, actor_user_id=actor_id)
        self._session.commit()
        self._session.refresh(app)
        return app

    def submit(
        self, application_id: uuid.UUID, *, actor_id, role, checklist, request_id: str | None,
        idempotency_key: str | None, simulate_provider_failure: bool = False,
    ) -> Application:
        # 1. Lock the application row (concurrency safety).
        app = self._repo.get_for_update(application_id)
        if app is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("Application not found.")

        # 2. Idempotency: a prior live submission (or same idempotency key) short-circuits.
        if idempotency_key:
            prior = self._repo.submission_by_idempotency(app.id, idempotency_key)
            if prior is not None:
                return app  # same logical submission; no duplicate
        existing_live = self._repo.live_submission(app.id)
        if existing_live is not None:
            raise ApplicationAlreadySubmittedError()

        # 3. Validate preconditions (eligibility, documents, state).
        validate_submittable_state(app.status)
        validate_eligibility(app.eligibility_snapshot)
        validate_documents(checklist)

        # 4. Move DRAFT -> READY_FOR_SUBMISSION -> SUBMISSION_PENDING (legal path).
        #    A prior SUBMISSION_FAILED retry re-enters via READY_FOR_SUBMISSION.
        if app.status is ApplicationStatus.SUBMISSION_FAILED:
            self._transition(app, ApplicationStatus.READY_FOR_SUBMISSION, actor_id=actor_id, role=role,
                             note="Retrying submission.")
        if app.status is ApplicationStatus.DRAFT:
            self._transition(app, ApplicationStatus.READY_FOR_SUBMISSION, actor_id=actor_id, role=role)
        if app.status is ApplicationStatus.READY_FOR_SUBMISSION:
            self._transition(app, ApplicationStatus.SUBMISSION_PENDING, actor_id=actor_id, role=role,
                             note="Submitting to government provider.")

        # 5. Call the government submission provider (mock in non-prod).
        provider = get_submission_provider(self._s)
        payload = {"application_number": app.application_number,
                   "_simulate_provider_failure": simulate_provider_failure}
        submission = ApplicationSubmission(
            application_id=app.id, status=SubmissionStatus.PENDING,
            submission_method=None, submitted_by=actor_id, request_id=request_id,
            idempotency_key=idempotency_key,
        )
        try:
            result = provider.submit_application(application_number=app.application_number, payload=payload)
        except SubmissionFailedError as exc:
            # Provider failure: record a FAILED submission, move to SUBMISSION_FAILED, rollback-safe.
            submission.status = SubmissionStatus.FAILED
            submission.submission_method = _method_default()
            submission.response_metadata = {"error": "provider_failure"}
            self._repo.add_submission(submission)
            self._transition(app, ApplicationStatus.SUBMISSION_FAILED, actor_id=actor_id, role=role,
                             note="Government submission provider failed.")
            self._audit.record(action=AuditAction.APPLICATION_SUBMISSION_FAILED, entity_type="application",
                               entity_id=app.id, actor_user_id=actor_id)
            self._session.commit()
            logger.warning("application_submission_failed", extra={"application_id": str(app.id)})
            raise SubmissionFailedAppError() from exc

        # 6. Persist the successful submission + transition SUBMITTED.
        submission.status = SubmissionStatus.SUBMITTED
        submission.submission_method = result.method
        submission.external_reference = result.external_reference
        submission.response_metadata = result.metadata  # non-sensitive
        submission.submitted_at = datetime.now(timezone.utc)
        try:
            self._repo.add_submission(submission)
            self._session.flush()
        except IntegrityError as exc:
            # A concurrent request won the partial-unique index race.
            self._session.rollback()
            raise ApplicationAlreadySubmittedError() from exc

        app.submitted_at = datetime.now(timezone.utc)
        self._transition(app, ApplicationStatus.SUBMITTED, actor_id=actor_id, role=role,
                         note=f"Submitted (ref {result.external_reference}).",
                         metadata={"external_reference": result.external_reference})
        self._audit.record(action=AuditAction.APPLICATION_SUBMITTED, entity_type="application",
                           entity_id=app.id, actor_user_id=actor_id,
                           diff={"external_reference": result.external_reference, "provider": result.provider})
        self._emit(app, "APPLICATION_SUBMITTED", "Your application was submitted.")
        self._session.commit()
        self._session.refresh(app)
        logger.info("application_submitted", extra={"application_id": str(app.id)})
        return app

    def withdraw(self, app: Application, *, actor_id, role, reason: str | None) -> Application:
        self._transition(app, ApplicationStatus.WITHDRAWN, actor_id=actor_id, role=role, note=reason)
        self._audit.record(action=AuditAction.APPLICATION_WITHDRAWN, entity_type="application",
                           entity_id=app.id, actor_user_id=actor_id)
        self._emit(app, "APPLICATION_STATUS_CHANGED", "Your application was withdrawn.")
        self._session.commit()
        self._session.refresh(app)
        return app

    # --- case management ---
    def assign(self, app: Application, *, case_worker_id, actor_id) -> Application:
        previous = app.assigned_case_worker_id
        if case_worker_id is None:
            action = AssignmentAction.UNASSIGN
            audit_action = AuditAction.APPLICATION_UNASSIGNED
        elif previous is not None and previous != case_worker_id:
            action = AssignmentAction.REASSIGN
            audit_action = AuditAction.APPLICATION_REASSIGNED
        else:
            action = AssignmentAction.ASSIGN
            audit_action = AuditAction.APPLICATION_ASSIGNED
        app.assigned_case_worker_id = case_worker_id
        self._repo.add_assignment(ApplicationAssignment(
            application_id=app.id, action=action, case_worker_id=case_worker_id,
            previous_case_worker_id=previous, assigned_by=actor_id,
        ))
        self._audit.record(action=audit_action, entity_type="application", entity_id=app.id,
                           actor_user_id=actor_id,
                           diff={"case_worker_id": str(case_worker_id) if case_worker_id else None})
        self._session.commit()
        self._session.refresh(app)
        return app

    def review(self, app: Application, *, action: ReviewAction, reason: str, required_items,
               actor_id, role) -> Application:
        # A submitted application enters review on first review action.
        if app.status is ApplicationStatus.SUBMITTED:
            self._transition(app, ApplicationStatus.UNDER_REVIEW, actor_id=actor_id, role=role,
                             note="Review started.")

        if action is ReviewAction.APPROVE:
            self._transition(app, ApplicationStatus.APPROVED, actor_id=actor_id, role=role, note=reason)
            self._audit.record(action=AuditAction.APPLICATION_APPROVED, entity_type="application",
                               entity_id=app.id, actor_user_id=actor_id)
            self._emit(app, "APPLICATION_APPROVED", "Your application was approved.")
        elif action is ReviewAction.REJECT:
            self._transition(app, ApplicationStatus.REJECTED, actor_id=actor_id, role=role, note=reason)
            self._audit.record(action=AuditAction.APPLICATION_REJECTED, entity_type="application",
                               entity_id=app.id, actor_user_id=actor_id)
            self._emit(app, "APPLICATION_REJECTED", "Your application was rejected.")
        else:  # REQUEST_ACTION
            self._transition(app, ApplicationStatus.ACTION_REQUIRED, actor_id=actor_id, role=role, note=reason)
            self._repo.add_action(ApplicationAction(
                application_id=app.id, reason=reason,
                required_items={"items": required_items} if required_items else None,
                status=ActionRequiredStatus.OPEN, created_by=actor_id,
            ))
            self._audit.record(action=AuditAction.APPLICATION_ACTION_REQUIRED, entity_type="application",
                               entity_id=app.id, actor_user_id=actor_id)
            self._emit(app, "APPLICATION_ACTION_REQUIRED", "Action is required on your application.")
        self._audit.record(action=AuditAction.APPLICATION_REVIEWED, entity_type="application",
                           entity_id=app.id, actor_user_id=actor_id, diff={"action": action.value})
        self._session.commit()
        self._session.refresh(app)
        return app

    def resolve_action(self, app: Application, *, actor_id, role, note: str | None) -> Application:
        open_actions = self._repo.open_actions(app.id)
        now = datetime.now(timezone.utc)
        for a in open_actions:
            a.status = ActionRequiredStatus.RESOLVED
            a.resolved_at = now
        self._transition(app, ApplicationStatus.UNDER_REVIEW, actor_id=actor_id, role=role,
                         note=note or "Citizen resolved requested action.")
        self._audit.record(action=AuditAction.APPLICATION_ACTION_RESOLVED, entity_type="application",
                           entity_id=app.id, actor_user_id=actor_id)
        self._emit(app, "APPLICATION_STATUS_CHANGED", "Your response was submitted for review.")
        self._session.commit()
        self._session.refresh(app)
        return app

    def complete(self, app: Application, *, actor_id, role) -> Application:
        self._transition(app, ApplicationStatus.COMPLETED, actor_id=actor_id, role=role)
        app.completed_at = datetime.now(timezone.utc)
        self._audit.record(action=AuditAction.APPLICATION_COMPLETED, entity_type="application",
                           entity_id=app.id, actor_user_id=actor_id)
        self._emit(app, "APPLICATION_COMPLETED", "Your application is complete.")
        self._session.commit()
        self._session.refresh(app)
        return app


def _method_default():
    from app.models.enums import SubmissionMethod

    return SubmissionMethod.MOCK
