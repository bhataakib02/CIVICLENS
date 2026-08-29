# Incident Response

Status: v1.0 draft
Related: security-architecture.md §5, audit-logging.md, threat-model.md, DPDP Act obligations

## 1. Severity Tiers

| Tier | Definition | Example | Response time |
|---|---|---|---|
| Sev1 | Active citizen data breach or full service outage | Document bucket exposed publicly; DB compromise | Immediate, all-hands |
| Sev2 | Significant degraded security or availability, contained | Elevated auth failure rate suggesting credential stuffing | ≤ 1 hour |
| Sev3 | Limited-impact issue, no active exploitation confirmed | Single account anomaly flagged | ≤ 1 business day |

## 2. Process

1. **Detect** — via alerting.md triggers, manual report, or external
   disclosure (SECURITY.md).
2. **Triage** — on-call assigns severity, forms a response group for
   Sev1/Sev2.
3. **Contain** — revoke affected credentials/tokens (global token-version
   bump if needed), disable affected endpoints/roles, isolate affected
   infrastructure.
4. **Investigate** — audit_logs, access logs, and tracing data
   (operations/tracing.md) reconstruct scope and timeline.
5. **Notify** — for a confirmed PII breach, notification follows the DPDP
   Act's breach-notification timeline to both the Data Protection Board
   and affected citizens; legal/compliance is looped in immediately for
   any Sev1 involving citizen data.
6. **Remediate** — fix root cause, not just the symptom.
7. **Post-incident review** — mandatory for Sev1/Sev2, blameless, produces
   concrete action items with owners.

## 3. On-Call

Defined rotation with escalation policy; paging integrated with
operations/alerting.md.

## 4. Reporting a Vulnerability

External reports follow SECURITY.md — never a public GitHub issue.
