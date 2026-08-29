# Service Layer

Status: v1.0 draft
Related: component-architecture.md §2, module-boundaries.md, repository-pattern.md

## 1. Responsibility

The service layer holds all business logic and transaction boundaries for
a module. Routers never contain business logic beyond request/response
shaping; repositories never contain business logic beyond query
construction.

## 2. Contract

Service functions:
- Accept and return typed DTOs (Pydantic schemas) or plain Python types —
  never leak ORM model instances across the module boundary (this is what
  makes `module-boundaries.md`'s "service and schemas only" rule
  meaningful).
- Own the transaction: a service function that writes to multiple tables
  wraps them in a single DB transaction and is the unit other modules call
  when they need that operation, rather than composing multiple raw
  repository calls themselves.
- Raise typed domain exceptions (e.g., `SchemeNotEligibleError`,
  `DocumentNotVerifiedError`) that routers translate to the appropriate
  HTTP status + error envelope (api/error-handling.md) — services never
  raise or catch `HTTPException` directly, keeping them testable without
  an HTTP context.

## 3. Example: `applications.service.start_application`

```python
def start_application(citizen_id: UUID, scheme_id: UUID) -> ApplicationDTO:
    eligibility = eligibility_service.evaluate(citizen_id, scheme_id)
    if eligibility.result not in ("eligible", "likely_eligible"):
        raise SchemeNotEligibleError(scheme_id)
    scheme_version = schemes_service.get_active_version(scheme_id)
    application = applications_repository.create(
        citizen_id, scheme_version.id, status="draft"
    )
    applications_repository.record_status_history(
        application.id, from_status=None, to_status="draft", actor=citizen_id
    )
    return ApplicationDTO.from_orm(application)
```

Note the cross-module calls are to `eligibility_service` and
`schemes_service` — other modules' service layers, per
module-boundaries.md — never their repositories or models directly.

## 4. Testing

Service functions are the primary target of unit and integration testing
(testing/testing-strategy.md §3–4): unit tests mock the repository layer;
integration tests run against a real ephemeral database to catch query
and transaction-boundary issues mocking would hide.
