"""Document processing pipeline orchestrator (prompt §16, §27, §28, §30).

Sequence (all after upload):
    load bytes -> validate -> malware scan -> OCR -> classify -> extract ->
    normalize + confidence -> identity match (vs profile) -> conflict detect
    (vs profile facts) -> persist DocumentExtraction + DocumentExtractedField ->
    set document status (VERIFIED auto if all HIGH + identity match + no
    conflict, else VERIFICATION_REQUIRED).

Permanent vs transient errors: validation/scan/corrupt => PERMANENT (document
-> VALIDATION_FAILED/REJECTED, job not retried). OCR/extraction infra hiccups
=> transient (bounded retry). PII-safe: no document text in errors/logs.

The pipeline is a pure orchestration over the injected providers + repository,
so it is unit-testable and the worker just wires storage + a DB session in.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.document import (
    Document,
    DocumentExtractedField,
    DocumentExtraction,
)
from app.models.enums import (
    ConfidenceLevel,
    DocumentStatus,
    FactSource,
    FieldValueType,
    FieldVerificationStatus,
)
from app.modules.documents.processing.classifier import classify
from app.modules.documents.processing.confidence import clamp_confidence, level_for, requires_verification
from app.modules.documents.processing.extractor import DocumentExtractionProvider
from app.modules.documents.processing.normalizer import normalize_field
from app.modules.documents.processing.ocr import OCRProvider
from app.modules.documents.processing.scanner import MalwareScanner
from app.modules.documents.processing.validator import FileValidationError, validate_file

logger = get_logger("civiclens.documents.pipeline")

PERMANENT_ERROR_CODES = {
    "EMPTY_FILE", "FILE_TOO_LARGE", "UNSUPPORTED_TYPE", "MIME_MISMATCH",
    "CORRUPT_FILE", "TOO_MANY_PAGES", "IMAGE_TOO_LARGE", "MALWARE_DETECTED",
}

_VALUE_TYPE_PY = {
    FieldValueType.NUMBER: float,
    FieldValueType.INTEGER: int,
    FieldValueType.DATE: str,
    FieldValueType.BOOLEAN: bool,
    FieldValueType.STRING: str,
}


class PermanentProcessingError(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class TransientProcessingError(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class PipelineResult:
    document_id: uuid.UUID
    status: DocumentStatus
    extraction_id: uuid.UUID | None
    field_count: int
    identity_match: bool | None
    conflicts: list[dict] = field(default_factory=list)


class ProcessingPipeline:
    def __init__(
        self,
        session: Session,
        *,
        scanner: MalwareScanner,
        ocr: OCRProvider,
        extractor: DocumentExtractionProvider,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._scanner = scanner
        self._ocr = ocr
        self._extractor = extractor
        self._s = settings or get_settings()

    def process(self, document: Document, data: bytes) -> PipelineResult:
        # 1. Validation (permanent errors).
        try:
            validation = validate_file(data, declared_mime=document.mime_type, settings=self._s)
        except FileValidationError as exc:
            document.status = DocumentStatus.VALIDATION_FAILED
            self._session.flush()
            raise PermanentProcessingError(str(exc), code=exc.code) from exc

        # 2. Malware scan (permanent on detection).
        scan = self._scanner.scan(data)
        if not scan.clean:
            document.status = DocumentStatus.REJECTED
            self._session.flush()
            raise PermanentProcessingError("Malware detected.", code="MALWARE_DETECTED")

        document.status = DocumentStatus.PROCESSING
        self._session.flush()

        # 3. OCR (transient on infra failure).
        try:
            ocr_result = self._ocr.extract_text(data, validation.mime_type)
        except Exception as exc:
            raise TransientProcessingError("OCR failed.", code="OCR_FAILED") from exc

        # 4. Classification.
        classification = classify(ocr_result.full_text, declared_type=document.document_type)

        # 5. Extraction (typed, provenance, no fabrication).
        try:
            extraction_out = self._extractor.extract(classification.document_type, ocr_result)
        except Exception as exc:
            raise TransientProcessingError("Extraction failed.", code="EXTRACTION_FAILED") from exc

        # 6. Persist extraction + fields (normalize + confidence per field).
        extraction = DocumentExtraction(
            document_id=document.id,
            extracted_fields={},
            classified_type=classification.document_type,
            classification_confidence=Decimal(str(round(classification.confidence, 2))),
            ocr_provider=self._ocr.name,
            extraction_provider=self._extractor.name,
            model_version="test-1.0.0",
            page_count=len(ocr_result.pages),
        )
        self._session.add(extraction)
        self._session.flush()

        summary_fields: dict[str, object] = {}
        min_conf = 1.0
        any_field = False
        for f in extraction_out.fields:
            conf = clamp_confidence(f.confidence)
            if f.raw_value is None:
                # Absent field: persist as null-typed, low confidence. No fabrication.
                nv_norm = None
                vtype = FieldValueType.STRING
                verif = FieldVerificationStatus.VERIFICATION_REQUIRED
            else:
                any_field = True
                nv = normalize_field(f.field_name, f.raw_value)
                nv_norm = nv.normalized_value
                vtype = nv.value_type
                if not nv.ok:
                    conf = min(conf, 0.5)  # unnormalizable value is lower confidence
                verif = (
                    FieldVerificationStatus.AUTO_ACCEPTED
                    if not requires_verification(conf, self._s) and nv.ok
                    else FieldVerificationStatus.VERIFICATION_REQUIRED
                )
                min_conf = min(min_conf, conf)
            self._session.add(
                DocumentExtractedField(
                    extraction_id=extraction.id,
                    document_id=document.id,
                    field_name=f.field_name,
                    value_type=vtype,
                    raw_value=f.raw_value,
                    normalized_value=nv_norm,
                    confidence=Decimal(str(round(conf, 3))),
                    confidence_level=level_for(conf, self._s),
                    page_number=f.page_number,
                    text_span=f.text_span,
                    bounding_box=f.bounding_box,
                    source=FactSource.DOCUMENT_EXTRACTED,
                    verification_status=verif,
                )
            )
            if f.raw_value is not None and nv_norm is not None:
                summary_fields[f.field_name] = nv_norm

        # 7. Identity matching + conflict detection against the citizen profile.
        identity_match = self._identity_match(document, summary_fields)
        conflicts = self._detect_conflicts(document, summary_fields)

        extraction.extracted_fields = summary_fields
        extraction.identity_match = identity_match
        extraction.confidence = Decimal(str(round(min_conf if any_field else 0.0, 2)))
        extraction.conflicts = {"items": conflicts} if conflicts else None
        self._session.flush()

        # 8. Decide document status.
        auto_ok = (
            any_field
            and not requires_verification(min_conf, self._s)
            and identity_match is not False
            and not conflicts
        )
        document.status = DocumentStatus.VERIFIED if auto_ok else DocumentStatus.VERIFICATION_REQUIRED
        document.processed_at = datetime.now(timezone.utc)
        if document.status is DocumentStatus.VERIFIED:
            document.verified_at = datetime.now(timezone.utc)
        self._session.flush()

        return PipelineResult(
            document_id=document.id,
            status=document.status,
            extraction_id=extraction.id,
            field_count=len(extraction_out.fields),
            identity_match=identity_match,
            conflicts=conflicts,
        )

    # ------------------------------------------------------------------ #
    def _identity_match(self, document: Document, fields: dict) -> bool | None:
        """Compare extracted person_name against the citizen profile (best-effort).

        Returns None when there's nothing to compare (no extracted name and no
        profile name signal), True on a normalized match, False on mismatch.
        """
        extracted_name = fields.get("person_name")
        if not extracted_name:
            return None
        profile = document.profile
        # The profile has no explicit name column in this schema; identity match
        # is evaluated against any prior document names / occupation-free signal.
        # With no authoritative profile name, we cannot assert a mismatch -> None,
        # unless a previously VERIFIED document established a name.
        prior = self._prior_verified_name(document)
        if prior is None:
            return None
        return _norm_name(prior) == _norm_name(extracted_name)

    def _prior_verified_name(self, document: Document) -> str | None:
        from sqlalchemy import select

        from app.models.document import Document as Doc, DocumentExtraction as Ext

        stmt = (
            select(Ext.extracted_fields)
            .join(Doc, Ext.document_id == Doc.id)
            .where(
                Doc.citizen_profile_id == document.citizen_profile_id,
                Doc.id != document.id,
                Doc.status == DocumentStatus.VERIFIED,
            )
        )
        for (ef,) in self._session.execute(stmt).all():
            if ef and ef.get("person_name"):
                return ef["person_name"]
        return None

    def _detect_conflicts(self, document: Document, fields: dict) -> list[dict]:
        """Compare extracted facts vs. existing profile facts (prompt §28).

        Never overwrites the profile — records CONFLICTING_INFORMATION for a
        reviewer. Compares income (annual_income vs declared_annual_income) and
        state (vs primary address).
        """
        conflicts: list[dict] = []
        profile = document.profile

        if "annual_income" in fields and profile.declared_annual_income is not None:
            try:
                doc_income = float(fields["annual_income"])
                if abs(doc_income - float(profile.declared_annual_income)) > 0.5:
                    conflicts.append({
                        "field": "annual_income",
                        "profile_value": str(profile.declared_annual_income),
                        "document_value": str(fields["annual_income"]),
                    })
            except (TypeError, ValueError):
                pass

        if "state" in fields:
            primary = self._primary_address(document.citizen_profile_id)
            if primary is not None and primary.state:
                from app.modules.documents.processing.normalizer import normalize_state

                profile_state = normalize_state(primary.state).normalized_value
                if profile_state and profile_state != fields["state"]:
                    conflicts.append({
                        "field": "state",
                        "profile_value": profile_state,
                        "document_value": fields["state"],
                    })
        return conflicts

    def _primary_address(self, profile_id: uuid.UUID):
        from sqlalchemy import select

        from app.models.address import Address

        stmt = (
            select(Address)
            .where(Address.citizen_profile_id == profile_id)
            .order_by(Address.is_primary.desc(), Address.id)
        )
        return self._session.scalars(stmt).first()


def _norm_name(name: str) -> str:
    return " ".join((name or "").lower().split())
