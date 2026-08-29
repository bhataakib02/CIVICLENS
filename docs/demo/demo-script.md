# CivicLens — Presentation Script & Talking Points

Screen-by-screen talking points for presenting CivicLens in technical interviews or engineering reviews.

---

## Presentation Script

### 1. Introduction & Overview
- **Screen**: `/login` (Citizen Portal)
- **Action**: Log in with demo credentials.
- **Talking Point**: *"CivicLens is a civic tech platform built with Next.js 14, FastAPI, PostgreSQL + pgvector, and Redis. It solves the key problem of government scheme discovery, deterministic eligibility verification, and document intelligence."*

### 2. AI Assistant vs. Rule Engine Boundary
- **Screen**: `/assistant`
- **Action**: Ask a policy question and show citations.
- **Talking Point**: *"Notice how the LLM provides clear explanations with official citations, but it NEVER decides eligibility. Eligibility is evaluated by a separate deterministic rule engine to eliminate hallucinations."*

### 3. Scheme Eligibility Engine
- **Screen**: `/eligibility`
- **Action**: Click 'Check Eligibility'.
- **Talking Point**: *"The engine compiles versioned AST rules and evaluates them against the citizen's profile facts in under 2.5ms, outputting an immutable snapshot stored in PostgreSQL."*

### 4. Scheme Four-Eyes Governance
- **Screen**: `/admin/schemes` (Admin Console)
- **Action**: Show publish attempt with author account (rejected) vs. reviewer account (approved).
- **Talking Point**: *"For regulatory compliance, CivicLens enforces a strict server-side Four-Eyes rule: the author of a scheme version cannot publish their own version."*
