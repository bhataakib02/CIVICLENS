# CivicLens Opportunity Intelligence Architecture

## Overview
CivicLens Opportunity Intelligence is a unified discovery engine that automatically discovers, structures, verifies, deduplicates, updates, and presents opportunities across government jobs, private jobs, internships, apprenticeships, scholarships, fellowships, government schemes, benefits, grants, training programs, skill programs, job fairs, competitions, and admissions.

```text
Source Registry
       ↓
Connector (RSS / Sitemap / HTML / JSON / API / PDF)
       ↓
Safe Fetcher (SSRF & Rate Limiting Guard)
       ↓
Raw Document
       ↓
Parser & Content Hash Change Detection
       ↓
Opportunity Extractor (Pydantic Schema Validation)
       ↓
Normalizer & Date Classifier
       ↓
Link Validator (SSRF & Redirect Check)
       ↓
Quality Scorer (Auto-Publish vs Review Queue)
       ↓
Deduplicator (Deterministic & Canonical Source Selection)
       ↓
PostgreSQL Database (Opportunities, Versions, Changes, Links)
       ↓
Opportunity Matching Engine & Search Parser
       ↓
FastAPI Endpoints & Realtime Outbox Events
       ↓
Citizen Explorer & Admin Control Console
```

## Core Guarantees & Product Promise
1. **Defensible Scope**: CivicLens never claims to index "the entire internet." All listings explicitly show `Indexed Sources`, `Verified Sources`, `Last Crawl Time`, and `Last Verification Time`.
2. **Official Redirection Interstitial**: CivicLens never submits applications on behalf of citizens. The citizen is routed directly to the verified official portal via an explicit interstitial modal.
3. **Continuous 30-Minute Scheduler**: Background worker processes sources every 30 minutes using distributed Redis locks (`DistributedCrawlLock`) and incremental content hash change detection.
