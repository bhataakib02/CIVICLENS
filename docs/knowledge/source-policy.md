# Knowledge Source Policy

Status: v1.0 draft
Related: knowledge-base.md, source-verification.md, threat-model.md #4, ai-safety.md §3

## 1. Vetted Publisher Allowlist

Knowledge sources may only be registered from an explicit allowlist of
publishers: central and state government ministry/department official
sites and gazettes, and a small set of pre-approved authoritative
secondary publishers (e.g., an official scheme-aggregation portal) where
no primary source is directly available. Citizen-submitted URLs, general
web search results, and unmoderated third-party blogs/news are never
eligible sources — this is the primary structural defense against RAG
poisoning (threat-model.md #4).

## 2. Registration & Review

`POST /admin/knowledge-sources` (scheme_admin/admin only) requires the
source URL to resolve to an allowlisted domain; ingestion doesn't proceed
to `ingested` status until a human reviewer confirms the source content is
genuine, current, and correctly attributed (publisher, published_date)
before it becomes retrievable — see ingestion-pipeline.md §3.

## 3. Extending the Allowlist

Adding a new publisher to the allowlist is itself a reviewed change
(not a runtime admin action) — it goes through the same change-review
discipline as a code change, since it directly expands the trust boundary
for what the assistant can cite as authoritative.

## 4. Rejected Alternative

Allowing any URL with post-hoc moderation was considered and rejected —
by the time a bad source is flagged after the fact, it may already have
been retrieved and cited in live citizen-facing answers; pre-ingestion
allowlisting closes that gap by construction rather than by detection
speed.
