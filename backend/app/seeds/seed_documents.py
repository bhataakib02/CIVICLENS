"""Development document fixtures (prompt §53).

Creates CLEARLY FICTIONAL demo documents for a demo citizen and runs them
through the REAL upload + processing pipeline (local storage + test providers),
so document flows can be exercised in dev. NO real identity documents, Aadhaar,
PAN, bank statements, or certificates are used — all content is synthetic and
labeled fictional.

Usage: python -m app.seeds.seed_documents
"""
from __future__ import annotations

import struct
import uuid
import zlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_sessionmaker
from app.models.citizen_profile import CitizenProfile
from app.models.document import Document, DocumentProcessingJob
from app.models.enums import DocumentStatus, DocumentType, ProcessingJobStatus, UserRole, UserStatus
from app.models.user import User
from app.modules.documents.processing.ocr import make_test_image_with_ocr_text
from app.modules.documents.storage import generate_storage_key, get_storage_provider
from app.modules.documents.worker import run_job

DEMO_EMAIL = "demo.docs@example.com"
DEMO_PASSWORD = "CivicDemoPass123!"

_INCOME_OCR = (
    "INCOME CERTIFICATE (FICTIONAL DEMO — not a real document)\n"
    "Name: Demo Citizen\n"
    "Annual Income: Rs 2,00,000\n"
    "Financial Year: 2025-2026\n"
    "Issuing Authority: Demo Tehsildar Office\n"
    "Certificate Number: CIVICLENS-DEMO-DOC-001\n"
    "State: West Bengal"
)


def _png_1x1() -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = b"IHDR" + struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_c = struct.pack(">I", len(ihdr) - 4) + ihdr + struct.pack(">I", zlib.crc32(ihdr) & 0xFFFFFFFF)
    idat_raw = b"IDAT" + zlib.compress(b"\x00\x00\x00\x00")
    idat = struct.pack(">I", len(idat_raw) - 4) + idat_raw + struct.pack(">I", zlib.crc32(idat_raw) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    return sig + ihdr_c + idat + iend


def seed(session: Session) -> dict:
    from app.core.security import hash_password

    user = session.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
                    role=UserRole.CITIZEN, status=UserStatus.ACTIVE)
        user.profile = CitizenProfile(current_version_no=1, declared_annual_income=200000)
        session.add(user)
        session.flush()
    profile = user.profile

    storage = get_storage_provider()
    document_id = uuid.uuid4()
    key = generate_storage_key(citizen_profile_id=profile.id, document_id=document_id, ext="png")
    image = make_test_image_with_ocr_text(_png_1x1(), _INCOME_OCR)
    storage.put_object(key, image, "image/png")

    doc = session.get(Document, document_id)
    if doc is None:
        doc = Document(
            id=document_id, citizen_profile_id=profile.id, uploaded_by=user.id,
            document_type=DocumentType.INCOME_CERTIFICATE, status=DocumentStatus.UPLOADED,
            storage_key=key, filename="demo_income.png", mime_type="image/png",
            size_bytes=len(image),
        )
        session.add(doc)
        job = DocumentProcessingJob(document_id=doc.id, status=ProcessingJobStatus.PENDING)
        session.add(job)
        session.flush()
        job_id = job.id
        session.commit()
        run_job(job_id)  # process synchronously for the seed

    session.commit()
    return {"document_id": str(document_id), "demo_email": DEMO_EMAIL}


def main() -> None:
    session = get_sessionmaker()()
    try:
        print("Seeded documents:", seed(session))
    finally:
        session.close()


if __name__ == "__main__":
    main()
