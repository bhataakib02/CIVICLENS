"""RAG evaluation metrics (prompt §36).

Pure metric functions over (ranked retrieved ids, relevant ids) and over
answer/citation records. Used by the RAG regression tests against a small
golden dataset. No model calls here — deterministic math.
"""
from __future__ import annotations

import math


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    topk = retrieved_ids[:k]
    hits = sum(1 for r in relevant_ids if r in topk)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(cases: list[tuple[list[str], set[str]]]) -> float:
    if not cases:
        return 0.0
    return sum(reciprocal_rank(r, rel) for r, rel in cases) / len(cases)


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    dcg = 0.0
    for i, rid in enumerate(retrieved_ids[:k], start=1):
        if rid in relevant_ids:
            dcg += 1.0 / math.log2(i + 1)
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return (dcg / idcg) if idcg > 0 else 0.0


def citation_validity_rate(records: list[dict]) -> float:
    """Fraction of answers whose citations are all valid (grounded).

    Each record: {"grounded": bool, "citations": [...], "made_claim": bool}.
    A grounded answer with >=1 citation counts as valid; a safe refusal counts
    as valid (no fabricated citation). An answer that made a claim but is not
    grounded is invalid.
    """
    if not records:
        return 1.0
    valid = 0
    for r in records:
        if r["grounded"] and r.get("citations"):
            valid += 1
        elif not r["grounded"] and not r.get("made_claim", True):
            valid += 1
        elif not r["grounded"] and r.get("is_refusal"):
            valid += 1
    return valid / len(records)


def unsupported_claim_rate(records: list[dict]) -> float:
    """Fraction of answers that asserted a claim without grounding (should be 0)."""
    if not records:
        return 0.0
    bad = sum(1 for r in records if r.get("made_claim") and not r["grounded"] and not r.get("is_refusal"))
    return bad / len(records)
