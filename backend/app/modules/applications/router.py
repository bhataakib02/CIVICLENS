"""Application HTTP routes.

Contract + documented extensions:
    POST   /applications                       create draft (eligibility-gated)
    GET    /applications                       list (role-scoped, paginated)
    GET    /applications/{id}                   detail (role-scoped view)
    GET    /applications/{id}/checklist         document readiness (extension)
    POST   /applications/{id}/submit            transactional + idempotent
    POST   /applications/{id}/withdraw
    POST   /applications/{id}/assign            (admin — extension)
    POST   /applications/{id}/review            (case worker/admin — extension)
    POST   /applications/{id}/resolve-action    (citizen — extension)
    POST   /applications/{id}/complete          (case worker/admin — extension)

Detail assembly applies response-level authorization: reviewer-only info is
included only for case worker/admin viewers (prompt §29, §54).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.core.middleware import get_request_id
from app.db.session import db_session
from app.models.application import Application
from app.modules.applications.dependencies import require_user
from app.modules.applications.repository import ApplicationsRepository
from app.modules.applications.requirements import RequirementsService
from app.modules.applications.schemas import (
    Application as ApplicationSchema,
    ApplicationCreateInput,
    ApplicationDetail,
    ApplicationPage,
    AssignInput,
    ChecklistItemOut,
    ChecklistOut,
    EligibilitySummary,
    ResolveActionInput,
    ReviewInfo,
    ReviewInput,
    StatusHistoryItem,
    SubmissionInfo,
    SubmitInput,
    WithdrawInput,
)
from app.modules.applications.service import ApplicationsService
from app.modules.applications.state_machine import all_transitions
from app.modules.auth.dependencies import CurrentUser
from app.modules.notifications.service import dispatch_outbox_now

applications_router = APIRouter(prefix="/applications", tags=["applications"])

_REVIEWER_ROLES = {"agent", "admin"}


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _scheme_id_of(session: Session, app: Application) -> str:
    from app.models.scheme import SchemeVersion

    v = session.get(SchemeVersion, app.scheme_version_id)
    return str(v.scheme_id) if v else ""


from app.modules.applications.state_machine import all_transitions, to_public_status


def _to_summary(session: Session, app: Application) -> ApplicationSchema:
    return ApplicationSchema(
        id=str(app.id), application_number=app.application_number,
        scheme_id=_scheme_id_of(session, app), scheme_version_id=str(app.scheme_version_id),
        status=to_public_status(app.status), created_at=app.created_at, submitted_at=app.submitted_at,
    )


@applications_router.post("", response_model=ApplicationSchema, status_code=status.HTTP_201_CREATED)
def create_application(
    body: ApplicationCreateInput,
    request: Request,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationSchema:
    app = ApplicationsService(session).create(
        current=current, scheme_id=body.scheme_id, scheme_version_id=body.scheme_version_id,
        scheme_specific_answers=body.scheme_specific_answers, document_ids=body.document_ids,
        ip=_ip(request),
    )
    return _to_summary(session, app)


@applications_router.get("", response_model=ApplicationPage)
@applications_router.get("/", response_model=ApplicationPage, include_in_schema=False)
def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationPage:
    items, total = ApplicationsService(session).list(
        current=current, status=status_filter, page=page, page_size=page_size
    )
    return ApplicationPage(
        items=[_to_summary(session, a) for a in items], page=page, page_size=page_size, total=total
    )


@applications_router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(
    application_id: uuid.UUID,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationDetail:
    service = ApplicationsService(session)
    app = service.get(current=current, application_id=application_id)
    return _assemble_detail(session, app, current)


@applications_router.get("/{application_id}/checklist", response_model=ChecklistOut)
def get_checklist(
    application_id: uuid.UUID,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ChecklistOut:
    checklist = ApplicationsService(session).checklist(current=current, application_id=application_id)
    return _checklist_out(checklist)


@applications_router.post("/{application_id}/submit", response_model=ApplicationDetail)
def submit_application(
    application_id: uuid.UUID,
    request: Request,
    body: SubmitInput | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationDetail:
    service = ApplicationsService(session)
    app = service.submit(
        current=current, application_id=application_id, request_id=get_request_id(),
        idempotency_key=idempotency_key,
        simulate_provider_failure=bool(body and body.simulate_provider_failure),
    )
    dispatch_outbox_now()  # deliver queued notifications (worker seam)
    return _assemble_detail(session, app, current)


@applications_router.post("/{application_id}/withdraw", response_model=ApplicationDetail)
def withdraw_application(
    application_id: uuid.UUID,
    body: WithdrawInput | None = None,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationDetail:
    app = ApplicationsService(session).withdraw(
        current=current, application_id=application_id, reason=(body.reason if body else None)
    )
    dispatch_outbox_now()
    return _assemble_detail(session, app, current)


@applications_router.post("/{application_id}/assign", response_model=ApplicationDetail)
def assign_application(
    application_id: uuid.UUID,
    body: AssignInput,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationDetail:
    app = ApplicationsService(session).assign(
        current=current, application_id=application_id, case_worker_id=body.case_worker_id
    )
    return _assemble_detail(session, app, current)


@applications_router.post("/{application_id}/review", response_model=ApplicationDetail)
def review_application(
    application_id: uuid.UUID,
    body: ReviewInput,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationDetail:
    app = ApplicationsService(session).review(
        current=current, application_id=application_id, action=body.action,
        reason=body.reason, required_items=body.required_items,
    )
    dispatch_outbox_now()
    return _assemble_detail(session, app, current)


@applications_router.post("/{application_id}/resolve-action", response_model=ApplicationDetail)
def resolve_action(
    application_id: uuid.UUID,
    body: ResolveActionInput | None = None,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationDetail:
    app = ApplicationsService(session).resolve_action(
        current=current, application_id=application_id, note=(body.note if body else None)
    )
    dispatch_outbox_now()
    return _assemble_detail(session, app, current)


@applications_router.post("/{application_id}/complete", response_model=ApplicationDetail)
def complete_application(
    application_id: uuid.UUID,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
) -> ApplicationDetail:
    app = ApplicationsService(session).complete(current=current, application_id=application_id)
    dispatch_outbox_now()
    return _assemble_detail(session, app, current)


from fastapi.responses import Response


@applications_router.get("/{application_id}/export", response_class=Response)
def export_application(
    application_id: uuid.UUID,
    current: CurrentUser = Depends(require_user),
    session: Session = Depends(db_session),
):
    from app.modules.applications.pdf_package import generate_application_pdf

    # Verify authorization
    ApplicationsService(session).get(current=current, application_id=application_id)
    pdf_bytes = generate_application_pdf(session, application_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=application_{application_id}.pdf"},
    )


# --------------------------------- assembly --------------------------------- #
def _checklist_out(checklist) -> ChecklistOut:
    return ChecklistOut(
        items=[
            ChecklistItemOut(document_type=i.document_type, required=i.required,
                             status=i.status.value, document_id=str(i.document_id) if i.document_id else None)
            for i in checklist.items
        ],
        all_required_satisfied=checklist.all_required_satisfied,
    )


def _assemble_detail(session: Session, app: Application, current: CurrentUser) -> ApplicationDetail:
    repo = ApplicationsRepository(session)
    full = repo.get_with_related(app.id) or app
    snapshot = full.eligibility_snapshot or {}
    checklist = RequirementsService(session).build_checklist(
        scheme_version_id=full.scheme_version_id, citizen_profile_id=full.citizen_profile_id,
        application_id=full.id,
    )
    history = sorted(full.history, key=lambda h: h.created_at)
    submissions = [s for s in full.submissions if s.status.value != "failed"]
    submission = submissions[0] if submissions else None

    is_reviewer = current.role in _REVIEWER_ROLES
    detail = ApplicationDetail(
        id=str(full.id), application_number=full.application_number,
        scheme_id=_scheme_id_of(session, full), scheme_version_id=str(full.scheme_version_id),
        status=full.status.value, created_at=full.created_at, submitted_at=full.submitted_at,
        eligibility=EligibilitySummary(
            decision=snapshot.get("decision"), engine_version=snapshot.get("engine_version"),
            scheme_version_id=snapshot.get("scheme_version_id"), evaluated_at=snapshot.get("evaluated_at"),
        ),
        checklist=_checklist_out(checklist),
        status_history=[
            StatusHistoryItem(from_status=h.from_status, to_status=h.to_status, note=h.note,
                              created_at=h.created_at)
            for h in history
        ],
        attached_document_ids=[str(d.document_id) for d in full.documents],
        submission=SubmissionInfo(
            status=submission.status.value, submission_method=submission.submission_method.value,
            external_reference=submission.external_reference, submitted_at=submission.submitted_at,
            provider_environment=(submission.response_metadata or {}).get("environment"),
        ) if submission else None,
        next_actions=[t.value for t in all_transitions().get(full.status, set())],
        # Reviewer-only info withheld from citizens.
        review=ReviewInfo(
            assigned_case_worker_id=str(full.assigned_case_worker_id) if full.assigned_case_worker_id else None,
            open_actions=[{"reason": a.reason, "required_items": a.required_items}
                          for a in full.actions if a.status.value == "open"],
        ) if is_reviewer else None,
    )
    return detail
