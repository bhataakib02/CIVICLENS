# CivicLens — Flagship Project Demonstration Scenario

This scenario outlines a 5 to 10 minute live presentation highlighting the key engineering capabilities of CivicLens.

---

## Demonstration Sequence

1. **Citizen Portal Login**:
   - Authenticate as citizen user `citizen@example.com`.
   - Show Progressive Profile completeness scoring (85%).
2. **AI Assistant & Knowledge Retrieval**:
   - Query Assistant: *"What are the income thresholds for the West Bengal Student Credit Card scheme?"*
   - Highlight grounded prose explanation with clickable official source citations.
3. **Deterministic Eligibility Evaluation**:
   - Trigger Scheme Discovery & Check Eligibility.
   - Show decision output (`ELIGIBLE`) backed by the compiled AST Rule Engine breakdown.
4. **Document Intelligence & Upload**:
   - Upload Income Certificate PDF.
   - Show server magic bytes verification (`%PDF-`), SHA256 deduplication, and OCR entity extraction.
5. **Application Submission & State Machine**:
   - Submit application.
   - Show status transition `DRAFT` -> `READY_FOR_SUBMISSION` -> `SUBMISSION_PENDING` with outbox event generation.
6. **CSC Admin Console & Four-Eyes Governance**:
   - Login to `/admin` as Scheme Admin A. Create draft scheme version.
   - Login as Scheme Admin B to review diff and publish (demonstrating four-eyes authorization constraint).
7. **Realtime Notifications & Audit Log**:
   - Observe live WebSocket notification toast when application status changes.
   - View structured immutable audit log event stream.
