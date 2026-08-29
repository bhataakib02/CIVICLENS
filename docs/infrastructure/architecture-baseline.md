# CivicLens Production Architecture & Delivery Baseline

This document describes the production deployment topology, environment model, disaster recovery targets, and database migration safety guidelines for CivicLens.

---

## 1. Environment Model

CivicLens maintains four distinct environments:

| Environment | Purpose | Database | Redis | Storage | Provider Config |
|---|---|---|---|---|---|
| **development** | Local developer iteration | Docker Postgres+pgvector | Docker Redis | Local filesystem | `test` / `mock` providers |
| **test** | Automated CI pipeline | Ephemeral Postgres (`pgserver`) | Local Redis | Local filesystem | `test` / `mock` providers |
| **staging** | Staging & synthetic E2E testing | Private RDS Postgres | ElastiCache Redis | Private S3 Bucket | Staging API integration |
| **production** | Live public production | Multi-AZ RDS Postgres | Multi-AZ ElastiCache | Private S3 Bucket | Production Govt Providers |

> [!CAUTION]
> Development or test providers (`OTP_PROVIDER=test`, `SUBMISSION_PROVIDER=mock`, `OCR_PROVIDER=test`) are **STRICTLY PROHIBITED** in production and will cause startup failure via `validate_production_config()`.

---

## 2. Disaster Recovery Targets (DR)

- **Recovery Point Objective (RPO)**: $\le 5\text{ minutes}$ (Automated RDS continuous backups + transaction log archiving).
- **Recovery Time Objective (RTO)**: $\le 30\text{ minutes}$ (Multi-AZ automated failover + infrastructure as code).

---

## 3. Database Migration Deployment Policy

To ensure zero-downtime deployment:
1. Database schema migrations run as an explicit pre-deployment job (`alembic upgrade head`) before shifting API container traffic.
2. Migrations must follow **Expand / Contract** discipline:
   - **Phase 1 (Expand)**: Add new columns/tables as nullable or with default values.
   - **Phase 2 (Deploy Code)**: Deploy new API code reading/writing new columns.
   - **Phase 3 (Contract)**: Drop old unused columns in a subsequent release.
