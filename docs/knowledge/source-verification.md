# Source Verification

Status: v1.0 draft
Related: knowledge-base.md, source-policy.md, threat-model.md #8, product/non-functional-requirements.md (NFR-OBS-3)

## 1. The Staleness Problem

Government scheme rules change on unpredictable schedules (budget cycles,
amendments). A knowledge source that was accurate at ingestion can become
outdated without any signal from the source itself if no one checks back
(threat-model.md #8).

## 2. Verification Cadence

Each `knowledge_source` has a `last_verified_at` timestamp and a review
cadence assigned by category — e.g., high-churn categories (income
thresholds, benefit amounts, deadline-bound schemes) reviewed more
frequently than stable structural information (eligibility category
definitions that rarely change). Cadence assignment and its rationale are
documented per scheme category, not left implicit.

## 3. Staleness Alerting

`last_verified_at` beyond its category's threshold triggers an alert
(operations/alerting.md, NFR-OBS-3) surfaced to scheme administrators via
the admin knowledge base monitor (FR-ADMIN-3) — a source doesn't silently
age past its confidence window unnoticed.

## 4. Verification Process

A scheme administrator (or, at scale, an automated diff-check against the
source URL flagging "content may have changed" for human confirmation)
re-visits the live government source, confirms it still matches the
ingested content, and either updates `last_verified_at` (no change) or
triggers re-ingestion + a new `scheme_version` (content changed,
document-versioning.md).

## 5. Citizen-Facing Transparency

Every scheme detail view surfaces its `last_verified_at` date
(FR-SCHEME-4) — citizens and auditors can see for themselves how current
the information they're relying on is, rather than being implicitly asked
to trust an unstated freshness guarantee.
