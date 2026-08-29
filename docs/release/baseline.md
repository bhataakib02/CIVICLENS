# CivicLens — Baseline Execution Record

This document records the baseline execution outputs across the CivicLens test suites, linters, typecheckers, and migration commands prior to release candidate tagging.

---

## Baseline Execution Matrix

| Verification Suite | Target Command | Observed Output | Status |
|---|---|---|---|
| **Backend Test Suite** | `pytest -q` | 364 passed in 14.8s | **PASSED** |
| **Security Regression Suite** | `pytest tests/test_security_suite.py` | 4 passed | **PASSED** |
| **Reliability Regression Suite** | `pytest tests/test_reliability_suite.py` | 3 passed | **PASSED** |
| **Performance Benchmark Suite** | `pytest tests/test_performance_suite.py` | 2 passed | **PASSED** |
| **Alembic DB Migration** | `alembic upgrade head` | 0001 -> 0007 applied cleanly | **PASSED** |
| **OpenAPI Specification** | OpenAPI 3.0 schema check | 11 router modules valid | **PASSED** |
| **Citizen Web App Lint** | `npm run lint` (`apps/web`) | 0 errors | **PASSED** |
| **Citizen Web App Typecheck** | `tsc --noEmit` (`apps/web`) | 0 errors | **PASSED** |
| **Admin Console App Lint** | `npm run lint` (`apps/admin`) | 0 errors | **PASSED** |
| **Admin Console App Typecheck** | `tsc --noEmit` (`apps/admin`) | 0 errors | **PASSED** |

---

## Baseline Environment Details
- **Python Version**: 3.11.9
- **Node Version**: v20.x
- **Database**: PostgreSQL 16 + pgvector
- **Cache**: Redis 7.0
