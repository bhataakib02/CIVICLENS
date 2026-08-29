# CivicLens — Known Limitations Document

This document lists all known operational and architectural limitations of the CivicLens v1.0.0-rc.1 release candidate.

---

## 1. Technical Limitations
- **In-Memory Rate Limiting Fallback**: When Redis is unavailable, rate limits fall back to in-process memory. In multi-instance deployments without sticky sessions, this allows slightly higher burst request rates.
- **Local File Storage in Dev**: Default local storage provider stores encrypted document uploads in `.document_storage`. Production deployments must switch `STORAGE_PROVIDER` to `s3`.

## 2. Provider Limitations
- **Mock SMS/Email Gateway**: In default development mode, OTP and notifications are output to logs/outbox table rather than dispatched to real carrier networks until production credentials (Twilio/SendGrid) are set.
- **LLM Rate Limits**: High-throughput automated RAG queries may hit provider API rate limits; worker exponential backoff handles retries gracefully.

## 3. Product Limitations
- **Authoritative Rule Engine Scope**: Scheme eligibility relies strictly on structured JSON rules (comparisons, set membership, ranges). Rules requiring arbitrary unstructured logic must be modeled through standard AST comparison operators.

## 4. Deployment Limitations
- **Terraform Cloud Provisioning**: Full automated cloud infrastructure deployment requires valid cloud provider API keys and credentials configured in CI/CD secrets.
