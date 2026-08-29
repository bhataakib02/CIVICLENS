# CivicLens — Privacy & Data Protection Model

This document outlines PII minimization, data flow boundaries, and privacy controls implemented in CivicLens.

---

## 1. PII Inventory & Retention

| Data Element | Storage Location | Access Policy | Retention Period | Third-Party Exposure |
|---|---|---|---|---|
| **Email / Phone / Credentials** | PostgreSQL `users` (Argon2id Hash) | Owner / System Auth | Account Lifetime | Opaque hash only |
| **Demographics / Income / DOB** | PostgreSQL `citizen_profiles` | Owner / Consented Agent | Account Lifetime | Evaluated locally in Rule Engine |
| **Documents (PDF / PNG)** | Private AWS S3 Bucket | Owner (Signed URLs) | Soft-delete + Object Purge | Sent to OCR processor locally |
| **Audit Logs** | PostgreSQL `audit_logs` | Admin / Auditor | 1 Year (Salted IP Hash) | Internal only |
| **RAG Queries** | PostgreSQL `pgvector` | Citizen Assistant Session | Ephemeral Context | Sent to LLM with PII Stripped |

---

## 2. External Data Minimization

> [!IMPORTANT]
> **Data Minimization Guarantee**: No citizen PII (such as name, Aadhaar, PAN, phone number, or raw income) is transmitted to external AI LLM providers or notification services unless explicitly necessary for notification delivery.

- **AI Assistant Queries**: Context passages from government documents are sent with `<untrusted_context>` tags. Private citizen facts are stripped from prompt inputs.
- **Log Scrubbing**: Logging middleware redacts sensitive dictionary keys (`password`, `access_token`, `refresh_token`, `aadhaar`, `pan`) with `[REDACTED]`.
