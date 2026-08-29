# Rate Limiting

Status: v1.0 draft
Related: security-architecture.md, threat-model.md #12, architecture/system-architecture.md (Redis)

## 1. Implementation

Redis-backed sliding-window counters, enforced at the API gateway/
middleware layer before a request reaches business logic.

## 2. Limits by Endpoint Class

| Endpoint class | Limit | Key |
|---|---|---|
| `/auth/otp/request` | 5 / hour | phone_number |
| `/auth/otp/verify` | 5 attempts / issued code | phone_number + code |
| `/auth/token/refresh` | 30 / hour | user_id |
| `/assistant/messages` | 20 / hour (citizen), higher for agent role | user_id |
| `/eligibility/check-all` | 10 / hour | user_id (bulk op, cache-backed anyway) |
| General authenticated API | 300 / hour | user_id |
| Unauthenticated (scheme browse) | 60 / hour | IP |

Limits are configuration, not hardcoded, and reviewed periodically against
observed legitimate usage patterns to avoid blocking real citizens while
still deterring abuse.

## 3. Response

429 with a `Retry-After` header and the standard error envelope
(`error.code = "rate_limited"`). The assistant endpoint's limit exists
primarily for cost control (LLM calls) as much as abuse prevention.

## 4. Bypass for Trusted Agents

`agent` role accounts (CSC operators processing multiple citizens) get
higher per-agent limits reflecting legitimate bulk usage, but each
citizen-scoped action still passes through the ownership/consent check in
authorization-model.md — rate limiting is not a substitute for
authorization.
