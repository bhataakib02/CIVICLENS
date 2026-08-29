"""Unit tests: application state machine — every valid + invalid transition
and role gating (prompt §44, no DB)."""
from __future__ import annotations

import itertools

import pytest

from app.core.exceptions import PermissionDeniedError
from app.models.enums import ApplicationStatus as S
from app.modules.applications import state_machine as sm
from app.modules.applications.state_machine import InvalidStateTransitionError

pytestmark = pytest.mark.unit

VALID = [
    (S.DRAFT, S.READY_FOR_SUBMISSION),
    (S.DRAFT, S.WITHDRAWN),
    (S.READY_FOR_SUBMISSION, S.SUBMITTED),
    (S.READY_FOR_SUBMISSION, S.SUBMISSION_PENDING),
    (S.READY_FOR_SUBMISSION, S.WITHDRAWN),
    (S.SUBMISSION_PENDING, S.SUBMITTED),
    (S.SUBMISSION_PENDING, S.SUBMISSION_FAILED),
    (S.SUBMISSION_FAILED, S.READY_FOR_SUBMISSION),
    (S.SUBMITTED, S.UNDER_REVIEW),
    (S.SUBMITTED, S.WITHDRAWN),
    (S.UNDER_REVIEW, S.ACTION_REQUIRED),
    (S.UNDER_REVIEW, S.APPROVED),
    (S.UNDER_REVIEW, S.REJECTED),
    (S.ACTION_REQUIRED, S.UNDER_REVIEW),
    (S.APPROVED, S.COMPLETED),
]

# Explicitly forbidden transitions from the prompt.
INVALID = [
    (S.COMPLETED, S.DRAFT),
    (S.REJECTED, S.APPROVED),
    (S.WITHDRAWN, S.SUBMITTED),
    (S.APPROVED, S.REJECTED),
    (S.DRAFT, S.APPROVED),
    (S.DRAFT, S.SUBMITTED),
    (S.SUBMITTED, S.APPROVED),
    (S.COMPLETED, S.WITHDRAWN),
]


@pytest.mark.parametrize("frm,to", VALID)
def test_valid_transitions_allowed(frm, to):
    assert sm.can_transition(frm, to) is True
    sm.assert_transition(frm, to)  # no raise


@pytest.mark.parametrize("frm,to", INVALID)
def test_invalid_transitions_rejected(frm, to):
    assert sm.can_transition(frm, to) is False
    with pytest.raises(InvalidStateTransitionError):
        sm.assert_transition(frm, to)


def test_terminal_states_have_no_exits():
    for terminal in (S.REJECTED, S.WITHDRAWN, S.COMPLETED):
        assert sm.all_transitions()[terminal] == set()
        assert sm.is_terminal(terminal)


def test_exhaustive_transition_matrix_matches_table():
    # Every (from,to) pair not in the allowed table must be rejected.
    allowed = {(f, t) for f, tos in sm.all_transitions().items() for t in tos}
    for frm, to in itertools.product(list(S), list(S)):
        if (frm, to) in allowed:
            assert sm.can_transition(frm, to)
        else:
            assert not sm.can_transition(frm, to)


def test_role_gating_citizen_cannot_approve():
    # Transition DRAFT->? is fine; but citizen cannot drive APPROVED.
    with pytest.raises(PermissionDeniedError):
        sm.assert_transition(S.UNDER_REVIEW, S.APPROVED, role="citizen")


def test_role_gating_reviewer_can_approve():
    sm.assert_transition(S.UNDER_REVIEW, S.APPROVED, role="agent")  # no raise


def test_role_gating_citizen_can_resolve_action():
    sm.assert_transition(S.ACTION_REQUIRED, S.UNDER_REVIEW, role="citizen")  # no raise


def test_role_gating_citizen_can_withdraw():
    sm.assert_transition(S.SUBMITTED, S.WITHDRAWN, role="citizen")  # no raise
