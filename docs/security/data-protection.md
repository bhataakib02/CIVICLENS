# Data Protection

Status: v1.0 draft
Related: pii-handling.md, security-architecture.md, database/database-design.md

## 1. Encryption at Rest

- PostgreSQL: encrypted storage volumes (cloud-provider managed disk
  encryption) plus column-level encryption for the highest-sensitivity
  PII fields (declared_annual_income, date_of_birth, profile snapshots,
  document_extractions.extracted_fields) using envelope encryption via a
  managed KMS.
- Object storage: server-side encryption (KMS-managed keys) on all
  document buckets.
- Backups: encrypted using the same key management as the source data;
  backup access is logged and restricted to the on-call/DBA role.

## 2. Encryption in Transit

TLS 1.2+ for all external traffic; internal service-to-service traffic
(API ↔ workers ↔ database) runs within a private VPC and still uses TLS
for defense in depth (infrastructure/networking.md).

## 3. Key Management

Managed KMS (cloud provider) for encryption keys and application secrets;
keys are rotated on a defined schedule; no encryption key ever lives in
source control or application config files (secrets-management.md).

## 4. Data Classification

| Class | Examples | Handling |
|---|---|---|
| Highly sensitive PII | DOB, income, documents, extracted fields | Column/file-level encryption, access-controlled, redacted from logs |
| Sensitive | phone, email, address | Encrypted, redacted from logs |
| Internal | eligibility_rules, scheme_versions | Access-controlled, not encrypted (not PII, but integrity-protected via versioning/audit) |
| Public | published scheme catalog content | No special protection needed |

## 5. Backup & Recovery

See operations/backup-restore.md for RPO/RTO targets (NFR-AVAIL-4) and the
encrypted-backup verification process.
