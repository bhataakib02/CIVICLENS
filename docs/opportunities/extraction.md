# AI Extraction & Validation Engine

## Extraction Pipeline
1. **Raw Page Fetch**: Ingested content passed to `sanitize_external_text`.
2. **Security Filtering**: Prompt injection patterns (`ignore previous instructions`, `system prompt`) neutralized.
3. **Structured Schema Validation**: Parsed output validated against `OpportunityExtractionSchema` Pydantic model.
4. **Date Classification**: Distinguishes Published Date, Application Open Date, Application Deadline, Exam Date, Interview Date, Event Date. Never confuses exam date with deadline.
5. **Quality Scoring**: Assigns internal score; >= 0.75 auto-publishes, 0.50-0.74 routes to review queue, < 0.50 rejects.
