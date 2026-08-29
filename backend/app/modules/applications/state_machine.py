"""Application state machine (prompt §5, §6, §7).

SINGLE SOURCE OF TRUTH for application status transitions. Routers/services
never hardcode transition rules — they call can_transition / assert_transition.

Transitions are also role-gated: a citizen drives draft/submit/withdraw/resolve;
a case worker/admin drives review transitions. Enforced server-side.

`info_requested` is treated as an alias of `action_required` for contract
compatibility (both are the same review-wait state).
"""
from __future__ import annotations

from app.core.exceptions import AppError
from app.models.enums import ApplicationStatus as S
from app.models.enums import UserRole

# Roles that act as reviewers/case workers.
REVIEWER_ROLES = {UserRole.AGENT.value, UserRole.ADMIN.value}
CITIZEN_ROLE = UserRole.CITIZEN.value

TERMINAL_STATES = {S.APPROVED, S.REJECTED, S.WITHDRAWN, S.COMPLETED}

# Allowed transitions: from -> set of reachable states.
_TRANSITIONS: dict[S, set[S]] = {
    S.DRAFT: {S.READY_FOR_SUBMISSION, S.WITHDRAWN},
    S.READY_FOR_SUBMISSION: {S.DRAFT, S.SUBMISSION_PENDING, S.SUBMITTED, S.WITHDRAWN},
    S.SUBMISSION_PENDING: {S.SUBMITTED, S.SUBMISSION_FAILED},
    S.SUBMISSION_FAILED: {S.READY_FOR_SUBMISSION, S.WITHDRAWN},
    S.SUBMITTED: {S.UNDER_REVIEW, S.WITHDRAWN},
    S.UNDER_REVIEW: {S.ACTION_REQUIRED, S.APPROVED, S.REJECTED},
    S.ACTION_REQUIRED: {S.UNDER_REVIEW},
    S.INFO_REQUESTED: {S.UNDER_REVIEW},  # alias state
    S.APPROVED: {S.COMPLETED},
    S.REJECTED: set(),
    S.WITHDRAWN: set(),
    S.COMPLETED: set(),
}

# Which role may drive each transition (target-state -> allowed roles).
_ROLE_FOR_TARGET: dict[S, set[str]] = {
    S.READY_FOR_SUBMISSION: {CITIZEN_ROLE, *REVIEWER_ROLES},
    S.DRAFT: {CITIZEN_ROLE, *REVIEWER_ROLES},
    S.SUBMISSION_PENDING: {CITIZEN_ROLE, *REVIEWER_ROLES},
    S.SUBMISSION_FAILED: {CITIZEN_ROLE, *REVIEWER_ROLES},
    S.SUBMITTED: {CITIZEN_ROLE, *REVIEWER_ROLES},
    S.WITHDRAWN: {CITIZEN_ROLE, *REVIEWER_ROLES},
    S.UNDER_REVIEW: REVIEWER_ROLES | {CITIZEN_ROLE},  # citizen resolves ACTION_REQUIRED->UNDER_REVIEW
    S.ACTION_REQUIRED: REVIEWER_ROLES,
    S.APPROVED: REVIEWER_ROLES,
    S.REJECTED: REVIEWER_ROLES,
    S.COMPLETED: REVIEWER_ROLES,
}


class InvalidStateTransitionError(AppError):
    status_code = 409
    code = "INVALID_STATE_TRANSITION"
    message = "This application status transition is not allowed."


def _coerce(status) -> S:
    return status if isinstance(status, S) else S(status)


def can_transition(current, target) -> bool:
    return _coerce(target) in _TRANSITIONS.get(_coerce(current), set())


def role_may_transition(role: str, target) -> bool:
    return role in _ROLE_FOR_TARGET.get(_coerce(target), set())


def assert_transition(current, target, *, role: str | None = None) -> None:
    """Raise InvalidStateTransitionError if the transition (and role) is illegal."""
    current_s, target_s = _coerce(current), _coerce(target)
    if not can_transition(current_s, target_s):
        raise InvalidStateTransitionError(
            f"Cannot transition {current_s.value} -> {target_s.value}."
        )
    if role is not None and not role_may_transition(role, target_s):
        from app.core.exceptions import PermissionDeniedError

        raise PermissionDeniedError(
            f"Role '{role}' may not perform the transition to {target_s.value}."
        )


def is_terminal(status) -> bool:
    return _coerce(status) in TERMINAL_STATES


def all_transitions() -> dict[S, set[S]]:
    return {k: set(v) for k, v in _TRANSITIONS.items()}
