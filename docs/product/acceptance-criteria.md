# Acceptance Criteria (Launch Gate)

Status: v1.0 draft
Related: functional-requirements.md, non-functional-requirements.md, testing/testing-strategy.md

CivicLens v1.0 is ready to launch when all of the following hold, verified
by the corresponding test/process, not asserted informally:

## Functional
- [ ] Every `FR-*` in functional-requirements.md has passing contract,
      integration, and (where applicable) E2E test coverage.
- [ ] The vertical slice — register → profile → address → browse schemes
      → check eligibility → see evidence — works end-to-end
      (architecture/system-architecture.md's stated first milestone).
- [ ] Document upload → OCR → extraction → validation works end-to-end
      for all launch-supported document types.
- [ ] Application → status machine → notifications works end-to-end.

## Non-Functional
- [ ] Load testing confirms NFR-PERF-* and NFR-SCALE-* targets hold at
      launch-projected traffic (testing/load-testing.md).
- [ ] WCAG 2.1 AA conformance verified on all citizen-facing screens
      (frontend/accessibility.md).
- [ ] Hindi and English fully supported across UI, scheme content, and
      assistant responses (NFR-ACC-3).

## Security & Privacy
- [ ] Independent security review / penetration test completed with all
      critical/high findings resolved (NFR-SEC-4).
- [ ] Every threat-model.md entry maps to a tested, implemented control
      (security/threat-model.md, testing/security-testing.md §3).
- [ ] DPDP Act compliance review completed (consent flows, erasure/
      correction flows, breach-notification process).

## AI Quality
- [ ] RAG assistant passes the evaluation gate thresholds (factual
      accuracy, citation presence/correctness, refusal correctness) on
      the current held-out evaluation set (ADR-009).
- [ ] Eligibility engine has ≥ 80% unit coverage with property-based
      invariant tests passing (unit-testing.md §2).

## Operational
- [ ] Observability (logging, metrics, tracing, alerting) live in
      production with defined on-call rotation (operations/*.md).
- [ ] Backup/restore and disaster recovery procedures tested at least
      once against staging (architecture/disaster-recovery.md §4).

## Legal
- [ ] Legal review of "advisory eligibility" disclaimers completed
      (product-requirements.md §9, open question).
- [ ] Launch-priority state schemes confirmed with data-sourcing
      agreements in place (product-requirements.md §9).
