"""Schemes persistence layer (schemes, scheme_versions, eligibility_rules).

Queries are paginated/filtered in SQL (LIMIT/OFFSET + WHERE) — never load the
whole table into memory (prompt §4, §30). No policy decisions here.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.eligibility import EligibilityRule
from app.models.enums import SchemeScope, SchemeVersionStatus
from app.models.scheme import Scheme, SchemeVersion


class SchemesRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------ schemes ------------------------------ #
    def add_scheme(self, scheme: Scheme) -> Scheme:
        self._session.add(scheme)
        self._session.flush()
        return scheme

    def get_scheme(self, scheme_id: uuid.UUID) -> Scheme | None:
        return self._session.get(Scheme, scheme_id)

    def get_scheme_by_code(self, code: str) -> Scheme | None:
        return self._session.scalar(select(Scheme).where(Scheme.code == code))

    def _scheme_filter(
        self,
        stmt: Select,
        *,
        q: str | None,
        category: str | None,
        scope: SchemeScope | None,
    ) -> Select:
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(Scheme.canonical_name.ilike(like), Scheme.category.ilike(like))
            )
        if category:
            stmt = stmt.where(Scheme.category == category)
        if scope:
            stmt = stmt.where(Scheme.scope == scope)
        return stmt

    def count_schemes(
        self, *, q: str | None, category: str | None, scope: SchemeScope | None
    ) -> int:
        stmt = self._scheme_filter(
            select(func.count()).select_from(Scheme), q=q, category=category, scope=scope
        )
        return int(self._session.scalar(stmt) or 0)

    def list_schemes(
        self,
        *,
        q: str | None,
        category: str | None,
        scope: SchemeScope | None,
        limit: int,
        offset: int,
    ) -> list[Scheme]:
        stmt = self._scheme_filter(
            select(Scheme), q=q, category=category, scope=scope
        ).order_by(Scheme.canonical_name, Scheme.id).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    # -------------------------- scheme_versions -------------------------- #
    def add_version(self, version: SchemeVersion) -> SchemeVersion:
        self._session.add(version)
        self._session.flush()
        return version

    def get_version(self, version_id: uuid.UUID) -> SchemeVersion | None:
        return self._session.get(SchemeVersion, version_id)

    def list_versions(self, scheme_id: uuid.UUID) -> list[SchemeVersion]:
        stmt = (
            select(SchemeVersion)
            .where(SchemeVersion.scheme_id == scheme_id)
            .order_by(SchemeVersion.version_no)
        )
        return list(self._session.scalars(stmt))

    def max_version_no(self, scheme_id: uuid.UUID) -> int:
        stmt = select(func.max(SchemeVersion.version_no)).where(
            SchemeVersion.scheme_id == scheme_id
        )
        return int(self._session.scalar(stmt) or 0)

    def current_published_version(self, scheme_id: uuid.UUID) -> SchemeVersion | None:
        """The currently-effective published version (open-ended effective_to)."""
        stmt = (
            select(SchemeVersion)
            .where(
                SchemeVersion.scheme_id == scheme_id,
                SchemeVersion.status == SchemeVersionStatus.PUBLISHED,
                SchemeVersion.effective_to.is_(None),
            )
            .order_by(SchemeVersion.version_no.desc())
        )
        return self._session.scalars(stmt).first()

    def published_versions_overlapping(
        self, scheme_id: uuid.UUID, eff_from: date, eff_to: date | None, exclude_id: uuid.UUID | None
    ) -> list[SchemeVersion]:
        """Published versions whose effective range overlaps [eff_from, eff_to)."""
        # Overlap: existing.from <= new.to (or new open) AND existing.to (or open) >= new.from
        new_to = eff_to
        stmt = select(SchemeVersion).where(
            SchemeVersion.scheme_id == scheme_id,
            SchemeVersion.status == SchemeVersionStatus.PUBLISHED,
        )
        if exclude_id is not None:
            stmt = stmt.where(SchemeVersion.id != exclude_id)
        candidates = list(self._session.scalars(stmt))
        overlaps = []
        for v in candidates:
            starts_before_new_ends = new_to is None or v.effective_from <= new_to
            ends_after_new_starts = v.effective_to is None or v.effective_to >= eff_from
            if starts_before_new_ends and ends_after_new_starts:
                overlaps.append(v)
        return overlaps

    # -------------------------- eligibility_rules ------------------------ #
    def add_rules(self, rules: list[EligibilityRule]) -> None:
        self._session.add_all(rules)
        self._session.flush()

    def delete_rules_for_version(self, version_id: uuid.UUID) -> None:
        for r in self.list_rules(version_id):
            self._session.delete(r)
        self._session.flush()

    def list_rules(self, version_id: uuid.UUID) -> list[EligibilityRule]:
        stmt = (
            select(EligibilityRule)
            .where(EligibilityRule.scheme_version_id == version_id)
            .order_by(EligibilityRule.sort_order, EligibilityRule.id)
        )
        return list(self._session.scalars(stmt))
