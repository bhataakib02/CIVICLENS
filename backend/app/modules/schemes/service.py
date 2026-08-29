"""Schemes application service.

Owns: scheme CRUD, scheme versioning, version lifecycle transitions, and rule
authoring. Enforces (server-side, not just UI — prompt §6):
- Legal lifecycle transitions only (draft->in_review->published->superseded;
  no superseded->published).
- At most one currently-effective published version per scheme, with no
  overlapping effective date ranges among published versions.
- Four-eyes on publish (FR-ADMIN-2): publisher must differ from author.
- Rules validated through the DSL validator before persistence; rules can
  only be authored on a draft/in_review version (published versions are
  immutable — ADR-004).

Every lifecycle operation writes an audit event (prompt §25). Owns the
transaction (commit/rollback).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.eligibility import EligibilityRule
from app.models.enums import SchemeScope, SchemeVersionStatus
from app.models.scheme import Scheme, SchemeVersion
from app.modules.audit.service import AuditAction, AuditService
from app.modules.eligibility.compiler import flatten_rule_set, rule_cache
from app.modules.eligibility.validator import validate_rule_set
from app.modules.schemes.repository import SchemesRepository

logger = get_logger("civiclens.schemes")

# Legal status transitions (prompt §6, authoritative lifecycle).
_LEGAL_TRANSITIONS: dict[SchemeVersionStatus, set[SchemeVersionStatus]] = {
    SchemeVersionStatus.DRAFT: {SchemeVersionStatus.IN_REVIEW, SchemeVersionStatus.ARCHIVED},
    SchemeVersionStatus.IN_REVIEW: {
        SchemeVersionStatus.PUBLISHED,
        SchemeVersionStatus.DRAFT,
        SchemeVersionStatus.ARCHIVED,
    },
    SchemeVersionStatus.PUBLISHED: {SchemeVersionStatus.SUPERSEDED, SchemeVersionStatus.ARCHIVED},
    SchemeVersionStatus.SUPERSEDED: set(),
    SchemeVersionStatus.ARCHIVED: set(),
}


class SchemesService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = SchemesRepository(session)
        self._audit = AuditService(session)

    # ------------------------------------------------------------------ #
    # Schemes
    # ------------------------------------------------------------------ #
    def create_scheme(
        self,
        *,
        canonical_name: str,
        category: str,
        scope: SchemeScope,
        administering_dept: str | None,
        code: str | None,
        actor_user_id: uuid.UUID,
        ip: str | None = None,
    ) -> Scheme:
        if code and self._repo.get_scheme_by_code(code) is not None:
            raise ConflictError("A scheme with this code already exists.", code="SCHEME_CODE_EXISTS")

        scheme = Scheme(
            canonical_name=canonical_name.strip(),
            category=category.strip(),
            scope=scope,
            administering_dept=(administering_dept or None),
            code=(code or None),
        )
        try:
            self._repo.add_scheme(scheme)
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("Scheme could not be created (duplicate code).", code="SCHEME_CODE_EXISTS") from exc

        self._audit.record(
            action=AuditAction.SCHEME_CREATE,
            entity_type="scheme",
            entity_id=scheme.id,
            actor_user_id=actor_user_id,
            diff={"canonical_name": scheme.canonical_name, "category": scheme.category},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(scheme)
        return scheme

    def get_scheme(self, scheme_id: uuid.UUID) -> Scheme:
        scheme = self._repo.get_scheme(scheme_id)
        if scheme is None:
            raise NotFoundError("Scheme not found.")
        return scheme

    def list_schemes(
        self,
        *,
        q: str | None,
        category: str | None,
        scope: SchemeScope | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Scheme], int]:
        offset = (page - 1) * page_size
        total = self._repo.count_schemes(q=q, category=category, scope=scope)
        items = self._repo.list_schemes(
            q=q, category=category, scope=scope, limit=page_size, offset=offset
        )
        return items, total

    def current_published_version(self, scheme_id: uuid.UUID) -> SchemeVersion | None:
        return self._repo.current_published_version(scheme_id)

    # ------------------------------------------------------------------ #
    # Versions
    # ------------------------------------------------------------------ #
    def create_version(
        self,
        *,
        scheme_id: uuid.UUID,
        benefits_summary: str,
        effective_from: date,
        effective_to: date | None,
        knowledge_source_id: uuid.UUID | None,
        actor_user_id: uuid.UUID,
        ip: str | None = None,
    ) -> SchemeVersion:
        scheme = self.get_scheme(scheme_id)
        if effective_to is not None and effective_to < effective_from:
            raise ValidationError(
                "effective_to must not be before effective_from.",
                field_errors=[{"field": "effective_to", "message": "Must be on/after effective_from."}],
            )
        version_no = self._repo.max_version_no(scheme.id) + 1
        version = SchemeVersion(
            scheme_id=scheme.id,
            version_no=version_no,
            status=SchemeVersionStatus.DRAFT,
            benefits_summary=benefits_summary.strip(),
            effective_from=effective_from,
            effective_to=effective_to,
            knowledge_source_id=knowledge_source_id,
            created_by=actor_user_id,
        )
        self._repo.add_version(version)
        self._audit.record(
            action=AuditAction.SCHEME_VERSION_CREATE,
            entity_type="scheme_version",
            entity_id=version.id,
            actor_user_id=actor_user_id,
            diff={"scheme_id": str(scheme.id), "version_no": version_no},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(version)
        return version

    def list_versions(self, scheme_id: uuid.UUID) -> list[SchemeVersion]:
        self.get_scheme(scheme_id)  # 404 if missing
        return self._repo.list_versions(scheme_id)

    def get_version(self, version_id: uuid.UUID) -> SchemeVersion:
        version = self._repo.get_version(version_id)
        if version is None:
            raise NotFoundError("Scheme version not found.")
        return version

    def _transition(
        self, version: SchemeVersion, target: SchemeVersionStatus
    ) -> None:
        if target not in _LEGAL_TRANSITIONS[version.status]:
            raise ConflictError(
                f"Illegal version transition {version.status.value} -> {target.value}.",
                code="ILLEGAL_VERSION_TRANSITION",
            )

    def publish_version(
        self, *, version_id: uuid.UUID, actor_user_id: uuid.UUID, ip: str | None = None
    ) -> SchemeVersion:
        version = self.get_version(version_id)

        # Allow publishing directly from draft or in_review.
        if version.status not in (SchemeVersionStatus.DRAFT, SchemeVersionStatus.IN_REVIEW):
            raise ConflictError(
                f"Only draft/in_review versions can be published (was {version.status.value}).",
                code="ILLEGAL_VERSION_TRANSITION",
            )

        # Four-eyes: publisher must differ from author (FR-ADMIN-2).
        if version.created_by is not None and version.created_by == actor_user_id:
            raise ConflictError(
                "Publisher must differ from the version author (four-eyes rule).",
                code="FOUR_EYES_REQUIRED",
            )

        # A version must have at least one rule before it can go live.
        if not self._repo.list_rules(version.id):
            raise ConflictError(
                "Cannot publish a version with no eligibility rules.",
                code="VERSION_HAS_NO_RULES",
            )

        # Effective-range overlap guard against other published versions.
        overlaps = self._repo.published_versions_overlapping(
            version.scheme_id, version.effective_from, version.effective_to, exclude_id=version.id
        )
        if overlaps:
            raise ConflictError(
                "Effective period overlaps an already-published version.",
                code="EFFECTIVE_PERIOD_OVERLAP",
            )

        version.status = SchemeVersionStatus.PUBLISHED
        version.published_at = datetime.now(timezone.utc)
        version.published_by = actor_user_id
        rule_cache.invalidate(version.id)

        self._audit.record(
            action=AuditAction.SCHEME_VERSION_PUBLISH,
            entity_type="scheme_version",
            entity_id=version.id,
            actor_user_id=actor_user_id,
            diff={"version_no": version.version_no},
            ip=ip,
        )
        logger.info(
            "scheme_version_activated",
            extra={"scheme_version_id": str(version.id), "version_no": version.version_no},
        )
        try:
            self._session.commit()
        except IntegrityError as exc:
            # Partial unique index caught a concurrent open-ended publish.
            self._session.rollback()
            raise ConflictError(
                "Another currently-effective version already exists.",
                code="EFFECTIVE_PERIOD_OVERLAP",
            ) from exc
        self._session.refresh(version)
        return version

    def supersede_version(
        self,
        *,
        version_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        effective_to: date | None = None,
        ip: str | None = None,
    ) -> SchemeVersion:
        version = self.get_version(version_id)
        self._transition(version, SchemeVersionStatus.SUPERSEDED)
        version.status = SchemeVersionStatus.SUPERSEDED
        if version.effective_to is None:
            version.effective_to = effective_to or date.today()
        rule_cache.invalidate(version.id)
        self._audit.record(
            action=AuditAction.SCHEME_VERSION_SUPERSEDE,
            entity_type="scheme_version",
            entity_id=version.id,
            actor_user_id=actor_user_id,
            diff={"version_no": version.version_no},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(version)
        return version

    # ------------------------------------------------------------------ #
    # Rules
    # ------------------------------------------------------------------ #
    def list_rules(self, version_id: uuid.UUID) -> list[EligibilityRule]:
        self.get_version(version_id)
        return self._repo.list_rules(version_id)

    def set_rules(
        self,
        *,
        version_id: uuid.UUID,
        rules: list[dict],
        actor_user_id: uuid.UUID,
        ip: str | None = None,
    ) -> list[EligibilityRule]:
        version = self.get_version(version_id)
        if version.status not in (SchemeVersionStatus.DRAFT, SchemeVersionStatus.IN_REVIEW):
            raise ConflictError(
                "Rules can only be edited on a draft/in_review version (published versions are immutable).",
                code="VERSION_IMMUTABLE",
            )

        try:
            root = validate_rule_set(rules)
        except ValidationError:
            self._audit.record(
                action=AuditAction.RULE_VALIDATION_FAILED,
                entity_type="scheme_version",
                entity_id=version.id,
                actor_user_id=actor_user_id,
                ip=ip,
            )
            self._session.commit()
            logger.info("rule_validation_failed", extra={"scheme_version_id": str(version.id)})
            raise

        flat = flatten_rule_set(root)
        self._repo.delete_rules_for_version(version.id)
        rows = [
            EligibilityRule(
                scheme_version_id=version.id,
                rule_code=r["rule_code"],
                field_key=r["field_key"],
                operator=r["operator"],
                value=r["value"],
                mandatory=r["mandatory"],
                group_id=r["group_id"],
                group_operator=r["group_operator"],
                parent_group_id=r["parent_group_id"],
                sort_order=r["sort_order"],
                explanation_text=r["explanation_text"],
                source_citation=r["source_citation"],
            )
            for r in flat
        ]
        self._repo.add_rules(rows)
        rule_cache.invalidate(version.id)
        self._audit.record(
            action=AuditAction.SCHEME_VERSION_RULES_SET,
            entity_type="scheme_version",
            entity_id=version.id,
            actor_user_id=actor_user_id,
            diff={"rule_count": len(rows)},
            ip=ip,
        )
        self._session.commit()
        return self._repo.list_rules(version.id)

    @staticmethod
    def validate_rules(rules: list[dict]) -> int:
        """Validate a rule set without persisting; returns normalized leaf count."""
        root = validate_rule_set(rules)
        from app.modules.eligibility.compiler import flatten_rule_set as _flatten

        return len(_flatten(root))
