# CivicLens — Known Technical Limitations

This document provides a transparent, honest record of technical boundaries and provider dependencies in CivicLens.

---

## Known Technical Limitations & Dependencies

1. **Third-Party SMS/Email Gateways**:
   - Production integration relies on mock providers (`MockSMSProvider`) during local/staging execution. Live delivery requires configuring production vendor credentials (Twilio / Kaleyra).
2. **AWS Cloud Infrastructure Verification**:
   - Complete Terraform infrastructure manifests (`infrastructure/terraform/`) are fully declared for VPC, ECS, RDS PostgreSQL, Redis, and S3. Live provisioning is marked as `PROVIDER-DEPENDENT / NOT VERIFIED` in local dev.
3. **OCR Multilingual Coverage**:
   - Current Tesseract OCR parsing is optimized for English and Bengali document structures. Additional language packs (Hindi, Tamil) require worker image language data expansion.
4. **Single-Node Rate Limiting Fallback**:
   - If Redis is unavailable, rate limiting falls back to single-node in-memory storage with warning logs. Horizontally scaled deployments require Redis.
