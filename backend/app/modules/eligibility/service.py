"""Eligibility application service.

Orchestrates a single deterministic eligibility check:
  authz -> resolve scheme_version -> ONE context load -> compile AST (cached)
  -> evaluate -> persist (idempotent) -> explanation.

Determinism/auditability (prompt §21): the persisted eligibility_checks row
stores scheme_version_id, profile_version_no, engine_version, decision,
full rule_breakdown, missing_information, conflicts, evidence, and computed_at.
Re-running the same (profile snapshot, scheme_version, engine_version) returns
the identical stored result (idempotency), and recomputation is deterministic.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.core.logging import get_logger
from app.models.eligibility import EligibilityCheck
from app.models.enums import SchemeVersionStatus
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.dependencies import CurrentUser
from app.modules.eligibility.compiler import rule_cache
from app.modules.eligibility.context import ContextBuilder
from app.modules.eligibility.engine import EngineResult, evaluate
from app.modules.eligibility.explanation import build_explanation
from app.modules.eligibility.policies import STAFF_ROLES
from app.modules.eligibility.repository import EligibilityRepository
from app.modules.eligibility.rule_types import ENGINE_VERSION

logger = get_logger("civiclens.eligibility")


class EligibilityService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = EligibilityRepository(session)
        self._audit = AuditService(session)

    def check(
        self,
        *,
        current: CurrentUser,
        scheme_id: uuid.UUID | None,
        scheme_version_id: uuid.UUID | None,
        facts: dict,
        idempotency_key: str | None,
        target_profile_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> dict:
        # --- resolve the citizen profile (identity from principal) ---
        if target_profile_id is not None and current.role in STAFF_ROLES:
            profile = self._repo.get_profile(target_profile_id)
        elif target_profile_id is not None and current.role not in STAFF_ROLES:
            # A citizen attempting to target another profile is forbidden.
            raise PermissionDeniedError("You may only evaluate your own eligibility.")
        else:
            profile = self._repo.get_profile_by_user_id(current.id)
        if profile is None:
            raise NotFoundError("Citizen profile not found.")

        # --- resolve the scheme_version ---
        version = self._resolve_version(scheme_id, scheme_version_id)

        logger.info(
            "eligibility_check_started",
            extra={
                "scheme_version_id": str(version.id),
                "citizen_profile_id": str(profile.id),
                "engine_version": ENGINE_VERSION,
            },
        )

        try:
            # --- idempotency / cache: identical inputs => stored result ---
            existing = self._repo.find_idempotent(
                profile_id=profile.id,
                profile_version_no=profile.current_version_no,
                scheme_version_id=version.id,
                engine_version=ENGINE_VERSION,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                logger.info(
                    "eligibility_check_completed",
                    extra={
                        "scheme_version_id": str(version.id),
                        "result": existing.result,
                        "cached": True,
                    },
                )
                return self._to_output(existing, profile_id=profile.id, scheme_id=version.scheme_id)

            # --- ONE context load (profile + primary address) ---
            primary_address = self._repo.primary_address(profile.id)
            ctx = ContextBuilder().build(
                citizen_profile=profile,
                primary_address=primary_address,
                evaluation_date=date.today(),
                scheme_version_id=version.id,
                extra_facts=facts,
            )

            # --- compile (cached per scheme_version) + evaluate ---
            rows = self._repo.load_rules(version.id)
            ast = rule_cache.get_or_compile(version.id, rows)
            result: EngineResult = evaluate(ast, ctx)

            check = self._persist(profile, version.id, result, idempotency_key)
            self._audit.record(
                action=AuditAction.ELIGIBILITY_CHECK,
                entity_type="eligibility_check",
                entity_id=check.id,
                actor_user_id=current.id,
                diff={"scheme_version_id": str(version.id), "result": result.decision.value},
                ip=ip,
            )
            self._session.commit()
            self._session.refresh(check)
            logger.info(
                "eligibility_check_completed",
                extra={
                    "scheme_version_id": str(version.id),
                    "result": check.result,
                    "cached": False,
                },
            )
            return self._to_output(check, profile_id=profile.id, scheme_id=version.scheme_id)
        except (NotFoundError, PermissionDeniedError, ValidationError):
            raise
        except Exception:
            self._session.rollback()
            logger.error(
                "eligibility_check_failed",
                extra={"scheme_version_id": str(version.id)},
                exc_info=True,
            )
            raise

    def check_all(
        self,
        *,
        current: CurrentUser,
        target_profile_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> list[dict]:
        """Bulk eligibility check across all active published schemes for a citizen.

        Loads reusable citizen/profile context once, iterates active schemes,
        evaluates deterministically, and returns ranked results.
        """
        if target_profile_id is not None and current.role in STAFF_ROLES:
            profile = self._repo.get_profile(target_profile_id)
        elif target_profile_id is not None and current.role not in STAFF_ROLES:
            raise PermissionDeniedError("You may only evaluate your own eligibility.")
        else:
            profile = self._repo.get_profile_by_user_id(current.id)

        if profile is None:
            raise NotFoundError("Citizen profile not found.")

        # Load context ONCE for all schemes
        primary_address = self._repo.primary_address(profile.id)
        today = date.today()

        # Get all published scheme versions
        from app.modules.schemes.repository import SchemesRepository

        published_versions = SchemesRepository(self._session).list_all_published_versions()

        results = []
        for version in published_versions:
            ctx = ContextBuilder().build(
                citizen_profile=profile,
                primary_address=primary_address,
                evaluation_date=today,
                scheme_version_id=version.id,
                extra_facts={},
            )
            rows = self._repo.load_rules(version.id)
            ast = rule_cache.get_or_compile(version.id, rows)
            res: EngineResult = evaluate(ast, ctx)
            check = self._persist(profile, version.id, res, idempotency_key=None)
            results.append(self._to_output(check, profile_id=profile.id, scheme_id=version.scheme_id))

        self._session.commit()
        return results

    # ------------------------------------------------------------------ #
    def _resolve_version(self, scheme_id, scheme_version_id):
        if scheme_version_id is not None:
            version = self._repo.get_version(scheme_version_id)
            if version is None:
                raise NotFoundError("Scheme version not found.")
            return version
        if scheme_id is not None:
            from app.modules.schemes.repository import SchemesRepository

            version = SchemesRepository(self._session).current_published_version(scheme_id)
            if version is None:
                raise NotFoundError("No currently-published version for this scheme.")
            return version
        raise ValidationError(
            "Either scheme_id or scheme_version_id is required.",
            field_errors=[{"field": "scheme_id", "message": "Provide scheme_id or scheme_version_id."}],
        )

    def _persist(
        self, profile, version_id: uuid.UUID, result: EngineResult, idempotency_key: str | None
    ) -> EligibilityCheck:
        breakdown_json = {
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_code": r.rule_code,
                    "field_key": r.field_key,
                    "operator": r.operator,
                    "value": r.value,
                    "citizen_value": r.citizen_value,
                    "outcome": r.outcome,
                    "mandatory": r.mandatory,
                    "explanation": r.explanation,
                    "source_citation": r.source_citation,
                }
                for r in result.rule_breakdown
            ],
            "matched_rules": result.matched_rules,
            "failed_rules": result.failed_rules,
            "missing_information": result.missing_information,
            "conflicts": result.conflicts,
            "evidence": result.evidence,
        }
        check = EligibilityCheck(
            citizen_profile_id=profile.id,
            profile_version_no=profile.current_version_no,
            scheme_version_id=version_id,
            result=result.decision.value,
            rule_breakdown=breakdown_json,
            engine_version=result.engine_version,
            idempotency_key=idempotency_key,
        )
        try:
            self._repo.add_check(check)
        except IntegrityError:
            # Concurrent identical check won the unique index — return theirs.
            self._session.rollback()
            existing = self._repo.find_idempotent(
                profile_id=profile.id,
                profile_version_no=profile.current_version_no,
                scheme_version_id=version_id,
                engine_version=result.engine_version,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                return existing
            raise
        return check

    def _to_output(self, check: EligibilityCheck, *, profile_id: uuid.UUID, scheme_id: uuid.UUID) -> dict:
        bd = check.rule_breakdown or {}
        # Rebuild explanation deterministically from the stored breakdown.
        result_enum_value = check.result
        explanation = _explanation_from_breakdown(result_enum_value, bd)
        return {
            "id": str(check.id),
            "citizen_id": str(profile_id),
            "scheme_id": str(scheme_id),
            "scheme_version_id": str(check.scheme_version_id),
            "result": check.result,
            "decision": check.result,
            "engine_version": check.engine_version,
            "matched_rules": bd.get("matched_rules", []),
            "failed_rules": bd.get("failed_rules", []),
            "missing_information": bd.get("missing_information", []),
            "conflicts": bd.get("conflicts", []),
            "evidence": bd.get("evidence", []),
            "rule_breakdown": bd.get("rules", []),
            "explanation": explanation,
            "computed_at": check.computed_at,
            "created_at": check.computed_at,
        }


def _explanation_from_breakdown(result_value: str, breakdown: dict) -> str:
    """Rebuild a human explanation from a persisted breakdown (deterministic)."""
    from app.modules.eligibility.engine import EngineResult, RuleOutcomeRow
    from app.modules.eligibility.rule_types import Decision

    rows = [
        RuleOutcomeRow(
            rule_id=r.get("rule_id"),
            rule_code=r.get("rule_code", ""),
            field_key=r.get("field_key", ""),
            operator=r.get("operator", ""),
            value=r.get("value"),
            citizen_value=r.get("citizen_value"),
            outcome=r.get("outcome", "unknown"),
            mandatory=r.get("mandatory", True),
            explanation=r.get("explanation", ""),
            source_citation=r.get("source_citation"),
        )
        for r in breakdown.get("rules", [])
    ]
    engine_result = EngineResult(
        decision=Decision(result_value),
        engine_version="",
        rule_breakdown=rows,
        matched_rules=breakdown.get("matched_rules", []),
        failed_rules=breakdown.get("failed_rules", []),
        missing_information=breakdown.get("missing_information", []),
        conflicts=breakdown.get("conflicts", []),
        evidence=breakdown.get("evidence", []),
    )
    return build_explanation(engine_result)
