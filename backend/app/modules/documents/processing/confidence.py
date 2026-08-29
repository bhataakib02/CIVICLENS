"""Confidence scoring/thresholds (prompt §24).

Buckets a provider/model confidence in [0,1] into HIGH/MEDIUM/LOW using
configurable thresholds. NOTE: confidence is provider/model-reported and is NOT
assumed to be calibrated across providers — it is a routing signal for human
verification, not a probability guarantee.
"""
from __future__ import annotations

from app.core.config import Settings, get_settings
from app.models.enums import ConfidenceLevel


def clamp_confidence(value: float) -> float:
    """Force any provider score into [0,1]."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, v))


def level_for(confidence: float, settings: Settings | None = None) -> ConfidenceLevel:
    settings = settings or get_settings()
    c = clamp_confidence(confidence)
    if c >= settings.document_confidence_high:
        return ConfidenceLevel.HIGH
    if c >= settings.document_confidence_medium:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def requires_verification(confidence: float, settings: Settings | None = None) -> bool:
    """A field below the HIGH threshold requires human verification."""
    settings = settings or get_settings()
    return clamp_confidence(confidence) < settings.document_confidence_high
