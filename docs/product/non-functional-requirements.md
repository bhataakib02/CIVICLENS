# CivicLens — Non-Functional Requirements

Status: v1.0 draft
Related: product-requirements.md, architecture/system-architecture.md, architecture/scalability.md, security/security-architecture.md

Each NFR has an ID: `NFR-<category>-<n>`. Where a target is a number, it is a
launch target for v1.0, not an aspirational ceiling.

## NFR-PERF — Performance

- NFR-PERF-1: Scheme search / eligibility list p95 latency ≤ 800ms server-side
  for a citizen with a fully-populated profile, at launch traffic levels.
- NFR-PERF-2: Assistant (RAG) answer p95 latency ≤ 6s end-to-end, including
  retrieval + generation; interim "thinking" state shown to the user beyond
  1.5s.
- NFR-PERF-3: Document OCR + extraction completes asynchronously; the
  citizen sees a result or explicit failure within 60s p95 for a single
  document.
- NFR-PERF-4: Bulk eligibility check across the full active scheme catalog
  (target: ~500 schemes at launch) completes in ≤ 3s p95 using cached rule
  compilation.

## NFR-SCALE — Scalability

- NFR-SCALE-1: Backend must handle 10x launch traffic via horizontal scaling
  of stateless API instances without architectural changes (modular monolith
  behind a load balancer; see ADR-001).
- NFR-SCALE-2: Async workloads (OCR, embedding generation, notification
  delivery) run on a worker pool (Celery) that scales independently of the
  API tier.
- NFR-SCALE-3: The knowledge base must support at least 50,000 knowledge
  chunks with pgvector similarity search returning top-k in ≤ 200ms p95 at
  that scale.

## NFR-AVAIL — Availability & Reliability

- NFR-AVAIL-1: Core citizen-facing flows (auth, profile, scheme browse,
  eligibility) target 99.5% monthly availability at launch.
- NFR-AVAIL-2: The assistant (RAG) subsystem is allowed a lower availability
  target (99%) and must degrade gracefully — if generation is unavailable,
  deterministic eligibility results and scheme browsing must continue to
  work.
- NFR-AVAIL-3: No single AI provider outage may take down eligibility
  determination, since eligibility is computed by the deterministic rule
  engine, not by a model call (see ai/eligibility-engine.md).
- NFR-AVAIL-4: Database backups: automated daily snapshots + point-in-time
  recovery with RPO ≤ 15 minutes, RTO ≤ 4 hours (see
  operations/backup-restore.md).

## NFR-SEC — Security

- NFR-SEC-1: All data in transit encrypted (TLS 1.2+); all PII at rest
  encrypted at the storage layer.
- NFR-SEC-2: Document files (identity/income proofs) are stored in
  access-controlled object storage with per-object authorization, never
  served via predictable/public URLs (see security/document-security.md).
- NFR-SEC-3: All admin and scheme-administrator accounts require MFA.
- NFR-SEC-4: The system must pass an independent security review /
  penetration test before handling real citizen documents in production.
- NFR-SEC-5: See threat-model.md for the enumerated threat list this system
  is designed against.

## NFR-PRIV — Privacy & Compliance

- NFR-PRIV-1: Compliance with India's Digital Personal Data Protection Act
  (DPDP), 2023: purpose limitation, consent records, data minimization,
  right to erasure/correction.
- NFR-PRIV-2: PII must never appear in application logs, error traces, or
  analytics events in plaintext (see security/pii-handling.md).
- NFR-PRIV-3: A citizen can request full export and deletion of their data,
  subject to statutory retention requirements for submitted government
  applications.

## NFR-ACC — Accessibility & Usability

- NFR-ACC-1: WCAG 2.1 AA conformance for all citizen-facing screens.
- NFR-ACC-2: Must function on low-end Android devices (2GB RAM class) and on
  2G/3G-equivalent network conditions (PWA, aggressive asset budgeting; see
  frontend/pwa.md).
- NFR-ACC-3: All citizen-facing content available in Hindi and English at
  launch; i18n framework must not require redeployment to add a language.
- NFR-ACC-4: Reading level for eligibility explanations and scheme summaries
  targeted at class 8 comprehension level in the primary language.

## NFR-OBS — Observability

- NFR-OBS-1: Structured logging, distributed tracing, and metrics across
  API and worker tiers (see operations/observability.md).
- NFR-OBS-2: Every AI-generated answer and every eligibility determination
  is logged with enough context (rule versions, retrieved chunk IDs, model
  version) to reproduce the result for audit.
- NFR-OBS-3: Alerting on: knowledge base staleness beyond threshold, RAG
  citation rate dropping below threshold, elevated eligibility-engine error
  rate, OCR failure rate spikes.

## NFR-MAINT — Maintainability

- NFR-MAINT-1: Backend organized as a modular monolith with enforced module
  boundaries (see backend/module-boundaries.md) so modules can later be
  extracted into services without a rewrite, if scale ever requires it.
- NFR-MAINT-2: Every eligibility rule change and every knowledge source
  ingestion is versioned and attributable (who, when, from what source).
- NFR-MAINT-3: Test coverage gates on CI: unit ≥ 80% for `core` and
  `eligibility` modules; contract tests required for every API endpoint
  (see testing/testing-strategy.md).

## NFR-AI — AI-Specific Quality Requirements

- NFR-AI-1: The assistant must not answer scheme-specific factual questions
  without a retrieval citation (see ai/hallucination-controls.md).
- NFR-AI-2: Eligibility determinations are never produced by free-generation
  LLM output; the LLM may only assist in *structuring* a citizen's
  free-text input into profile attributes, which are then evaluated by the
  deterministic engine.
- NFR-AI-3: A held-out evaluation set of scheme Q&A pairs must pass a
  defined accuracy/citation threshold before any change to the retrieval
  pipeline or prompt ships to production (see ai/ai-evaluation.md,
  ADR-009).
