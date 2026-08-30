"""Domain event types + the typed event envelope (prompt §4, §5, §35).

An EventEnvelope is the canonical shape written to the outbox and read by the
worker. It carries identity, causality (correlation/causation), ordering
(occurred_at + per-aggregate sequence_no) and a schema_version so payloads can
evolve without breaking old events.

Payloads MUST be PII-free (ids + status + non-sensitive references only).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.enums import DomainEventType

# Current envelope/payload schema version. Bump when a payload shape changes;
# handlers branch on schema_version (prompt §35).
CURRENT_SCHEMA_VERSION = 1


class AggregateType:
    APPLICATION = "APPLICATION"
    DOCUMENT = "DOCUMENT"
    ELIGIBILITY = "ELIGIBILITY"
    SCHEME_VERSION = "SCHEME_VERSION"
    OPPORTUNITY = "OPPORTUNITY"


def _clean_payload(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _clean_payload(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_payload(x) for x in obj]
    return obj


@dataclass
class EventEnvelope:
    """In-memory representation of a domain event (prompt §5)."""

    event_type: DomainEventType
    aggregate_type: str
    aggregate_id: uuid.UUID
    payload: dict = field(default_factory=dict)
    actor_id: uuid.UUID | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    schema_version: int = CURRENT_SCHEMA_VERSION
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_row_kwargs(self) -> dict:
        return {
            "id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "actor_id": self.actor_id,
            "payload": _clean_payload(self.payload),
            "schema_version": self.schema_version,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "occurred_at": self.occurred_at,
        }




def parse_event_type(value: str) -> DomainEventType:
    """Parse a stored event_type string into the typed enum (tolerant of legacy
    aliases used before Phase 6)."""
    _ALIASES = {
        "ACTION_REQUIRED": DomainEventType.APPLICATION_ACTION_REQUIRED,
    }
    if value in _ALIASES:
        return _ALIASES[value]
    return DomainEventType(value)
