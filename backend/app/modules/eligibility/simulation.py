"""Rule simulation engine (prompt §18).

Allows a Scheme Admin to simulate a draft rule set against citizen profile datasets.
Security & Privacy:
  - Operates on a draft/version without modifying published rules.
  - Aggregates and anonymizes results: outputs only counts (newly_eligible,
    newly_ineligible, unchanged, insufficient_data).
  - Contains NO personally identifying information (PII) in output.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.citizen_profile import CitizenProfile
from app.models.enums import UserRole
from app.modules.auth.dependencies import CurrentUser
from app.modules.eligibility.compiler import flatten_rule_set
from app.modules.eligibility.context import ContextBuilder
from app.modules.eligibility.engine import EngineResult, evaluate
from app.modules.eligibility.repository import EligibilityRepository
from app.modules.eligibility.rule_types import Decision
from app.modules.eligibility.validator import validate_rule_set
from app.modules.schemes.repository import SchemesRepository


class RuleSimulationInput(BaseModel):
    scheme_version_id: uuid.UUID
    draft_rules: list[dict] = Field(description="List of raw rule definitions to test")


class RuleSimulationResult(BaseModel):
    scheme_version_id: uuid.UUID
    total_profiles_evaluated: int
    newly_eligible: int
    newly_ineligible: int
    unchanged: int
    insufficient_data: int
    summary: dict[str, int]


class RuleSimulationService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._eligibility_repo = EligibilityRepository(session)
        self._schemes_repo = SchemesRepository(session)

    def simulate(
        self,
        current: CurrentUser,
        body: RuleSimulationInput,
    ) -> RuleSimulationResult:
        if current.role not in (UserRole.SCHEME_ADMIN.value, UserRole.ADMIN.value):
            raise PermissionDeniedError("Only Scheme Admins or Admins can run rule simulations.")

        version = self._schemes_repo.get_version(body.scheme_version_id)
        if version is None:
            raise NotFoundError("Scheme version not found.")

        # Validate draft rules
        validate_rule_set(body.draft_rules)
        draft_ast = flatten_rule_set(body.draft_rules)

        # Existing rules AST for comparison
        existing_rows = self._eligibility_repo.load_rules(version.id)
        existing_rules_dict = [
            {
                "id": str(r.id),
                "rule_code": r.rule_code,
                "field_key": r.field_key,
                "operator": r.operator,
                "value": r.value,
                "mandatory": r.mandatory,
                "group_id": r.group_id,
                "group_operator": r.group_operator,
            }
            for r in existing_rows
        ]
        existing_ast = flatten_rule_set(existing_rules_dict) if existing_rules_dict else None

        # Fetch citizen profiles for simulation (anonymized)
        profiles = list(self._session.scalars(select(CitizenProfile).limit(500)))
        today = date.today()

        newly_eligible = 0
        newly_ineligible = 0
        unchanged = 0
        insufficient_data = 0

        for profile in profiles:
            primary_address = self._eligibility_repo.primary_address(profile.id)
            ctx = ContextBuilder().build(
                citizen_profile=profile,
                primary_address=primary_address,
                evaluation_date=today,
                scheme_version_id=version.id,
                extra_facts={},
            )

            new_result: EngineResult = evaluate(draft_ast, ctx)

            if existing_ast:
                old_result: EngineResult = evaluate(existing_ast, ctx)
                old_dec = old_result.decision
            else:
                old_dec = Decision.INSUFFICIENT_DATA

            new_dec = new_result.decision

            if new_dec == Decision.INSUFFICIENT_DATA:
                insufficient_data += 1
            elif old_dec == new_dec:
                unchanged += 1
            elif new_dec in (Decision.ELIGIBLE, Decision.LIKELY_ELIGIBLE) and old_dec not in (
                Decision.ELIGIBLE,
                Decision.LIKELY_ELIGIBLE,
            ):
                newly_eligible += 1
            elif old_dec in (Decision.ELIGIBLE, Decision.LIKELY_ELIGIBLE) and new_dec not in (
                Decision.ELIGIBLE,
                Decision.LIKELY_ELIGIBLE,
            ):
                newly_ineligible += 1
            else:
                unchanged += 1

        summary = {
            "eligible": newly_eligible,
            "ineligible": newly_ineligible,
            "unchanged": unchanged,
            "insufficient_data": insufficient_data,
        }

        return RuleSimulationResult(
            scheme_version_id=version.id,
            total_profiles_evaluated=len(profiles),
            newly_eligible=newly_eligible,
            newly_ineligible=newly_ineligible,
            unchanged=unchanged,
            insufficient_data=insufficient_data,
            summary=summary,
        )
