# Document Security

Status: v1.0 draft
Related: security-architecture.md, threat-model.md #1 #2 #5, ADR-005, database/data-dictionary.md (documents)

## 1. Storage

Document files live in S3-compatible object storage (ADR-005), never in
PostgreSQL. Each object's key is a non-guessable UUID-derived path, never
citizen-identifier-derived, never sequential. Buckets are private by
default with no public-read policy.

## 2. Access Control

Every document fetch is mediated by the API:
1. Client requests a document by `document_id`.
2. Service layer checks the requesting user owns the document (or holds a
   valid `agent_assist` consent for the owning citizen, or is staff with a
   documented business reason — case_notes reference).
3. API issues a short-lived (≤5 minute) pre-signed URL scoped to that
   single object.
4. Client fetches directly from object storage using the pre-signed URL.

No document is ever served via a long-lived or object-storage-native
public URL (threat-model.md #1, #2).

## 3. Upload Validation

- Allowed MIME types and max file size enforced before the file leaves
  the multipart parser.
- Files are scanned for malware before being persisted or handed to the
  OCR pipeline (threat-model.md #5).
- The OCR worker runs with a least-privilege IAM role limited to the
  specific bucket/prefix it needs — no broader storage or database access
  than required for its task.

## 4. Encryption

Server-side encryption at rest (KMS-managed keys) on the storage bucket;
in transit, TLS for both upload and pre-signed-URL download.

## 5. Retention & Deletion

Document retention follows retention-policy.md; on account
deletion/anonymization (pii-handling.md §4), associated document files are
deleted from object storage, not merely unlinked from the citizen's
profile.

## 6. Reuse Across Applications

A verified document can be attached to multiple applications
(`application_documents` join table) without re-upload (FR-DOCS-5) — this
reduces redundant PII exposure (fewer copies of the same document) compared
to a design that would otherwise require re-uploading per application.
