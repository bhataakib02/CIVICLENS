# CivicLens — Technical Architecture Walkthrough & Interview Guide

This guide prepares engineers to discuss the architecture, engineering tradeoffs, and system design decisions of CivicLens.

---

## Technical Q&A Guide

### Q1: Why separate the AI LLM Assistant from the Eligibility Engine?
- **Answer**: LLMs are probabilistic and prone to hallucination. In public sector benefits administration, misinforming a citizen about legal eligibility is unacceptable. CivicLens uses a deterministic Rule Engine (`app.modules.eligibility.engine`) that evaluates AST expressions against verified facts with 100% reproducible outcomes. The LLM is used strictly in a descriptive, conversational role for RAG search and policy explanation.

### Q2: How does CivicLens handle asynchronous event consistency and notifications?
- **Answer**: CivicLens uses the **Transactional Outbox Pattern** (`OutboxWriter`). When an application state transition occurs, the domain state mutation and an `outbox_events` record are committed within the same database transaction. A Celery background worker polls or processes outbox records, guaranteeing at-least-once event delivery to SMS/Email dispatchers and live WebSocket streams without losing events during node crashes.

### Q3: How is document upload security enforced?
- **Answer**: File uploads use a two-step presigned S3 URL pattern (`upload-init` -> `complete`). Before processing, the server re-reads the object bytes and performs **Magic Bytes Header Validation** (`_validate_magic_bytes`), verifying `%PDF-`, `\x89PNG`, or `\xFF\xD8` signatures to prevent executable file uploads disguised with fake MIME headers.

### Q4: How does CivicLens prevent horizontal privilege escalation (IDOR)?
- **Answer**: Every single record lookup in the service layer enforces explicit ownership checks (`citizen_profile_id == current_profile_id`), independent of FastAPI route dependencies. If a user attempts to access another citizen's resource ID, the API returns a 404 Not Found to prevent disclosing resource existence.
