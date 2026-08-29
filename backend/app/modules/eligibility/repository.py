"""Eligibility persistence layer.

One controlled context load (profile + primary address) plus the version's
rules — no per-rule DB queries (prompt §30). Persists eligibility_checks and
supports idempotent lookup (prompt §18).
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.citizen_profile import CitizenProfile
from app.models.eligibility import EligibilityCheck, EligibilityRule
from app.models.scheme import SchemeVersion


class EligibilityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_profile_by_user_id(self, user_id: uuid.UUID) -> CitizenProfile | None:
        return self._session.scalar(
            select(CitizenProfile).where(CitizenProfile.user_id == user_id)
        )

    def get_profile(self, profile_id: uuid.UUID) -> CitizenProfile | None:
        return self._session.get(CitizenProfile, profile_id)

    def primary_address(self, profile_id: uuid.UUID) -> Address | None:
        stmt = (
            select(Address)
            .where(Address.citizen_profile_id == profile_id)
            .order_by(Address.is_primary.desc(), Address.id)
        )
        return self._session.scalars(stmt).first()

    def get_version(self, version_id: uuid.UUID) -> SchemeVersion | None:
        return self._session.get(SchemeVersion, version_id)

    def load_rules(self, version_id: uuid.UUID) -> list[EligibilityRule]:
        stmt = (
            select(EligibilityRule)
            .where(EligibilityRule.scheme_version_id == version_id)
            .order_by(EligibilityRule.sort_order, EligibilityRule.id)
        )
        return list(self._session.scalars(stmt))

    def find_idempotent(
        self,
        *,
        profile_id: uuid.UUID,
        profile_version_no: int,
        scheme_version_id: uuid.UUID,
        engine_version: str,
        idempotency_key: str | None,
    ) -> EligibilityCheck | None:
        stmt = select(EligibilityCheck).where(
            EligibilityCheck.citizen_profile_id == profile_id,
            EligibilityCheck.profile_version_no == profile_version_no,
            EligibilityCheck.scheme_version_id == scheme_version_id,
            EligibilityCheck.engine_version == engine_version,
        )
        if idempotency_key is None:
            stmt = stmt.where(EligibilityCheck.idempotency_key.is_(None))
        else:
            stmt = stmt.where(EligibilityCheck.idempotency_key == idempotency_key)
        return self._session.scalars(stmt.order_by(EligibilityCheck.computed_at.desc())).first()

    def add_check(self, check: EligibilityCheck) -> EligibilityCheck:
        self._session.add(check)
        self._session.flush()
        return check
