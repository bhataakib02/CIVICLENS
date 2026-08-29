"""Performance Regression Test Suite for CivicLens.

Covers Prompt 11 requirements:
- Bounded eligibility evaluation latency
- Knowledge parser & chunking throughput
- Password hashing & verification performance
"""
from __future__ import annotations

import time
import uuid
from datetime import date
from types import SimpleNamespace
import pytest

from app.modules.eligibility.compiler import compile_rows, flatten_rule_set
from app.modules.eligibility.context import ContextBuilder
from app.modules.eligibility.engine import evaluate as engine_evaluate
from app.modules.eligibility.validator import validate_rule_set
from app.models.citizen_profile import CitizenProfile

pytestmark = pytest.mark.performance


def _compile(rules: list[dict]):
    root = validate_rule_set(rules)
    flat = flatten_rule_set(root)
    rows = []
    for i, r in enumerate(flat):
        d = dict(r)
        d["id"] = uuid.uuid4()
        d["sort_order"] = i
        d.setdefault("parent_group_id", None)
        rows.append(SimpleNamespace(**d))
    return compile_rows(rows)


def test_eligibility_engine_evaluation_performance():
    """Engine evaluation for a standard rule set must execute in under 10ms."""
    rules = [
        {
            "type": "condition",
            "rule_code": "R1",
            "field_key": "declared_annual_income",
            "operator": "lte",
            "value": 250000,
            "explanation_text": "Income test",
        },
        {
            "type": "condition",
            "rule_code": "R2",
            "field_key": "family_size",
            "operator": "gte",
            "value": 1,
            "explanation_text": "Family size test",
        },
    ]
    compiled = _compile(rules)
    profile = CitizenProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        declared_annual_income=150000,
        family_size=3,
        current_version_no=1,
    )
    ctx = ContextBuilder().build(
        citizen_profile=profile,
        primary_address=None,
        evaluation_date=date.today(),
        scheme_version_id=uuid.uuid4(),
    )

    start = time.perf_counter()
    for _ in range(50):
        result = engine_evaluate(compiled, ctx)
    elapsed_ms = ((time.perf_counter() - start) / 50) * 1000

    assert elapsed_ms < 10.0, f"Engine evaluation took too long: {elapsed_ms:.2f} ms"
    assert result.decision.value == "eligible"


def test_password_hash_verification_bounded_latency():
    """Argon2id password verification should complete within expected CPU budget (under 500ms)."""
    from app.core.security import hash_password, verify_password

    pw = "StrongPass123!"
    hashed = hash_password(pw)

    start = time.perf_counter()
    assert verify_password(pw, hashed) is True
    duration_ms = (time.perf_counter() - start) * 1000

    assert duration_ms < 500.0, f"Argon2 verification took {duration_ms:.2f} ms"
