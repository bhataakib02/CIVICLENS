"""Applications application service (authorization + view assembly + creation).

Owns: object-level authorization, application creation (running/pinning the
eligibility snapshot + scheme_version), role-scoped listing, detail assembly
(citizen vs reviewer views), and delegating state changes to the workflow.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from app.core.logging import get_logger
from app.models.application import Application
from app.models.citizen_profile import CitizenProfile
from app.models.eligibility import EligibilityCheck
from app.models.enums import ApplicationStatus, ReviewAction, SchemeVersionStatus
from app.models.scheme import SchemeVersion
from app.modules.applications import state_machine as sm
from app.modules.applications.policies import (
    can_assign,
    can_review_application,
    can_view_application,
)
from app.modules.applications.repository import ApplicationsRepository
from app.modules.applications.requirements import Checklist, RequirementsService
from app.modules.applications.submission import generate_application_number
from app.modules.applications.validators import validate_eligibility
from app.modules.applications.workflow import ApplicationWorkflow
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.dependencies import CurrentUser
from app.modules.eligibility.compiler import rule_cache
from app.modules.eligibility.context import ContextBuilder
from app.modules.eligibility.engine import evaluate as engine_evaluate

logger = get_logger("civiclens.applications.service")


class ApplicationsService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._s = settings or get_settings()
        self._repo = ApplicationsRepository(session)
        self._reqs = RequirementsService(session)
        self._audit = AuditService(session)

    # ------------------------------------------------------------------ #
    def _profile_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        return self._session.scalar(select(CitizenProfile.id).where(CitizenProfile.user_id == user_id))

    def _load_authorized(self, current: CurrentUser, application_id: uuid.UUID) -> Application:
        app = self._repo.get(application_id)
        if app is None:
            raise NotFoundError("Application not found.")
        profile_id = self._profile_id(current.id)
        if not can_view_application(
            role=current.role, current_user_id=current.id, current_profile_id=profile_id,
            owner_profile_id=app.citizen_profile_id, assigned_case_worker_id=app.assigned_case_worker_id,
        ):
            raise NotFoundError("Application not found.")  # no existence disclosure
        return app

    def _resolve_version(self, scheme_id, scheme_version_id) -> SchemeVersion:
        if scheme_version_id is not None:
            v = self._session.get(SchemeVersion, scheme_version_id)
            if v is None:
                raise NotFoundError("Scheme version not found.")
            return v
        if scheme_id is not None:
            from app.modules.schemes.repository import SchemesRepository

            v = SchemesRepository(self._session).current_published_version(scheme_id)
            if v is None:
                raise NotFoundError("No currently-published version for this scheme.")
            return v
        raise ValidationError("scheme_version_id or scheme_id is required.")

    # ------------------------------------------------------------------ #
    def create(
        self, *, current: CurrentUser, scheme_id, scheme_version_id, scheme_specific_answers,
        document_ids, ip: str | None = None,
    ) -> Application:
        profile_id = self._profile_id(current.id)
        if profile_id is None:
            raise NotFoundError("Citizen profile not found.")
        version = self._resolve_version(scheme_id, scheme_version_id)

        # Run a deterministic eligibility evaluation and snapshot it (immutable).
        snapshot, check_id = self._evaluate_and_snapshot(profile_id, version)
        # Enforce product policy: NOT_ELIGIBLE cannot start (contract: 409).
        try:
            validate_eligibility(snapshot)
        except Exception:
            raise ConflictError(
                "Citizen is not eligible / likely_eligible for this scheme.",
                code="NOT_ELIGIBLE",
            )

        number = self._unique_number()
        app = Application(
            application_number=number,
            citizen_profile_id=profile_id,
            scheme_version_id=version.id,
            eligibility_check_id=check_id,
            eligibility_snapshot=snapshot,
            status=ApplicationStatus.DRAFT,
            scheme_specific_answers=scheme_specific_answers or {},
            deadline_at=version.effective_to,
        )
        self._repo.add(app)

        # Attach any provided (owned) documents.
        self._attach_documents(app, profile_id, document_ids or [])

        # Record initial DRAFT history + audit.
        from app.modules.applications.history import HistoryWriter

        HistoryWriter(self._session).record(
            application_id=app.id, from_status=None, to_status=ApplicationStatus.DRAFT.value,
            actor_user_id=current.id, note="Application created.",
        )
        self._audit.record(action=AuditAction.APPLICATION_CREATED, entity_type="application",
                           entity_id=app.id, actor_user_id=current.id,
                           diff={"scheme_version_id": str(version.id), "decision": snapshot.get("decision")}, ip=ip)
        self._session.commit()
        self._session.refresh(app)
        logger.info("application_created", extra={"application_id": str(app.id)})
        return app

    def _evaluate_and_snapshot(self, profile_id: uuid.UUID, version: SchemeVersion) -> tuple[dict, uuid.UUID | None]:
        from app.models.address import Address
        from app.modules.documents.evidence import DocumentFactsProvider

        profile = self._session.get(CitizenProfile, profile_id)
        primary_address = self._session.scalars(
            select(Address).where(Address.citizen_profile_id == profile_id)
            .order_by(Address.is_primary.desc(), Address.id)
        ).first()
        # Verified document facts count as evidence (Phase 5 integration).
        doc_facts = DocumentFactsProvider(self._session).verified_facts(profile_id)
        ctx = ContextBuilder().build(
            citizen_profile=profile, primary_address=primary_address,
            evaluation_date=date.today(), scheme_version_id=version.id, extra_facts=doc_facts,
        )
        from app.modules.eligibility.repository import EligibilityRepository

        rows = EligibilityRepository(self._session).load_rules(version.id)
        result = engine_evaluate(rule_cache.get_or_compile(version.id, rows), ctx)

        # Persist an eligibility_checks row so the application references it.
        check = EligibilityCheck(
            citizen_profile_id=profile_id, profile_version_no=profile.current_version_no,
            scheme_version_id=version.id, result=result.decision.value,
            rule_breakdown={
                "rules": [
                    {"rule_code": r.rule_code, "field_key": r.field_key, "operator": r.operator,
                     "value": r.value, "citizen_value": r.citizen_value, "outcome": r.outcome,
                     "mandatory": r.mandatory, "explanation": r.explanation}
                    for r in result.rule_breakdown
                ],
                "matched_rules": result.matched_rules, "failed_rules": result.failed_rules,
                "missing_information": result.missing_information, "conflicts": result.conflicts,
            },
            engine_version=result.engine_version, idempotency_key=f"app-{uuid.uuid4().hex}",
        )
        self._session.add(check)
        self._session.flush()

        snapshot = {
            "decision": result.decision.value,
            "engine_version": result.engine_version,
            "scheme_version_id": str(version.id),
            "rule_results": check.rule_breakdown["rules"],
            "evaluated_facts": {k: _jsonable(v.value) for k, v in ctx.facts.items() if v.known},
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        return snapshot, check.id

    def _attach_documents(self, app: Application, profile_id: uuid.UUID, document_ids: list) -> None:
        from app.models.application import ApplicationDocument
        from app.models.document import Document

        for doc_id in document_ids:
            doc = self._session.get(Document, doc_id)
            if doc is None or doc.citizen_profile_id != profile_id or doc.deleted_at is not None:
                # Cannot attach another citizen's / missing document.
                raise ValidationError("Invalid document reference.")
            self._session.add(ApplicationDocument(
                application_id=app.id, document_id=doc.id, document_type=doc.document_type.value,
            ))
        self._session.flush()

    def _unique_number(self) -> str:
        for _ in range(5):
            number = generate_application_number()
            if not self._repo.number_exists(number):
                return number
        raise ConflictError("Could not allocate a unique application number.", code="CONFLICT")

    # ------------------------------------------------------------------ #
    def get(self, *, current: CurrentUser, application_id: uuid.UUID) -> Application:
        return self._load_authorized(current, application_id)

    def list(
        self, *, current: CurrentUser, status: str | None, page: int, page_size: int,
    ) -> tuple[list[Application], int]:
        offset = (page - 1) * page_size
        status_enum = ApplicationStatus(status) if status else None
        if current.role == "citizen":
            profile_id = self._profile_id(current.id)
            if profile_id is None:
                return [], 0
            total = self._repo.count(citizen_profile_id=profile_id, status=status_enum)
            items = self._repo.list(citizen_profile_id=profile_id, status=status_enum,
                                    limit=page_size, offset=offset)
        elif current.role == "agent":
            total = self._repo.count(assigned_case_worker_id=current.id, status=status_enum)
            items = self._repo.list(assigned_case_worker_id=current.id, status=status_enum,
                                    limit=page_size, offset=offset)
        else:  # admin
            total = self._repo.count(status=status_enum)
            items = self._repo.list(status=status_enum, limit=page_size, offset=offset)
        return items, total

    def checklist(self, *, current: CurrentUser, application_id: uuid.UUID) -> Checklist:
        app = self._load_authorized(current, application_id)
        return self._reqs.build_checklist(
            scheme_version_id=app.scheme_version_id, citizen_profile_id=app.citizen_profile_id,
            application_id=app.id,
        )

    # --- state transitions (authorized wrappers) ---
    def submit(self, *, current: CurrentUser, application_id: uuid.UUID, request_id, idempotency_key,
               simulate_provider_failure: bool = False) -> Application:
        app = self._load_authorized(current, application_id)
        # Only the owning citizen (or admin) may submit.
        if current.role == "agent":
            raise PermissionDeniedError("Case workers do not submit applications.")
        checklist = self._reqs.build_checklist(
            scheme_version_id=app.scheme_version_id, citizen_profile_id=app.citizen_profile_id,
            application_id=app.id,
        )
        return ApplicationWorkflow(self._session, self._s).submit(
            application_id, actor_id=current.id, role=current.role, checklist=checklist,
            request_id=request_id, idempotency_key=idempotency_key,
            simulate_provider_failure=simulate_provider_failure,
        )

    def withdraw(self, *, current: CurrentUser, application_id: uuid.UUID, reason) -> Application:
        app = self._load_authorized(current, application_id)
        if current.role == "agent":
            raise PermissionDeniedError("Case workers do not withdraw applications.")
        return ApplicationWorkflow(self._session, self._s).withdraw(
            app, actor_id=current.id, role=current.role, reason=reason)

    def assign(self, *, current: CurrentUser, application_id: uuid.UUID, case_worker_id) -> Application:
        if not can_assign(current.role):
            raise PermissionDeniedError("Only admins manage assignment.")
        app = self._repo.get(application_id)
        if app is None:
            raise NotFoundError("Application not found.")
        if case_worker_id is not None:
            self._assert_case_worker(case_worker_id)
        return ApplicationWorkflow(self._session, self._s).assign(
            app, case_worker_id=case_worker_id, actor_id=current.id)

    def review(self, *, current: CurrentUser, application_id: uuid.UUID, action: ReviewAction,
               reason: str, required_items) -> Application:
        app = self._repo.get(application_id)
        if app is None:
            raise NotFoundError("Application not found.")
        if not can_review_application(role=current.role, current_user_id=current.id,
                                      assigned_case_worker_id=app.assigned_case_worker_id):
            raise PermissionDeniedError("You are not authorized to review this application.")
        if not reason or not reason.strip():
            raise ValidationError("A review reason is required.")
        return ApplicationWorkflow(self._session, self._s).review(
            app, action=action, reason=reason, required_items=required_items,
            actor_id=current.id, role=current.role)

    def resolve_action(self, *, current: CurrentUser, application_id: uuid.UUID, note) -> Application:
        app = self._load_authorized(current, application_id)
        if current.role != "citizen":
            raise PermissionDeniedError("Only the citizen resolves a requested action.")
        return ApplicationWorkflow(self._session, self._s).resolve_action(
            app, actor_id=current.id, role=current.role, note=note)

    def complete(self, *, current: CurrentUser, application_id: uuid.UUID) -> Application:
        app = self._repo.get(application_id)
        if app is None:
            raise NotFoundError("Application not found.")
        if not can_review_application(role=current.role, current_user_id=current.id,
                                      assigned_case_worker_id=app.assigned_case_worker_id):
            raise PermissionDeniedError("Not authorized to complete this application.")
        return ApplicationWorkflow(self._session, self._s).complete(
            app, actor_id=current.id, role=current.role)

    def _assert_case_worker(self, user_id: uuid.UUID) -> None:
        from app.models.user import User

        user = self._session.get(User, user_id)
        if user is None or user.role.value not in ("agent", "admin"):
            raise ValidationError("Assignee must be a case worker (agent) or admin.")


def _jsonable(value):
    from datetime import date as _date
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, _date):
        return value.isoformat()
    return value
