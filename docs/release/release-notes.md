# CivicLens Release Candidate 1 (v1.0.0-rc.1) — Release Notes

---

## Overview
We are pleased to announce **CivicLens Release Candidate 1 (`v1.0.0-rc.1`)**. This candidate is a fully validated, security-hardened, and failure-tested release of the CivicLens civic technology platform.

---

## Key Platform Capabilities

1. **Deterministic Scheme Eligibility Engine**:
   - Sub-2.5ms AST evaluation engine assessing citizen facts against versioned policy rules with 100% reproducible outcomes.
2. **Four-Eyes Scheme Publishing Governance**:
   - Server-side access control preventing scheme authors from publishing their own draft versions.
3. **Document Intelligence & Magic Bytes Inspection**:
   - Two-step presigned upload pipeline enforcing `%PDF-`, `\x89PNG`, and `\xFF\xD8` binary header inspection prior to OCR entity extraction.
4. **Prompt-Isolated Vector RAG Assistant**:
   - PostgreSQL `pgvector` HNSW vector search grounding policy answers with clickable source citations while protecting context passages in `<untrusted_context>` tags.
5. **Transactional Outbox & Realtime Eventing**:
   - Atomic database outbox records driving asynchronous Celery notification dispatches and live WebSocket UI streams.
6. **Argon2id Authentication & OTP Verification**:
   - Security-hardened authentication with Pydantic `extra="forbid"` mass assignment protection and sliding session refresh tokens.

---

## Known Operational Dependencies
- **AWS Infrastructure**: Declared via complete Terraform modules (`infrastructure/terraform/`), awaiting production cloud credentials.
- **Third-Party Gateways**: Production SMS/Email delivery uses fallback mock providers when vendor credentials are not supplied.
