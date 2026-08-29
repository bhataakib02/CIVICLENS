"""Typed eligibility evaluation context (prompt §11).

The evaluator operates ONLY against this context. The context is built once
(one controlled load) from the citizen's profile snapshot + primary address +
any explicit facts supplied on the request + (future) document extractions.
No rule expression can query PostgreSQL — it can only read resolved facts
from here.

Fact resolution and conflict detection (prompt §12, §13):
- Each canonical field_key resolves to a FactValue carrying the value, whether
  it is KNOWN, and the source(s) it came from.
- When two authoritative sources disagree for the same field, a Conflict is
  recorded and the field is treated as UNKNOWN by the evaluator (the engine
  never silently picks a side — eligibility-engine.md §5).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from app.modules.eligibility.rule_types import CANONICAL_ALIAS, FIELD_REGISTRY


@dataclass(frozen=True)
class FactValue:
    known: bool
    value: Any = None
    sources: tuple[str, ...] = ()
    conflicted: bool = False


@dataclass(frozen=True)
class Conflict:
    field_key: str
    values: tuple[Any, ...]
    sources: tuple[str, ...]


@dataclass
class EligibilityContext:
    citizen_profile_id: uuid.UUID
    profile_version_no: int
    scheme_version_id: uuid.UUID
    evaluation_date: date
    facts: dict[str, FactValue]
    conflicts: list[Conflict] = field(default_factory=list)

    def get(self, field_key: str) -> FactValue:
        canonical = CANONICAL_ALIAS.get(field_key, field_key)
        return self.facts.get(canonical, FactValue(known=False))


def _age_from_dob(dob: date, as_of: date) -> int:
    return as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))


def _norm(value: Any) -> Any:
    """Normalize values for equality/conflict comparison (Decimal->float, etc.)."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


class ContextBuilder:
    """Builds an EligibilityContext from profile/address rows + explicit facts.

    Explicit request facts (prompt §16 `facts`) are treated as an additional
    source that can CONFIRM a missing profile field or CONFLICT with a present
    one. This is where document-vs-profile conflicts will also flow in later.
    """

    def build(
        self,
        *,
        citizen_profile,
        primary_address,
        evaluation_date: date,
        scheme_version_id: uuid.UUID,
        extra_facts: dict[str, Any] | None = None,
    ) -> EligibilityContext:
        raw_sources: dict[str, list[tuple[str, Any]]] = {}

        def add(key: str, value: Any, source: str) -> None:
            if value is None:
                return
            raw_sources.setdefault(key, []).append((source, value))

        # Profile facts.
        add("date_of_birth", citizen_profile.date_of_birth, "profile")
        add("declared_annual_income", citizen_profile.declared_annual_income, "profile")
        add("gender", citizen_profile.gender, "profile")
        add("category", citizen_profile.category, "profile")
        add("occupation", citizen_profile.occupation, "profile")
        add("disability_status", citizen_profile.disability_status, "profile")
        add("family_size", citizen_profile.family_size, "profile")

        # Address facts (from the primary address, if any).
        if primary_address is not None:
            add("state", primary_address.state, "profile")
            add("district", primary_address.district, "profile")
            add("pincode", primary_address.pincode, "profile")

        # Derived age.
        if citizen_profile.date_of_birth is not None:
            add("age", _age_from_dob(citizen_profile.date_of_birth, evaluation_date), "derived")

        # Explicit request facts (canonicalized). Unknown keys are ignored here;
        # rules referencing unknown fields are rejected at validation time.
        for raw_key, value in (extra_facts or {}).items():
            canonical = _canonical(raw_key)
            if canonical is None:
                continue
            if canonical == "age" and value is not None:
                add("age", value, "request")
            else:
                add(canonical, value, "request")

        facts: dict[str, FactValue] = {}
        conflicts: list[Conflict] = []
        for key, entries in raw_sources.items():
            distinct = {}
            for source, value in entries:
                distinct.setdefault(_norm(value), []).append(source)
            if len(distinct) == 1:
                (norm_value, srcs), = distinct.items()
                # keep the original (un-normalized) first value for evaluation
                original = entries[0][1]
                facts[key] = FactValue(known=True, value=original, sources=tuple(dict.fromkeys(srcs)))
            else:
                # Conflict: authoritative sources disagree.
                all_sources = tuple(dict.fromkeys(s for s, _ in entries))
                values = tuple(v for v in distinct.keys())
                conflicts.append(Conflict(field_key=key, values=values, sources=all_sources))
                facts[key] = FactValue(known=False, conflicted=True, sources=all_sources)

        return EligibilityContext(
            citizen_profile_id=citizen_profile.id,
            profile_version_no=citizen_profile.current_version_no,
            scheme_version_id=scheme_version_id,
            evaluation_date=evaluation_date,
            facts=facts,
            conflicts=conflicts,
        )


def _canonical(raw_key: str) -> str | None:
    from app.modules.eligibility.rule_types import normalize_field_key

    key = normalize_field_key(raw_key)
    if key is None:
        return None
    return CANONICAL_ALIAS.get(key, key)
