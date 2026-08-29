"""Development knowledge seed (prompt §37).

Creates CLEARLY FICTIONAL demo knowledge sources (CIVICLENS-DEMO-*) and runs
them through the REAL ingestion pipeline (parse -> normalize -> chunk -> embed
-> persist), so retrieval/assistant tests exercise the genuine path. The
content is explicitly labeled fictional and is NOT presented as real
government policy.

The demo sources are linked to the Prompt-2 CIVIC-DEMO schemes when present,
and marked verified/official-government FOR DEMO PURPOSES ONLY so they are
retrievable as authoritative evidence in local/dev.

Usage: python -m app.seeds.seed_knowledge
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_sessionmaker
from app.models.enums import SourceTrustLevel, VerificationStatus
from app.models.knowledge import KnowledgeSource
from app.models.scheme import Scheme, SchemeVersion
from app.modules.knowledge.embeddings.provider import get_embedding_provider
from app.modules.knowledge.ingestion.pipeline import IngestionPipeline

# Fictional demo documents. The FICTIONAL banner is deliberate.
_DEMO_DOCS = [
    {
        "code": "CIVICLENS-DEMO-001",
        "scheme_code": "CIVIC-DEMO-001",
        "title": "Demo Income Support — Guidance (FICTIONAL)",
        "url": "https://demo.civiclens.gov.in/income-support",
        "publisher": "CivicLens Demo Directorate (fictional)",
        "content": (
            "<h1>Demo Income Support Scheme</h1>"
            "<p>FICTIONAL DEMO CONTENT — not a real government scheme.</p>"
            "<h2>Benefits</h2><p>The scheme provides a monthly demo stipend to eligible residents.</p>"
            "<h2>Required Documents</h2>"
            "<ul><li>Income certificate</li><li>Proof of residence in the state</li>"
            "<li>Age proof (date of birth)</li></ul>"
            "<h2>Who administers it</h2><p>Administered by the CivicLens Demo Directorate.</p>"
            "<h2>Where to apply</h2><p>Applications are submitted on the demo state portal.</p>"
        ),
        "content_type": "text/html",
    },
    {
        "code": "CIVICLENS-DEMO-002",
        "scheme_code": "CIVIC-DEMO-002",
        "title": "Demo Unemployment Aid — Guidance (FICTIONAL)",
        "url": "https://demo.civiclens.gov.in/unemployment-aid",
        "publisher": "CivicLens Demo Directorate (fictional)",
        "content": (
            "<h1>Demo Unemployment Aid</h1>"
            "<p>FICTIONAL DEMO CONTENT — not a real government scheme.</p>"
            "<h2>Eligibility</h2><p>Open to unemployed adults aged eighteen or older.</p>"
            "<h2>Required Documents</h2><ul><li>Proof of unemployment status</li>"
            "<li>Age proof</li></ul>"
        ),
        "content_type": "text/html",
    },
]


def seed(session: Session) -> dict:
    embedder = get_embedding_provider()
    pipeline = IngestionPipeline(session, embedder=embedder)
    created: list[str] = []

    for doc in _DEMO_DOCS:
        scheme = session.scalar(select(Scheme).where(Scheme.code == doc["scheme_code"]))
        scheme_id = scheme.id if scheme else None
        scheme_version_id = None
        if scheme is not None:
            sv = session.scalars(
                select(SchemeVersion).where(SchemeVersion.scheme_id == scheme.id)
            ).first()
            scheme_version_id = sv.id if sv else None

        # Skip if this URL's content was already ingested (idempotent).
        from app.modules.knowledge.ingestion.metadata import content_hash

        chash = content_hash(doc["content"])
        existing = session.scalar(
            select(KnowledgeSource).where(KnowledgeSource.content_hash == chash)
        )
        if existing is not None:
            source = existing
        else:
            outcome = pipeline.ingest(
                title=doc["title"],
                url=doc["url"],
                publisher=doc["publisher"],
                content=doc["content"].encode("utf-8"),
                content_type=doc["content_type"],
                scheme_id=scheme_id,
                scheme_version_id=scheme_version_id,
            )
            source = session.get(KnowledgeSource, outcome.source_id)

        # Mark verified + official FOR DEMO so retrieval can surface it.
        source.verification_status = VerificationStatus.VERIFIED
        source.trust_level = SourceTrustLevel.OFFICIAL_GOVERNMENT
        source.last_verified_at = datetime.now(timezone.utc)
        session.flush()
        created.append(str(source.id))

    session.commit()
    return {"source_ids": created}


def main() -> None:
    session = get_sessionmaker()()
    try:
        print("Seeded knowledge:", seed(session))
    finally:
        session.close()


if __name__ == "__main__":
    main()
