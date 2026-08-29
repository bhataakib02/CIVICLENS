# Authorization Model

Status: v1.0 draft
Related: security-architecture.md §1, threat-model.md #2 #6, api/authorization.md

## 1. Roles

| Role | Scope |
|---|---|
| `citizen` | Own profile, addresses, documents, applications, notifications only |
| `agent` | Citizen-equivalent access, but only for citizens with an active `agent_assist` consent naming that agent |
| `scheme_admin` | Full CRUD on schemes/scheme_versions/eligibility_rules/document_requirements (draft state); publish requires a second `scheme_admin` reviewer |
| `admin` | All of the above plus audit log access, knowledge source management, user role management |

## 2. Enforcement Points

1. **Router-level role check**: a dependency asserts the JWT's role is
   permitted for the endpoint at all (coarse-grained).
2. **Service-level ownership check**: for citizen-scoped resources, the
   service layer independently verifies the resource's `citizen_profile_id`
   matches the requester's own profile (or a validly-consented agent
   relationship) — this check happens even for `admin`/`agent` roles
   accessing citizen data, so a role check alone never suffices
   (threat-model.md #2, #6).
3. **Four-eyes on publish**: `scheme_version` publish requires the
   publishing user to differ from the version's author (FR-ADMIN-2),
   enforced in the service layer, not just process/policy.

## 3. Never-Trust-The-Client Rule

No authorization decision is made client-side only. The frontend hides UI
it doesn't expect the user to need, but every corresponding API endpoint
independently re-checks role and ownership — the API is the actual
boundary.

## 4. Denial Response Shape

Authorization failures return 403 (authenticated but not permitted) or 404
(when revealing existence of the resource would itself leak information —
e.g., another citizen's application ID) rather than 401, and are logged
for anomaly detection (security-architecture.md §4).
