# Authentication Security

Status: v1.0 draft
Related: security-architecture.md §1, api/authentication.md, ADR referenced: none (implementation detail, not architecture-level)

## 1. Citizen Authentication (phone + OTP)

- OTP is a 6-digit code, valid for 5 minutes, single-use, rate-limited to
  5 requests per phone number per hour (rate-limiting.md).
- OTP verification attempts are capped (5 per issued code) before the code
  is invalidated, to resist brute force.
- Successful verification issues a short-lived JWT access token (~15 min)
  and a rotating refresh token (FR-AUTH-3).

## 2. Staff/Admin Authentication (email + password + MFA)

- Password hashing: Argon2id.
- MFA (TOTP) is mandatory for `scheme_admin` and `admin` roles
  (NFR-SEC-3, FR-AUTH-5) — no exceptions, no "skip for now" flag in
  production config.
- Failed login attempts are rate-limited and logged; repeated failures
  trigger a temporary account lock with staff notification.

## 3. Token Handling

- Access tokens: JWT, short-lived, signed with an asymmetric key managed
  via secrets-management.md; contain user id, role, and token version
  (for global revocation).
- Refresh tokens: opaque, stored hashed server-side, rotated on every use
  (reuse of an old refresh token invalidates the whole token family —
  standard refresh-token-rotation theft detection).
- Logout revokes the current refresh token; "logout all devices" bumps the
  user's token version, invalidating all outstanding access tokens
  immediately (FR-AUTH-3).

## 4. Session Boundaries

- Agent sessions (FR-AUTH-4) are scoped: an agent's JWT carries their own
  identity, never impersonates the citizen's identity — every
  agent-on-behalf-of-citizen action is attributable to the agent account
  and checked against an active `agent_assist` consent per request, not
  cached for the session.

## 5. Threats Addressed

Directly mitigates threat-model.md #6 (privilege escalation) and
contributes to #12 (API abuse, via OTP rate limiting).
