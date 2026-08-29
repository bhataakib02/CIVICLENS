# API Authentication

Status: v1.0 draft
Related: api-overview.md, security/authentication-security.md, openapi.yaml (securitySchemes.bearerAuth)

## 1. Scheme

Bearer JWT in the `Authorization: Bearer <token>` header, as declared in
`openapi.yaml`'s `bearerAuth` security scheme. All endpoints require it
except `/health`, `/health/ready`, `/auth/otp/request`,
`/auth/otp/verify`, `/auth/token/refresh`.

## 2. Obtaining a Token

1. `POST /auth/otp/request` with a phone number → OTP dispatched via SMS.
2. `POST /auth/otp/verify` with phone number + code → returns
   `{access_token, refresh_token, token_type, expires_in}`
   (`TokenPair` schema). Registers a new account automatically if the
   phone number is unseen (FR-AUTH-1).
3. Staff/admin accounts use a separate email+password+MFA flow (not
   exposed on this same endpoint pair — see
   security/authentication-security.md §2).

## 3. Using the Token

Include `Authorization: Bearer <access_token>` on every subsequent
request. Access tokens expire quickly (~15 min); use
`POST /auth/token/refresh` with the refresh token to obtain a new pair
before expiry, or on receiving a 401.

## 4. Token Expiry & Revocation

A 401 with `error.code = "token_expired"` signals the client should
refresh. `POST /auth/logout` (optionally `?all=true`) revokes the current
or all refresh tokens; see security/authentication-security.md §3 for the
rotation/reuse-detection mechanics.

## 5. Agent-Scoped Requests

An `agent`-role token acts on behalf of a citizen only where an active
`agent_assist` consent exists; there is no separate "act as citizen X"
token — every request carries the agent's own identity and the target
citizen is specified explicitly per request, checked server-side each
time (security/authorization-model.md §2).
