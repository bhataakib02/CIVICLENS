# Integration Testing

Status: v1.0 draft
Related: testing-strategy.md §4, backend/repository-pattern.md §4, database/migration-strategy.md §5

## 1. Scope

A module's service + repository layer running against a real, ephemeral
(Dockerized, spun up per test run) PostgreSQL and Redis — no mocking the
database. This is where ORM query correctness, migration/schema
consistency with erd.md, and transaction-boundary behavior are actually
verified, not assumed.

## 2. Cross-Module Flows

Because service layers call other modules' service layers directly
(backend/service-layer.md §3), integration tests cover realistic
cross-module sequences end-to-end at the service layer (without going
through HTTP): starting an application triggers an eligibility re-check
and document-completeness check; publishing a scheme_version invalidates
cached eligibility results; a profile edit invalidates the affected
citizen's cached eligibility results.

## 3. Migration Consistency

Every integration test run applies migrations from scratch against a
fresh database (not a pre-baked schema dump), so a migration/model drift
bug surfaces here before it reaches contract or E2E tests
(database/migration-strategy.md §5).

## 4. Test Data

Uses the synthetic fixture set (testing-strategy.md §10) — representative
citizen profiles, scheme/rule fixtures spanning the DSL's operator set,
and sample knowledge sources — never real data, even in CI.

## 5. Isolation

Each test (or test class) runs against an isolated database
transaction/schema that's rolled back or torn down afterward, so tests
don't leak state into one another regardless of execution order.
