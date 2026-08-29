# Module Boundaries

Status: v1.0 draft
Related: architecture/component-architecture.md, NFR-MAINT-1, CONTRIBUTING.md §3

## 1. The Rule

A module (`backend/app/modules/<name>/`) may import:
- Another module's `service.py` (function calls) and `schemas.py`
  (Pydantic types).

A module may **never** import:
- Another module's `models.py` (ORM classes) or `repository.py`.

Direct cross-module database access — reaching into another module's
tables via raw SQL or a shared session query — is likewise prohibited;
all cross-module reads go through the owning module's service layer.

## 2. Why

This keeps each module free to change its internal schema/persistence
without breaking unrelated modules, keeps transaction/authorization logic
co-located with the data it governs (a module's service layer is the only
place that can decide "is this access allowed"), and preserves the option
to extract a module into a separate service later (most likely candidates:
`documents`/OCR and the `assistant`/RAG pipeline, given their distinct
load profiles) without a rewrite.

## 3. Enforcement

An import-linter configuration (`backend/setup.cfg` or equivalent) defines
the allowed import graph and runs in CI on every PR
(infrastructure/ci-cd.md); a violation fails the build. This is not a
convention enforced by code review alone — review catches what CI misses,
not the primary line of defense.

## 4. Shared Code

Genuinely cross-cutting code (auth dependencies, base ORM config, logging
setup, common exceptions) lives in `backend/app/core/` and
`backend/app/db/`, which every module may depend on — these are
foundational, not peer modules, and have no reverse dependency on any
domain module.

## 5. Example Violation (rejected in review)

```python
# modules/applications/service.py
from app.modules.documents.models import Document  # ✗ NOT ALLOWED

# Correct:
from app.modules.documents.service import get_verified_documents  # ✓
```
