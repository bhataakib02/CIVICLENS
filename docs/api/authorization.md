# API Authorization

Status: v1.0 draft
Related: security/authorization-model.md, api-overview.md

## 1. Role Requirements Per Resource Group

| Resource group | Allowed roles |
|---|---|
| `/me*`, `/documents*`, `/applications*`, `/notifications*` | `citizen` (own data), `agent` (consented citizen's data) |
| `/schemes*`, `/eligibility*`, `/assistant*` | `citizen`, `agent` |
| `/admin/schemes*`, `/admin/scheme-versions*`, `/admin/knowledge-sources*` | `scheme_admin`, `admin` |
| `/admin/audit-logs` | `admin` only |

## 2. Ownership Enforcement

Role membership alone is necessary but not sufficient — every citizen-
scoped endpoint additionally verifies resource ownership (or a valid
agent consent) in the service layer, per
security/authorization-model.md §2. A `citizen` token can never read or
write another citizen's `/me`, `/documents`, or `/applications` data
regardless of how the request is crafted.

## 3. Error Responses

- 401: missing/invalid/expired token.
- 403: valid token, insufficient role or failed ownership/consent check.
- 404: used instead of 403 where confirming a resource's existence to an
  unauthorized caller would itself leak information (e.g., another
  citizen's `application_id`).

## 4. Four-Eyes Endpoints

`POST /admin/scheme-versions/{id}/publish` additionally checks the
publishing user differs from the version's original author, returning 403
with a specific message if they match (FR-ADMIN-2) — this is an
authorization rule beyond simple role membership.
