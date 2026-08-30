"""Assistant service (prompt §22, §23, §27).

Pipeline:
    query -> fact extraction -> scheme discovery -> retrieval -> rerank
          -> (deterministic eligibility checks where rules exist)
          -> grounding (system/user/data separation, injection defense)
          -> LLM generation (structured) -> citation validation + hallucination
             guard -> response.

CRITICAL: the LLM only EXPLAINS. Eligibility is decided by the deterministic
engine (ADR-003). Any eligibility statement in the response is backed by an
`eligibility_tool_calls` entry produced by the engine, never by the model.

Fact extraction here is deterministic keyword/regex extraction (no model) —
turning "I'm 22 and unemployed in West Bengal" into structured facts that feed
the engine. This is assistive parsing, not eligibility reasoning.
"""
from __future__ import annotations

import re
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.enums import SchemeVersionStatus
from app.models.scheme import Scheme, SchemeVersion
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.dependencies import CurrentUser
from app.modules.eligibility.compiler import rule_cache
from app.modules.eligibility.context import ContextBuilder
from app.modules.eligibility.engine import evaluate as engine_evaluate
from app.modules.eligibility.repository import EligibilityRepository
from app.modules.knowledge.embeddings.provider import get_embedding_provider
from app.modules.knowledge.grounding.context import build_grounding_context
from app.modules.knowledge.llm.guard import LLMAnswer, guard_answer
from app.modules.knowledge.llm.provider import get_llm_provider
from app.modules.knowledge.retrieval.hybrid import HybridRetriever
from app.modules.knowledge.retrieval.reranker import get_reranker

logger = get_logger("civiclens.assistant")

_STATE_HINTS = [
    "west bengal", "bihar", "kerala", "karnataka", "maharashtra", "tamil nadu",
    "uttar pradesh", "rajasthan", "gujarat", "punjab",
]
_AGE_RE = re.compile(r"\b(\d{1,2})\s*(?:years?\s*old|yo|y/o)?\b")
_UNEMPLOYED_RE = re.compile(r"\bunemployed\b", re.IGNORECASE)


class AssistantService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._s = settings or get_settings()
        self._audit = AuditService(session)

    def query(
        self,
        *,
        current: CurrentUser,
        query: str,
        scheme_id: uuid.UUID | None = None,
        scheme_version_id: uuid.UUID | None = None,
        conversation_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> dict:
        logger.info("assistant_query_started", extra={"has_scheme": scheme_id is not None})

        # 0. Handle simple conversational greetings gracefully
        clean_query = query.strip().lower()
        if clean_query in ("hi", "hello", "hey", "hii", "hiii", "namaste", "good morning", "good afternoon", "good evening"):
            return {
                "conversation_id": str(conversation_id or uuid.uuid4()),
                "answer": "Hello! I am CivicLens Assistant. How can I help you today? You can ask me about government schemes, eligibility rules, required documents, or how to apply.",
                "citations": [],
                "scheme_ids": [],
                "eligibility_tool_calls": [],
                "missing_information": [],
                "confidence": 1.0,
                "grounded": True,
            }

        # 1. Deterministic fact extraction (assistive parsing, not decisions).
        facts = self._extract_facts(query)

        # 2. Scheme discovery (semantic, if no scheme pinned).
        candidate_versions = self._discover_scheme_versions(query, scheme_id, scheme_version_id)

        # 3. Deterministic eligibility checks where rules exist (engine decides).
        eligibility_tool_calls = self._run_eligibility(current, candidate_versions, facts)

        # 4. Retrieval + rerank (authoritative evidence only).
        embedder = get_embedding_provider(self._s)
        retriever = HybridRetriever(self._session, embedder, self._s)
        candidates = retriever.retrieve(
            query=query,
            scheme_id=scheme_id,
            scheme_version_id=scheme_version_id,
            authoritative_only=True,
        )
        evidence = get_reranker().rerank(query, candidates, top_k=6)

        # 5. Grounding (system/user/data separation + injection defense).
        elig_ctx = self._format_eligibility(eligibility_tool_calls) if eligibility_tool_calls else None
        grounding = build_grounding_context(
            user_query=query, evidence=evidence, eligibility_context=elig_ctx
        )

        # 6. LLM generation (structured) — the model EXPLAINS only.
        provider = get_llm_provider(self._s)
        try:
            llm_answer = provider.generate_structured(grounding.to_prompt(), LLMAnswer)
        except Exception:
            logger.warning("assistant_llm_failed")
            llm_answer = LLMAnswer(
                answer="I couldn't verify this from the available official sources.",
                evidence_indices=[], confidence=0.0,
            )

        # 7. Citation validation + hallucination guard.
        guarded = guard_answer(llm_answer, grounding.evidence_markers)

        self._audit.record(
            action=AuditAction.ASSISTANT_QUERY,
            entity_type="assistant_query",
            actor_user_id=current.id,
            diff={
                "grounded": guarded.grounded,
                "evidence_count": len(evidence),
                "eligibility_calls": len(eligibility_tool_calls),
            },
            ip=ip,
        )
        self._session.commit()

        return {
            "conversation_id": str(conversation_id or uuid.uuid4()),
            "answer": guarded.answer,
            "citations": [
                {
                    "source_id": c.source_id,
                    "chunk_id": c.chunk_id,
                    "source_url": c.source_url,
                    "page_number": c.page_number,
                    "section": c.section,
                }
                for c in guarded.citations
            ],
            "scheme_ids": [str(v.scheme_id) for v in candidate_versions],
            "eligibility_tool_calls": eligibility_tool_calls,
            "missing_information": guarded.missing_information,
            "confidence": guarded.confidence,
            "grounded": guarded.grounded,
        }

    # ------------------------------------------------------------------ #
    def _extract_facts(self, query: str) -> dict:
        facts: dict = {}
        m = _AGE_RE.search(query)
        if m:
            age = int(m.group(1))
            if 0 < age < 120:
                facts["citizen.age"] = age
        if _UNEMPLOYED_RE.search(query):
            facts["citizen.occupation"] = "UNEMPLOYED"
        lowered = query.lower()
        for state in _STATE_HINTS:
            if state in lowered:
                facts["citizen.address.state"] = state.title()
                break
        return facts

    def _discover_scheme_versions(
        self, query: str, scheme_id: uuid.UUID | None, scheme_version_id: uuid.UUID | None
    ) -> list[SchemeVersion]:
        from sqlalchemy import select

        if scheme_version_id is not None:
            v = self._session.get(SchemeVersion, scheme_version_id)
            return [v] if v else []
        stmt = (
            select(SchemeVersion)
            .where(SchemeVersion.status == SchemeVersionStatus.PUBLISHED)
            .where(SchemeVersion.effective_to.is_(None))
        )
        if scheme_id is not None:
            stmt = stmt.where(SchemeVersion.scheme_id == scheme_id)
        else:
            # Lightweight discovery: match query terms against scheme name/category.
            terms = [t for t in re.findall(r"[a-z]+", query.lower()) if len(t) > 3]
            versions = list(self._session.scalars(stmt))
            if terms:
                scheme_ids = {v.scheme_id for v in versions}
                schemes = {
                    s.id: s
                    for s in self._session.scalars(
                        select(Scheme).where(Scheme.id.in_(scheme_ids))
                    )
                }
                scored = []
                for v in versions:
                    s = schemes.get(v.scheme_id)
                    hay = f"{s.canonical_name} {s.category}".lower() if s else ""
                    hits = sum(1 for t in terms if t in hay)
                    scored.append((hits, v))
                scored.sort(key=lambda x: x[0], reverse=True)
                return [v for hits, v in scored if hits > 0][:5] or versions[:5]
            return versions[:5]
        return list(self._session.scalars(stmt))

    def _run_eligibility(
        self, current: CurrentUser, versions: list[SchemeVersion], facts: dict
    ) -> list[dict]:
        elig_repo = EligibilityRepository(self._session)
        profile = elig_repo.get_profile_by_user_id(current.id)
        if profile is None:
            return []
        primary_address = elig_repo.primary_address(profile.id)
        # Profile data is authoritative. Query-extracted facts only SUPPLEMENT
        # fields the profile doesn't already provide (avoids a free-text "22"
        # conflicting with an authoritative date_of_birth). This keeps the
        # engine's conflict detection meaningful (profile vs. documents) without
        # manufacturing conflicts from loose conversational phrasing.
        supplemental = self._supplemental_facts(facts, profile, primary_address)
        calls: list[dict] = []
        for version in versions:
            rows = elig_repo.load_rules(version.id)
            if not rows:
                continue
            ast = rule_cache.get_or_compile(version.id, rows)
            ctx = ContextBuilder().build(
                citizen_profile=profile,
                primary_address=primary_address,
                evaluation_date=date.today(),
                scheme_version_id=version.id,
                extra_facts=supplemental,
            )
            result = engine_evaluate(ast, ctx)
            calls.append(
                {
                    "scheme_id": str(version.scheme_id),
                    "scheme_version_id": str(version.id),
                    "result": result.decision.value,
                    "matched_rules": result.matched_rules,
                    "failed_rules": result.failed_rules,
                    "missing_information": result.missing_information,
                    "engine_version": result.engine_version,
                }
            )
        return calls

    def _supplemental_facts(self, facts: dict, profile, primary_address) -> dict:
        """Keep only query-extracted facts for fields the profile lacks.

        The profile is authoritative; extracted conversational hints only fill
        gaps, so a loose "22" cannot conflict with an authoritative
        date_of_birth. This keeps the engine's conflict detection meaningful
        (profile vs. documents) rather than manufacturing conflicts from phrasing.
        """
        provided = {
            "citizen.age": profile.date_of_birth is not None,
            "citizen.date_of_birth": profile.date_of_birth is not None,
            "citizen.occupation": profile.occupation is not None,
            "citizen.employment_status": profile.occupation is not None,
            "citizen.declared_annual_income": profile.declared_annual_income is not None,
            "citizen.address.state": primary_address is not None,
        }
        return {k: v for k, v in facts.items() if not provided.get(k, False)}

    def _format_eligibility(self, calls: list[dict]) -> str:
        lines = []
        for c in calls:
            lines.append(
                f"scheme_version={c['scheme_version_id']} decision={c['result']} "
                f"(engine {c['engine_version']}; matched={c['matched_rules']} failed={c['failed_rules']})"
            )
        return "\n".join(lines)
