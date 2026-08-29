"""Document field extraction and classification helpers.

Re-exports the canonical document processing subsystem used by
``workers/ocr``. This module provides document type classification, OCR
orchestration, field extraction, and confidence scoring.

See ``docs/ai/entity-extraction.md`` and ``docs/ai/classification.md``.
"""

from app.modules.documents.processing.classifier import (
    ClassificationResult,
    classify as classify_document,
)
from app.modules.documents.processing.confidence import (
    clamp_confidence,
    level_for,
    requires_verification,
)
from app.modules.documents.processing.extractor import (
    get_extraction_provider,
)
from app.modules.documents.processing.normalizer import (
    NormalizedValue,
    normalize_field,
)
from app.modules.documents.processing.ocr import (
    get_ocr_provider,
)
from app.modules.documents.processing.pipeline import (
    PermanentProcessingError,
    ProcessingPipeline,
    TransientProcessingError,
)
from app.modules.documents.processing.scanner import (
    get_malware_scanner,
)
from app.modules.documents.processing.validator import (
    FileValidationError,
    ValidationResult,
    validate_file,
)

__all__ = [
    # Classification
    "ClassificationResult",
    "classify_document",
    # Confidence
    "clamp_confidence",
    "level_for",
    "requires_verification",
    # Extraction
    "get_extraction_provider",
    # Normalization
    "NormalizedValue",
    "normalize_field",
    # OCR
    "get_ocr_provider",
    # Pipeline
    "ProcessingPipeline",
    "PermanentProcessingError",
    "TransientProcessingError",
    # Security & Validation
    "get_malware_scanner",
    "validate_file",
    "FileValidationError",
    "ValidationResult",
]
