"""Eligibility models — matches data-dictionary.md `eligibility_rules` +
`eligibility_checks`.

Rule storage model (per data-dictionary note: the table is a normalized
encoding of the DSL AST from rule-dsl.md):
- Each `eligibility_rules` row is ONE leaf condition (field_key/operator/value).
- `group_id` names the group a condition belongs to; `group_operator`
  (AND/OR) is carried on each member row of that group (uniform per group,
  validated by the validator). A null group_id means the condition is a
  direct child of the version's implicit root AND-group.
- The compiler reconstructs the tree from these rows.

DOCUMENTED EXTENSIONS beyond the flat data-dictionary columns (required by
rule-dsl.md, recorded in the migration docstring):
- `rule_code` (stable per-rule identifier, e.g. "AGE_MINIMUM"),
- `mandatory` (rule-dsl.md; drives eligible vs likely_eligible),
- `group_operator`, `parent_group_id` (to encode nested AND/OR up to depth 4),
- `source_citation` (rule-dsl.md; provenance for evidence),
- `sort_order` (deterministic evaluation/rendering order).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.scheme import SchemeVersion


class EligibilityRule(Base):
    __tablename__ = "eligibility_rules"
    __table_args__ = (
        # rule_code is unique within a scheme_version.
        UniqueConstraint("scheme_version_id", "rule_code", name="uq_rule_code_per_version"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    scheme_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    field_key: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[object | None] = mapped_column(JSONB, nullable=True)  # operand(s)

    mandatory: Mapped[bool] = mapped_column(nullable=False, default=True)
    group_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    group_operator: Mapped[str | None] = mapped_column(String(3), nullable=True)  # AND | OR
    parent_group_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_citation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    scheme_version: Mapped["SchemeVersion"] = relationship(back_populates="rules")


class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"
    __table_args__ = (
        # Idempotency + cache: one row per (profile, profile_version, version,
        # engine_version, idempotency_key). NULL idempotency keys don't collide
        # (Postgres treats NULLs as distinct in a unique index).
        UniqueConstraint(
            "citizen_profile_id",
            "profile_version_no",
            "scheme_version_id",
            "engine_version",
            "idempotency_key",
            name="uq_eligibility_idempotent",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    citizen_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # snapshot reference (denormalized, not FK) per data-dictionary.
    profile_version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    scheme_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    # Immutable full breakdown: per-rule outcome + explanation + citation,
    # plus missing_information, conflicts, and evidence (DOCUMENTED EXTENSION
    # fields nested inside the existing rule_breakdown JSONB column).
    rule_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Extension: engine version for reproducibility/versioning (prompt §22).
    engine_version: Mapped[str] = mapped_column(String(16), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
