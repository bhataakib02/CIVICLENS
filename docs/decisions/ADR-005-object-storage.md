# ADR-005: Object Storage for Documents, Not Database BLOBs

Status: Accepted
Date: 2026-08-29
Related: database/database-design.md, security/document-security.md, infrastructure/aws-architecture.md

## Context

Citizens upload identity/income/residence documents (images, PDFs). These
need durable, access-controlled storage, must not bloat the primary
transactional database, and must support serving via short-lived
authenticated URLs rather than being routed through the API for every byte.

## Decision

Store uploaded document files in S3-compatible object storage. The
`documents` table stores only a non-guessable `storage_key` and metadata;
the file bytes never live in PostgreSQL. Access is always mediated by the
API, which issues short-lived pre-signed URLs after an authorization check
— objects are never public or predictably keyed (see threat-model.md #1,
#2).

## Consequences

- Positive: database stays lean and fast for transactional workloads;
  storage scales independently and cheaply.
- Positive: fine-grained, per-request authorization on document access,
  addressing cross-user access risk directly at the architecture level.
- Negative: an additional system to configure for encryption-at-rest,
  bucket policy, and lifecycle rules (retention/deletion) — mitigated
  by using managed cloud object storage with these as first-class
  features rather than self-hosting.

## Alternatives Considered

- **Database BLOB storage**: rejected — poor fit for large binary files at
  scale, complicates backup/restore and read-replica sizing.
- **Public CDN-served files**: rejected outright — documents are
  high-sensitivity PII; nothing citizen-uploaded is ever served from a
  public or predictable URL.
