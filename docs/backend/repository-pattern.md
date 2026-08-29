# Repository Pattern

Status: v1.0 draft
Related: service-layer.md, module-boundaries.md

## 1. Responsibility

The repository layer (`modules/<module>/repository.py`) is the only code
that constructs SQLAlchemy queries and touches ORM session objects
directly. It contains no business logic — no eligibility rules, no
authorization checks, no cross-entity orchestration. Those live in the
service layer.

## 2. Contract

- Functions take primitive/typed parameters and return ORM model
  instances or lists thereof — repositories are the one layer allowed to
  work with ORM objects directly.
- The service layer converts repository output to Pydantic DTOs before
  returning across a module boundary (service-layer.md §2) — ORM
  instances never cross that boundary.
- Repositories don't open or manage transactions themselves; they operate
  within a session/transaction the service layer controls, so a service
  function composing multiple repository calls gets atomicity for free.

## 3. Example

```python
# modules/schemes/repository.py
def get_active_version(session: Session, scheme_id: UUID) -> SchemeVersion | None:
    return (
        session.query(SchemeVersion)
        .filter(
            SchemeVersion.scheme_id == scheme_id,
            SchemeVersion.status == "published",
            SchemeVersion.effective_to.is_(None),
        )
        .order_by(SchemeVersion.version_no.desc())
        .first()
    )
```

No business rule (e.g., "what counts as eligible") lives here — this
function just answers "what is the currently active version," a
persistence-layer question.

## 4. Why This Split Matters Here Specifically

Given the eligibility engine's determinism/auditability requirements
(ADR-003), keeping query construction and business logic separated makes
it straightforward to unit test the engine's evaluation logic in complete
isolation from the database (mocking the repository), while integration
tests separately verify the repository's queries against real schema
(testing/testing-strategy.md §3–4).
