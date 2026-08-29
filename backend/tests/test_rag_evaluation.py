"""RAG evaluation regression (prompt §36).

Builds a small GOLDEN dataset of fictional demo documents + queries with known
relevant sources/answer facts, ingests them through the real pipeline, runs
hybrid retrieval + the assistant, and asserts measured quality thresholds:
    Recall@5, MRR, nDCG@5, citation validity rate, unsupported-claim rate.

Also asserts unit-level correctness of the metric functions themselves.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.modules.knowledge.evaluation import (
    citation_validity_rate,
    mean_reciprocal_rank,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
    unsupported_claim_rate,
)

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"

# Golden dataset: fictional demo docs. Each has a distinctive fact.
GOLDEN_DOCS = [
    {
        "key": "income",
        "url": "https://demo.gov.in/income",
        "content": "<h1>Income Support</h1><p>Applicants must submit an income certificate and a residence proof.</p>",
    },
    {
        "key": "unemployment",
        "url": "https://demo.gov.in/unemployment",
        "content": "<h1>Unemployment Aid</h1><p>Unemployed adults receive a monthly allowance.</p>",
    },
    {
        "key": "student",
        "url": "https://demo.gov.in/student",
        "content": "<h1>Student Grant</h1><p>Undergraduate and postgraduate students may claim a tuition grant.</p>",
    },
]

# query -> golden doc key expected as the top relevant source.
GOLDEN_QUERIES = [
    ("what income documents are required", "income"),
    ("monthly allowance for unemployed people", "unemployment"),
    ("tuition grant for postgraduate students", "student"),
]


def test_metric_functions_unit():
    import math

    assert recall_at_k(["a", "b", "c"], {"b"}, 5) == 1.0
    assert recall_at_k(["a", "b", "c"], {"z"}, 5) == 0.0
    assert reciprocal_rank(["a", "b"], {"b"}) == 0.5
    assert mean_reciprocal_rank([(["b"], {"b"}), (["x", "y"], {"y"})]) == pytest.approx(0.75)
    assert ndcg_at_k(["a", "b"], {"a"}, 5) == 1.0
    # single relevant item at rank 2 -> dcg = 1/log2(3), idcg = 1 -> ndcg = 1/log2(3)
    assert ndcg_at_k(["x", "a"], {"a"}, 5) == pytest.approx(1 / math.log2(3), rel=1e-6)


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _ingest_golden(session) -> dict[str, str]:
    from app.models.enums import SourceTrustLevel, VerificationStatus
    from app.models.knowledge import KnowledgeSource
    from app.modules.knowledge.embeddings.provider import DeterministicTestEmbeddingProvider
    from app.modules.knowledge.ingestion.pipeline import IngestionPipeline

    pipe = IngestionPipeline(session, embedder=DeterministicTestEmbeddingProvider(1536))
    key_to_source: dict[str, str] = {}
    for doc in GOLDEN_DOCS:
        o = pipe.ingest(
            title=doc["key"], url=doc["url"], publisher="Demo",
            content=doc["content"].encode("utf-8"), content_type="text/html",
        )
        src = session.get(KnowledgeSource, o.source_id)
        src.verification_status = VerificationStatus.VERIFIED
        src.trust_level = SourceTrustLevel.OFFICIAL_GOVERNMENT
        key_to_source[doc["key"]] = str(o.source_id)
    session.commit()
    return key_to_source


def test_rag_retrieval_quality(client, db_session_factory):
    from app.modules.knowledge.embeddings.provider import DeterministicTestEmbeddingProvider
    from app.modules.knowledge.retrieval.hybrid import HybridRetriever
    from app.modules.knowledge.retrieval.reranker import DeterministicReranker

    with db_session_factory() as s:
        key_to_source = _ingest_golden(s)
        retriever = HybridRetriever(s, DeterministicTestEmbeddingProvider(1536))
        reranker = DeterministicReranker()

        cases: list[tuple[list[str], set[str]]] = []
        recalls, ndcgs = [], []
        for query, gold_key in GOLDEN_QUERIES:
            cands = retriever.retrieve(query=query)
            top = reranker.rerank(query, cands, top_k=5)
            ranked_source_ids = [str(c.source_id) for c in top]
            relevant = {key_to_source[gold_key]}
            cases.append((ranked_source_ids, relevant))
            recalls.append(recall_at_k(ranked_source_ids, relevant, 5))
            ndcgs.append(ndcg_at_k(ranked_source_ids, relevant, 5))

    recall5 = sum(recalls) / len(recalls)
    mrr = mean_reciprocal_rank(cases)
    ndcg5 = sum(ndcgs) / len(ndcgs)
    # Measured thresholds (documented). The deterministic embedder + FTS make
    # these queries retrievable; assert real, non-trivial quality.
    assert recall5 >= 0.99, f"Recall@5={recall5}"
    assert mrr >= 0.8, f"MRR={mrr}"
    assert ndcg5 >= 0.8, f"nDCG@5={ndcg5}"


def test_rag_citation_validity_and_unsupported_rate(client, db_session_factory):
    with db_session_factory() as s:
        _ingest_golden(s)
    token = _register(client, "rageval@example.com")

    records: list[dict] = []
    # Answerable queries (evidence present).
    for query, _key in GOLDEN_QUERIES:
        r = client.post("/api/v1/assistant/query", headers=_h(token), json={"query": query})
        b = r.json()
        records.append({
            "grounded": b["grounded"],
            "citations": b["citations"],
            "made_claim": True,
            "is_refusal": not b["grounded"],
        })
    # Unanswerable query (no evidence) -> must refuse, not fabricate.
    r = client.post(
        "/api/v1/assistant/query", headers=_h(token),
        json={"query": "quantum entanglement grant for astronauts on mars"},
    )
    b = r.json()
    records.append({
        "grounded": b["grounded"],
        "citations": b["citations"],
        "made_claim": True,
        "is_refusal": not b["grounded"],
    })

    validity = citation_validity_rate(records)
    unsupported = unsupported_claim_rate(records)
    assert validity >= 0.99, f"citation_validity={validity}"
    assert unsupported == 0.0, f"unsupported_claim_rate={unsupported}"
