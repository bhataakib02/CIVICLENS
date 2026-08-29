"""Schemes + admin scheme/version/rule HTTP routes.

Contract endpoints:
    GET  /schemes                          (browse/search, paginated)
    GET  /schemes/{scheme_id}              (detail, current published version)
    POST /schemes                          (admin — contract extension)
    GET  /schemes/{scheme_id}/versions     (extension)
    POST /schemes/{scheme_id}/versions     (admin)
    POST /admin/scheme-versions/{id}/publish
    POST /admin/scheme-versions/{id}/supersede  (extension)
    GET  /scheme-versions/{id}/rules
    POST /scheme-versions/{id}/rules       (admin)
    POST /admin/rules/validate             (admin)

Routers translate HTTP <-> service commands; business logic is in the service.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.models.enums import SchemeScope
from app.modules.auth.dependencies import CurrentUser
from app.modules.schemes.dependencies import require_reader, require_scheme_admin
from app.modules.schemes.repository import SchemesRepository
from app.modules.schemes.service import SchemesService
from app.schemas.scheme import (
    RuleOut,
    RuleSetInput,
    RuleValidateInput,
    RuleValidateResult,
    SchemeCreate,
    SchemeDetail,
    SchemePage,
    SchemeSummary,
    SchemeVersionInput,
    SchemeVersionOut,
)

schemes_router = APIRouter(tags=["schemes"])
admin_schemes_router = APIRouter(prefix="/admin", tags=["admin"])
scheme_versions_router = APIRouter(tags=["schemes"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _summary(scheme, benefits: str | None) -> SchemeSummary:
    return SchemeSummary(
        id=str(scheme.id),
        canonical_name=scheme.canonical_name,
        category=scheme.category,
        scope=scheme.scope,
        benefits_summary=benefits,
    )


# ------------------------------- Catalog ------------------------------------ #
@schemes_router.get("/schemes", response_model=SchemePage)
def list_schemes(
    request: Request,
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    scope: SchemeScope | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _current: CurrentUser = Depends(require_reader),
    session: Session = Depends(db_session),
) -> SchemePage:
    service = SchemesService(session)
    items, total = service.list_schemes(
        q=q, category=category, scope=scope, page=page, page_size=page_size
    )
    summaries = []
    for scheme in items:
        pub = service.current_published_version(scheme.id)
        summaries.append(_summary(scheme, pub.benefits_summary if pub else None))
    return SchemePage(items=summaries, page=page, page_size=page_size, total=total)


@schemes_router.get("/schemes/{scheme_id}", response_model=SchemeDetail)
def get_scheme(
    scheme_id: uuid.UUID,
    _current: CurrentUser = Depends(require_reader),
    session: Session = Depends(db_session),
) -> SchemeDetail:
    service = SchemesService(session)
    scheme = service.get_scheme(scheme_id)
    pub = service.current_published_version(scheme.id)
    return SchemeDetail(
        id=str(scheme.id),
        canonical_name=scheme.canonical_name,
        category=scheme.category,
        scope=scheme.scope,
        benefits_summary=pub.benefits_summary if pub else None,
        administering_dept=scheme.administering_dept,
        document_requirements=[],
        last_verified_at=None,
        scheme_version_id=str(pub.id) if pub else None,
    )


@schemes_router.post("/schemes", response_model=SchemeSummary, status_code=status.HTTP_201_CREATED)
def create_scheme(
    body: SchemeCreate,
    request: Request,
    current: CurrentUser = Depends(require_scheme_admin),
    session: Session = Depends(db_session),
) -> SchemeSummary:
    scheme = SchemesService(session).create_scheme(
        canonical_name=body.canonical_name,
        category=body.category,
        scope=body.scope,
        administering_dept=body.administering_dept,
        code=body.code,
        actor_user_id=current.id,
        ip=_ip(request),
    )
    return _summary(scheme, None)


# ------------------------------- Versions ----------------------------------- #
@schemes_router.get("/schemes/{scheme_id}/versions", response_model=list[SchemeVersionOut])
def list_versions(
    scheme_id: uuid.UUID,
    _current: CurrentUser = Depends(require_reader),
    session: Session = Depends(db_session),
) -> list[SchemeVersionOut]:
    versions = SchemesService(session).list_versions(scheme_id)
    return [_version_out(v) for v in versions]


@schemes_router.post(
    "/schemes/{scheme_id}/versions",
    response_model=SchemeVersionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_version(
    scheme_id: uuid.UUID,
    body: SchemeVersionInput,
    request: Request,
    current: CurrentUser = Depends(require_scheme_admin),
    session: Session = Depends(db_session),
) -> SchemeVersionOut:
    version = SchemesService(session).create_version(
        scheme_id=scheme_id,
        benefits_summary=body.benefits_summary,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        knowledge_source_id=body.knowledge_source_id,
        actor_user_id=current.id,
        ip=_ip(request),
    )
    return _version_out(version)


@admin_schemes_router.post(
    "/scheme-versions/{scheme_version_id}/publish", response_model=SchemeVersionOut
)
def publish_version(
    scheme_version_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(require_scheme_admin),
    session: Session = Depends(db_session),
) -> SchemeVersionOut:
    version = SchemesService(session).publish_version(
        version_id=scheme_version_id, actor_user_id=current.id, ip=_ip(request)
    )
    return _version_out(version)


@admin_schemes_router.post(
    "/scheme-versions/{scheme_version_id}/supersede", response_model=SchemeVersionOut
)
def supersede_version(
    scheme_version_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(require_scheme_admin),
    session: Session = Depends(db_session),
) -> SchemeVersionOut:
    version = SchemesService(session).supersede_version(
        version_id=scheme_version_id, actor_user_id=current.id, ip=_ip(request)
    )
    return _version_out(version)


# --------------------------------- Rules ------------------------------------ #
@scheme_versions_router.get(
    "/scheme-versions/{scheme_version_id}/rules", response_model=list[RuleOut]
)
def list_rules(
    scheme_version_id: uuid.UUID,
    _current: CurrentUser = Depends(require_reader),
    session: Session = Depends(db_session),
) -> list[RuleOut]:
    rules = SchemesService(session).list_rules(scheme_version_id)
    return [_rule_out(r) for r in rules]


@scheme_versions_router.post(
    "/scheme-versions/{scheme_version_id}/rules",
    response_model=list[RuleOut],
    status_code=status.HTTP_201_CREATED,
)
def set_rules(
    scheme_version_id: uuid.UUID,
    body: RuleSetInput,
    request: Request,
    current: CurrentUser = Depends(require_scheme_admin),
    session: Session = Depends(db_session),
) -> list[RuleOut]:
    rules = SchemesService(session).set_rules(
        version_id=scheme_version_id,
        rules=body.rules,
        actor_user_id=current.id,
        ip=_ip(request),
    )
    return [_rule_out(r) for r in rules]


@admin_schemes_router.post("/rules/validate", response_model=RuleValidateResult)
def validate_rules(
    body: RuleValidateInput,
    _current: CurrentUser = Depends(require_scheme_admin),
) -> RuleValidateResult:
    count = SchemesService.validate_rules(body.rules)
    return RuleValidateResult(
        valid=True, normalized_rule_count=count, message="Rule set is valid."
    )


# --------------------------------- mappers ---------------------------------- #
def _version_out(v) -> SchemeVersionOut:
    return SchemeVersionOut(
        id=str(v.id),
        scheme_id=str(v.scheme_id),
        version_no=v.version_no,
        status=v.status,
        benefits_summary=v.benefits_summary,
        effective_from=v.effective_from,
        effective_to=v.effective_to,
        published_at=v.published_at,
    )


def _rule_out(r) -> RuleOut:
    return RuleOut(
        id=str(r.id),
        rule_code=r.rule_code,
        field_key=r.field_key,
        operator=r.operator,
        value=r.value,
        mandatory=r.mandatory,
        group_id=r.group_id,
        group_operator=r.group_operator,
        explanation_text=r.explanation_text,
        source_citation=r.source_citation,
    )
