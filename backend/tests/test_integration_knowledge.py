"""Integration tests: ingestion pipeline, hybrid retrieval, knowledge search
API, ingestion jobs (real PostgreSQL + pgvector + FTS). Prompt §35."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"

DEMO_HTML = (
    "<h1>Demo Income Support</h1>"
    "<p>FICTIONAL DEMO. The scheme provides a monthly stipend.</p>"
    "<h2>Required Documents</h2><ul><li>Income certificate</li><li>Age proof</li></ul>"
)


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _promote(db_session_factory, email, role):
    from app.models.enums import UserRole
    from app.models.user import User

    with db_session_factory() as s:
        u = s.scalar(select(User).where(User.email == email))
        u.role = UserRole(role)
        s.commit()


def _admin_token(client, db_session_factory, email="kadmin@example.com"):
    _register(client, email)
    _promote(db_session_factory, email, "scheme_admin")
    return client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _ingest(session, *, content=DEMO_HTML, url="https://demo.gov.in/x", ctype="text/html",
            verified=True, scheme_id=None, scheme_version_id=None):
    """Run the real pipeline and (optionally) mark the source verified/official."""
    from app.models.enums import SourceTrustLevel, VerificationStatus
    from app.models.knowledge import KnowledgeSource
    from app.modules.knowledge.embeddings.provider import DeterministicTestEmbeddingProvider
    from app.modules.knowledge.ingestion.pipeline import IngestionPipeline

    pipe = IngestionPipeline(session, embedder=DeterministicTestEmbeddingProvider(1536))
    outcome = pipe.ingest(
        title="Demo", url=url, publisher="Demo Directorate",
        content=content.encode("utf-8"), content_type=ctype,
        scheme_id=scheme_id, scheme_version_id=scheme_version_id,
    )
    if verified:
        src = session.get(KnowledgeSource, outcome.source_id)
        src.verification_status = VerificationStatus.VERIFIED
        src.trust_level = SourceTrustLevel.OFFICIAL_GOVERNMENT
    session.commit()
    return outcome


# ------------------------------ ingestion ----------------------------------- #
def test_ingestion_creates_source_and_chunks_with_embeddings(client, db_session_factory):
    with db_session_factory() as s:
        outcome = _ingest(s, verified=False)
    from app.models.knowledge import KnowledgeChunk

    with db_session_factory() as s:
        chunks = s.scalars(
            select(KnowledgeChunk).where(KnowledgeChunk.knowledge_source_id == outcome.source_id)
        ).all()
    assert outcome.chunk_count >= 1
    assert len(chunks) == outcome.chunk_count
    assert all(c.embedding is not None and len(c.embedding) == 1536 for c in chunks)
    assert all(c.chunk_hash for c in chunks)


def test_ingestion_idempotent_by_content_hash(client, db_session_factory):
    with db_session_factory() as s:
        o1 = _ingest(s, verified=False)
    with db_session_factory() as s:
        o2 = _ingest(s, verified=False)  # identical content
    assert o2.duplicate is True
    assert o1.source_id == o2.source_id
    from app.models.knowledge import KnowledgeSource

    with db_session_factory() as s:
        count = s.scalar(select(__import__("sqlalchemy").func.count()).select_from(KnowledgeSource))
    assert count == 1


def test_ingestion_empty_content_rejected(client, db_session_factory):
    from app.modules.knowledge.ingestion.pipeline import EmptyContentError
    from app.modules.knowledge.embeddings.provider import DeterministicTestEmbeddingProvider
    from app.modules.knowledge.ingestion.pipeline import IngestionPipeline
    from app.models.enums import VerificationStatus
    from app.models.knowledge import KnowledgeSource

    with db_session_factory() as s:
        pipe = IngestionPipeline(s, embedder=DeterministicTestEmbeddingProvider(1536))
        with pytest.raises(EmptyContentError):
            pipe.ingest(
                title="Empty", url="https://demo.gov.in/empty", publisher="D",
                content=b"<html><body><nav>only nav</nav></body></html>", content_type="text/html",
            )
        # A REJECTED source row is recorded (not silently empty).
        src = s.scalars(select(KnowledgeSource).where(KnowledgeSource.url == "https://demo.gov.in/empty")).first()
        assert src is not None and src.verification_status is VerificationStatus.REJECTED


# ------------------------------ retrieval ----------------------------------- #
def test_semantic_lexical_hybrid_retrieval(client, db_session_factory):
    from app.modules.knowledge.embeddings.provider import DeterministicTestEmbeddingProvider
    from app.modules.knowledge.retrieval.hybrid import HybridRetriever
    from app.modules.knowledge.retrieval.lexical import LexicalRetriever
    from app.modules.knowledge.retrieval.semantic import SemanticRetriever

    with db_session_factory() as s:
        _ingest(s)
        emb = DeterministicTestEmbeddingProvider(1536)

        sem = SemanticRetriever(s, emb).retrieve(
            query="income certificate documents", scheme_id=None, scheme_version_id=None,
            authoritative_only=True, limit=10,
        )
        lex = LexicalRetriever(s).retrieve(
            query="income certificate", scheme_id=None, scheme_version_id=None,
            authoritative_only=True, limit=10,
        )
        hyb = HybridRetriever(s, emb).retrieve(query="income certificate documents")

    assert len(sem) >= 1
    assert len(lex) >= 1
    assert len(hyb) >= 1
    assert any("Income certificate" in c.content for c in hyb)


def test_trust_filtering_excludes_unverified(client, db_session_factory):
    from app.modules.knowledge.embeddings.provider import DeterministicTestEmbeddingProvider
    from app.modules.knowledge.retrieval.hybrid import HybridRetriever

    with db_session_factory() as s:
        _ingest(s, verified=False, url="https://random.example.com/unverified")  # stays unverified
        hyb = HybridRetriever(s, DeterministicTestEmbeddingProvider(1536)).retrieve(
            query="income certificate", authoritative_only=True
        )
    # Unverified source must not be surfaced as authoritative evidence.
    assert all(c.trust_level != "unverified" for c in hyb)


def test_version_aware_retrieval_prefers_version(client, db_session_factory):
    from app.modules.knowledge.embeddings.provider import DeterministicTestEmbeddingProvider
    from app.modules.knowledge.retrieval.hybrid import HybridRetriever

    vid = uuid.uuid4()
    with db_session_factory() as s:
        # We need a real scheme_version to FK against; create one via the model.
        from datetime import date
        from app.models.scheme import Scheme, SchemeVersion

        scheme = Scheme(canonical_name="V", category="c", scope="central")
        s.add(scheme); s.flush()
        v = SchemeVersion(scheme_id=scheme.id, version_no=1, status="published",
                          benefits_summary="b", effective_from=date(2025, 1, 1))
        s.add(v); s.flush()
        _ingest(s, url="https://demo.gov.in/v1", scheme_version_id=v.id,
                content="<h1>Version One</h1><p>income certificate needed under version one</p>")
        _ingest(s, url="https://demo.gov.in/other",
                content="<h1>Other</h1><p>income certificate general guidance</p>")
        hyb = HybridRetriever(s, DeterministicTestEmbeddingProvider(1536)).retrieve(
            query="income certificate", scheme_version_id=v.id
        )
    # The version-matched chunk should rank at or near the top (version bonus).
    assert hyb[0].scheme_version_id == v.id


# ------------------------------ search API ---------------------------------- #
def test_knowledge_search_api(client, db_session_factory):
    with db_session_factory() as s:
        _ingest(s)
    token = _register(client, "searcher@example.com")
    r = client.post(
        "/api/v1/knowledge/search",
        headers=_h(token),
        json={"query": "what income documents are required", "limit": 5},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body) >= 1
    item = body[0]
    assert set(["chunk_id", "source_id", "content", "source_url", "page_number", "section", "score"]) <= set(item)


# ------------------------------ jobs ---------------------------------------- #
def test_ingestion_job_flow_with_fake_fetcher(client, db_session_factory):
    # Create a job via the service, then run the worker with a fake fetcher
    # that returns demo HTML (no real network).
    from app.modules.knowledge.service import KnowledgeService
    from app.modules.knowledge.worker import run_job_until_terminal
    from app.modules.knowledge.ingestion.fetcher import FetchResult

    with db_session_factory() as s:
        admin = _admin_token(client, db_session_factory, "jobadmin@example.com")
        from app.models.user import User
        actor = s.scalar(select(User).where(User.email == "jobadmin@example.com"))
        job = KnowledgeService(s).create_ingestion_job(
            title="J", url="https://demo.gov.in/job", publisher="D",
            scheme_id=None, scheme_version_id=None, actor_user_id=actor.id,
        )
        job_id = job.id

    class FakeFetcher:
        def fetch(self, url):
            return FetchResult(url=url, final_url=url, status_code=200,
                               content_type="text/html", content=DEMO_HTML.encode("utf-8"),
                               retrieved_at=0.0)

    status = run_job_until_terminal(job_id, fetcher=FakeFetcher())
    from app.models.enums import IngestionJobStatus

    assert status is IngestionJobStatus.COMPLETED
    with db_session_factory() as s:
        from app.models.knowledge import IngestionJob

        j = s.get(IngestionJob, job_id)
        assert j.status is IngestionJobStatus.COMPLETED
        assert j.knowledge_source_id is not None
        assert j.result["chunk_count"] >= 1


def test_ingestion_job_ssrf_fails_permanently(client, db_session_factory):
    from app.modules.knowledge.service import KnowledgeService
    from app.modules.knowledge.worker import run_job_until_terminal
    from app.models.enums import IngestionJobStatus
    from app.models.user import User

    with db_session_factory() as s:
        _admin_token(client, db_session_factory, "ssrfadmin@example.com")
        actor = s.scalar(select(User).where(User.email == "ssrfadmin@example.com"))
        job = KnowledgeService(s).create_ingestion_job(
            title="bad", url="http://169.254.169.254/latest/meta-data", publisher="D",
            scheme_id=None, scheme_version_id=None, actor_user_id=actor.id,
        )
        job_id = job.id
    # Real SafeFetcher (default) — SSRF guard must reject and fail the job.
    status = run_job_until_terminal(job_id)
    assert status is IngestionJobStatus.FAILED
    with db_session_factory() as s:
        from app.models.knowledge import IngestionJob

        j = s.get(IngestionJob, job_id)
        assert j.status is IngestionJobStatus.FAILED
        assert j.attempts == 1  # permanent error, not retried repeatedly
        assert "Ssrf" in (j.error or "")


def test_knowledge_seed_runs(client, db_session_factory):
    from app.seeds.seed_knowledge import seed

    with db_session_factory() as s:
        summary = seed(s)
    assert len(summary["source_ids"]) >= 1
