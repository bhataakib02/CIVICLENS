"""Enumerations shared across models, matching data-dictionary.md."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """users.role — data-dictionary.md enum(citizen, agent, scheme_admin, admin)."""

    CITIZEN = "citizen"
    AGENT = "agent"
    SCHEME_ADMIN = "scheme_admin"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    """Account lifecycle status.

    DOCUMENTED EXTENSION: the data-dictionary users table has no status column.
    Added to support account suspension (FR-AUTH adjacent / security-model:
    a suspended account must be denied login and token use). Recorded in the
    implementation report and the Alembic migration docstring.
    """

    ACTIVE = "active"
    SUSPENDED = "suspended"


class AddressType(str, enum.Enum):
    """addresses.type — data-dictionary.md enum(permanent, current)."""

    PERMANENT = "permanent"
    CURRENT = "current"


class SchemeScope(str, enum.Enum):
    """schemes.scope — data-dictionary.md enum(central, state)."""

    CENTRAL = "central"
    STATE = "state"


class SchemeVersionStatus(str, enum.Enum):
    """scheme_versions.status — data-dictionary.md enum.

    Lifecycle: draft -> in_review -> published -> superseded; archived is a
    terminal state for versions retired without ever superseding. The prompt's
    DRAFT/ACTIVE/SUPERSEDED map onto draft/published/superseded ("activate" ==
    publish). Legal transitions are enforced in the schemes service.
    """

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class EligibilityResult(str, enum.Enum):
    """eligibility_checks.result — data-dictionary.md / openapi EligibilityResult."""

    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    LIKELY_ELIGIBLE = "likely_eligible"
    INSUFFICIENT_DATA = "insufficient_data"


class SourceType(str, enum.Enum):
    """knowledge_sources.source_type — how the source was published.

    DOCUMENTED EXTENSION: data-dictionary knowledge_sources has no source_type
    column; added per prompt §4. Recorded in the migration docstring.
    """

    HTML = "html"
    PDF = "pdf"
    TEXT = "text"


class SourceTrustLevel(str, enum.Enum):
    """knowledge_sources.trust_level — authoritativeness (prompt §5, source-policy.md).

    Only OFFICIAL_* and VERIFIED_SECONDARY are eligible for authoritative
    answers; UNVERIFIED sources are retrievable only for admin review, never
    surfaced as authoritative evidence.
    """

    OFFICIAL_GOVERNMENT = "official_government"
    OFFICIAL_DOCUMENT = "official_document"
    OFFICIAL_PORTAL = "official_portal"
    VERIFIED_SECONDARY = "verified_secondary"
    UNVERIFIED = "unverified"


class VerificationStatus(str, enum.Enum):
    """knowledge_sources.verification_status — data-dictionary uses
    ingestion_status(pending, ingested, failed, stale); this models the
    *verification* lifecycle distinct from *processing* (prompt §31).
    Processing state lives on ingestion_jobs.status.
    """

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    STALE = "stale"


class IngestionJobStatus(str, enum.Enum):
    """ingestion_jobs.status — async processing lifecycle (prompt §31, ADR-006)."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    """documents.document_type.

    Data-dictionary defines: aadhaar, income_certificate, residence_proof,
    caste_certificate, disability_certificate, other. Extended (documented) with
    the classifier's target set (identity/education/employment/land/bank) needed
    by prompt §21. `aadhaar` is retained (data-dictionary) as an identity subtype.
    """

    AADHAAR = "aadhaar"
    IDENTITY_DOCUMENT = "identity_document"
    INCOME_CERTIFICATE = "income_certificate"
    RESIDENCE_PROOF = "residence_proof"
    CASTE_CERTIFICATE = "caste_certificate"
    DISABILITY_CERTIFICATE = "disability_certificate"
    EDUCATION_CERTIFICATE = "education_certificate"
    EMPLOYMENT_CERTIFICATE = "employment_certificate"
    LAND_RECORD = "land_record"
    BANK_DOCUMENT = "bank_document"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    """documents.status — explicit document lifecycle (prompt §4, §41).

    DOCUMENTED EXTENSION: the data-dictionary enum is
    (uploaded, processing, verified, rejected). Extended to model the full
    lifecycle. The original four values are retained so existing contract
    consumers keep working. This is the DOCUMENT-level status; processing-job
    state lives on document_processing_jobs.status (kept separate, §41).
    """

    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VERIFICATION_REQUIRED = "verification_required"
    VERIFIED = "verified"
    VALIDATION_FAILED = "validation_failed"
    PROCESSING_FAILED = "processing_failed"
    REJECTED = "rejected"


class ProcessingJobStatus(str, enum.Enum):
    """document_processing_jobs.status — async processing (prompt §17, §41)."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfidenceLevel(str, enum.Enum):
    """Bucketed confidence (prompt §24). Thresholds are configurable."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FactSource(str, enum.Enum):
    """Provenance/priority of a fact (prompt §29)."""

    USER_PROVIDED = "user_provided"
    DOCUMENT_EXTRACTED = "document_extracted"
    OFFICIAL_SOURCE = "official_source"
    SYSTEM_DERIVED = "system_derived"


class FieldValueType(str, enum.Enum):
    """Typed value kind for an extracted field (prompt §40)."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    DATE = "date"
    BOOLEAN = "boolean"


class FieldVerificationStatus(str, enum.Enum):
    """Per-field / per-document verification outcome (prompt §30)."""

    AUTO_ACCEPTED = "auto_accepted"
    VERIFICATION_REQUIRED = "verification_required"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class ApplicationStatus(str, enum.Enum):
    """applications.status — full case-management lifecycle (prompt §5).

    Data-dictionary/contract base enum was
    (draft, submitted, under_review, info_requested, approved, rejected,
    withdrawn). DOCUMENTED EXTENSION: adds ready_for_submission, action_required
    (the workflow name for info_requested), completed, submission_pending,
    submission_failed. `info_requested` is retained for contract compatibility;
    the workflow uses `action_required` as its canonical name and both map to
    the same review state. Transitions are enforced by state_machine.py.
    """

    DRAFT = "draft"
    READY_FOR_SUBMISSION = "ready_for_submission"
    SUBMISSION_PENDING = "submission_pending"
    SUBMISSION_FAILED = "submission_failed"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACTION_REQUIRED = "action_required"
    INFO_REQUESTED = "info_requested"  # retained (contract alias of action_required)
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    COMPLETED = "completed"


class SubmissionStatus(str, enum.Enum):
    """application_submissions.status."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class SubmissionMethod(str, enum.Enum):
    """How the application was submitted to the government."""

    MOCK = "mock"          # NON-PRODUCTION test/dev provider
    PORTAL_API = "portal_api"
    MANUAL_EXPORT = "manual_export"


class ReviewAction(str, enum.Enum):
    """Reviewer decision (prompt §24)."""

    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_ACTION = "request_action"


class AssignmentAction(str, enum.Enum):
    ASSIGN = "assign"
    UNASSIGN = "unassign"
    REASSIGN = "reassign"


class ActionRequiredStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ChecklistItemStatus(str, enum.Enum):
    """Document-requirement readiness per item (prompt §14)."""

    MISSING = "MISSING"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class NotificationChannel(str, enum.Enum):
    """notifications.channel — data-dictionary enum(sms, email, in_app).

    DOCUMENTED EXTENSION (prompt §11): `push` added for the push provider
    abstraction. in_app remains the always-available channel.
    """

    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationCategory(str, enum.Enum):
    """notifications.category — data-dictionary enum + application events."""

    SCHEME_MATCH = "scheme_match"
    STATUS_CHANGE = "status_change"
    DOC_REVERIFICATION = "doc_reverification"
    DEADLINE_REMINDER = "deadline_reminder"


class NotificationStatus(str, enum.Enum):
    """notifications.status — delivery lifecycle (prompt §10).

    DOCUMENTED EXTENSION: the data-dictionary enum is (queued, sent, failed).
    Extended to the full delivery lifecycle. SENT (provider accepted) is kept
    DISTINCT from DELIVERED (provider confirmed receipt) — a console/dev
    provider only ever reaches SENT, never DELIVERED (prompt §54). The original
    three values are retained for contract compatibility.
    """

    QUEUED = "queued"
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, enum.Enum):
    """notifications.priority — ordering/urgency hint (prompt §10)."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DomainEventType(str, enum.Enum):
    """Typed domain event types (prompt §4). Never use bare strings for these."""

    APPLICATION_CREATED = "APPLICATION_CREATED"
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    APPLICATION_STATUS_CHANGED = "APPLICATION_STATUS_CHANGED"
    APPLICATION_ACTION_REQUIRED = "APPLICATION_ACTION_REQUIRED"
    APPLICATION_APPROVED = "APPLICATION_APPROVED"
    APPLICATION_REJECTED = "APPLICATION_REJECTED"
    APPLICATION_COMPLETED = "APPLICATION_COMPLETED"
    APPLICATION_WITHDRAWN = "APPLICATION_WITHDRAWN"

    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_PROCESSING_COMPLETED = "DOCUMENT_PROCESSING_COMPLETED"
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    DOCUMENT_VERIFICATION_REQUIRED = "DOCUMENT_VERIFICATION_REQUIRED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"

    ELIGIBILITY_CHECK_COMPLETED = "ELIGIBILITY_CHECK_COMPLETED"

    SCHEME_VERSION_ACTIVATED = "SCHEME_VERSION_ACTIVATED"

    OPPORTUNITY_PUBLISHED = "OPPORTUNITY_PUBLISHED"
    OPPORTUNITY_UPDATED = "OPPORTUNITY_UPDATED"


class DeliveryErrorCode(str, enum.Enum):
    """Structured provider delivery error codes (prompt §12, §31).

    Retryable errors (transient) vs permanent errors are classified in
    delivery.py; permanent errors must NOT retry indefinitely.
    """

    # transient / retryable
    TRANSIENT_PROVIDER_ERROR = "TRANSIENT_PROVIDER_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    # permanent / non-retryable
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PHONE = "INVALID_PHONE"
    UNSUPPORTED_CHANNEL = "UNSUPPORTED_CHANNEL"
    RECIPIENT_OPTED_OUT = "RECIPIENT_OPTED_OUT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"


class PreferredLanguage(str, enum.Enum):
    """citizen_profiles.preferred_language (prompt §26, §27). English is the
    default + fallback; bn/hi are prepared for."""

    EN = "en"
    BN = "bn"
    HI = "hi"


class OutboxStatus(str, enum.Enum):
    """outbox_events.status — transactional outbox (prompt §37).

    DOCUMENTED EXTENSION: PROCESSING added for the claim step so a worker can
    mark an event in-flight; DEAD_LETTER marks events that exhausted retries
    (prompt §32).
    """

    PENDING = "pending"
    PROCESSING = "processing"
    DISPATCHED = "dispatched"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class OpportunityType(str, enum.Enum):
    """Opportunity kinds supported across government and private sectors."""

    JOB = "JOB"
    INTERNSHIP = "INTERNSHIP"
    APPRENTICESHIP = "APPRENTICESHIP"
    SCHOLARSHIP = "SCHOLARSHIP"
    FELLOWSHIP = "FELLOWSHIP"
    GOVERNMENT_SCHEME = "GOVERNMENT_SCHEME"
    GRANT = "GRANT"
    TRAINING = "TRAINING"
    SKILL_PROGRAM = "SKILL_PROGRAM"
    JOB_FAIR = "JOB_FAIR"
    COMPETITION = "COMPETITION"
    ADMISSION = "ADMISSION"
    OTHER = "OTHER"


class OpportunitySourceType(str, enum.Enum):
    """Source organization type for opportunities."""

    CENTRAL_GOVERNMENT = "CENTRAL_GOVERNMENT"
    STATE_GOVERNMENT = "STATE_GOVERNMENT"
    PUBLIC_INSTITUTION = "PUBLIC_INSTITUTION"
    UNIVERSITY = "UNIVERSITY"
    PSU = "PSU"
    PRIVATE_COMPANY = "PRIVATE_COMPANY"
    NGO = "NGO"
    FOUNDATION = "FOUNDATION"
    EDUCATIONAL_INSTITUTION = "EDUCATIONAL_INSTITUTION"
    OTHER = "OTHER"


class OpportunityAuthorityLevel(str, enum.Enum):
    """Authority and trust tier of opportunity sources."""

    OFFICIAL = "OFFICIAL"
    VERIFIED_PARTNER = "VERIFIED_PARTNER"
    KNOWN_PRIVATE = "KNOWN_PRIVATE"
    UNVERIFIED = "UNVERIFIED"


class OpportunityDeadlineStatus(str, enum.Enum):
    """Calculated urgency and deadline status."""

    UPCOMING = "UPCOMING"
    OPEN = "OPEN"
    CLOSING_SOON = "CLOSING_SOON"
    CLOSED = "CLOSED"
    DATE_UNKNOWN = "DATE_UNKNOWN"


class OpportunityLinkType(str, enum.Enum):
    """Classification of links on opportunity pages."""

    NOTIFICATION = "NOTIFICATION"
    APPLY = "APPLY"
    REGISTRATION = "REGISTRATION"
    LOGIN = "LOGIN"
    DOWNLOAD = "DOWNLOAD"
    RESULT = "RESULT"
    SYLLABUS = "SYLLABUS"


class OpportunityApplicationStatus(str, enum.Enum):
    """External application tracking state recorded by citizens."""

    NOT_APPLIED = "NOT_APPLIED"
    APPLIED = "APPLIED"
    INTERVIEW = "INTERVIEW"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class OpportunitySourceLifecycleState(str, enum.Enum):
    """Explicit lifecycle states for opportunity sources (Phase 2 requirement)."""

    DISCOVERED = "DISCOVERED"
    VALIDATING = "VALIDATING"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    RETIRED = "RETIRED"


