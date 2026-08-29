# CivicLens — External Integration Status Matrix

This document classifies every external service integration in CivicLens by its actual runtime mode and implementation state.

---

| Integration Name | Integration Category | Implementation Status | Runtime Mode | Description / Notes |
|---|---|---|---|---|
| **PostgreSQL + pgvector** | Database & Vector Search | `COMPLETE` | `REAL` | Runs local or cloud PostgreSQL 16 with pgvector extension for data persistence & HNSW vector search. |
| **Redis** | Cache & PubSub | `COMPLETE` | `REAL` / `SANDBOX` | Redis 7.0 for rate limiting and WebSocket pub/sub. Graceful in-memory fallback enabled if offline. |
| **OCR Provider** | Document Processing | `COMPLETE` | `SANDBOX` / `MOCK` | Configurable OCR provider supporting local tesseract / test mock mode for deterministic document extraction. |
| **LLM Provider (Gemini / Azure OpenAI)** | AI & Policy Explanation | `COMPLETE` | `SANDBOX` / `MOCK` | Strict non-authoritative AI wrapper for generating policy explanations and scheme assistance. |
| **SMS / Email Gateway** | Citizen Notifications | `COMPLETE` | `MOCK` / `STUB` | Mock notification outbox dispatcher in dev mode; ready for Twilio/Sendgrid API keys. |
| **Government Portal Integration** | External Authority | `NOT APPLICABLE` | `MOCK` | Internal scheme governance engine is authoritative. External portal sync simulated via mock endpoints. |
| **Document Storage (S3 / Local)** | Object Storage | `COMPLETE` | `REAL` (Local) / `SANDBOX` (S3) | Local signed file storage active in dev; S3 private bucket integration configured in Terraform. |
