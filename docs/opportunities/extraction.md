# AI Extraction & Validation Engine

## Extraction Pipeline
1. **Raw Page Fetch**: Ingested content passed to `sanitize_external_text`.
2. **Security Filtering**: Prompt injection patterns (`ignore previous instructions`, `system prompt`) neutralized.
3. **Structured Schema Validation**: Parsed output validated against `OpportunityExtractionSchema` Pydantic model.
4. **Date Classification**: Distinguishes Published Date, Application Open Date, Application Deadline, Exam Date, Interview Date, Event Date. Never confuses exam date with deadline.
5. **Tiered Quality Scoring**: Assigns internal quality score (0.0 to 1.0); applies stricter cutoff (0.85) for `OFFICIAL` government sources and `GOVERNMENT_SCHEME` postings vs 0.75 for private sources. High confidence -> `AUTO_PUBLISH` (emits `OPPORTUNITY_PUBLISHED` outbox event), medium (0.50–0.84/0.74) -> `REVIEW_QUEUE`, low (< 0.50) -> `REJECT`.

