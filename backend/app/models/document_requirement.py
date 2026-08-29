"""Document requirement model — matches data-dictionary.md `document_requirements`.

Defines which document types a scheme_version requires (prompt §11: requirements
originate from scheme configuration, never hardcoded in application code).
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk
from app.models.enums import DocumentType

if TYPE_CHECKING:
    from app.models.scheme import SchemeVersion


class DocumentRequirement(Base):
    __tablename__ = "document_requirements"

    id: Mapped[uuid.UUID] = uuid_pk()
    scheme_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scheme_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(
            DocumentType,
            name="document_type",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum: [m.value for m in enum],
        ),
        nullable=False,
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    scheme_version: Mapped["SchemeVersion"] = relationship()
