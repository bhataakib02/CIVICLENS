# CivicLens — Production Blocker Register & Accepted Risks

This document provides a transparent log of open production blockers (zero active blockers) and accepted operational risks.

---

## Active Blockers Register

| Blocker ID | Severity | Component | Description | Impact | Status |
|---|---|---|---|---|---|
| *None* | N/A | N/A | No critical or high severity blockers remain in codebase. | None | **CLOSED** |

---

## Accepted Operational Risks

1. **Third-Party Provider Credentials (AWS / SMS)**:
   - **Severity**: MEDIUM
   - **Description**: AWS Cloud infrastructure and live SMS gateways rely on mock providers during local execution.
   - **Workaround / Mitigation**: Complete Terraform modules and mock gateways exist. Production deployment simply requires adding environment vendor keys.
2. **Single-Node Rate Limiting Fallback**:
   - **Severity**: LOW
   - **Description**: If Redis is offline, rate limiting falls back to single-node in-memory tracking with warning logs.
   - **Mitigation**: Redis container configured in Docker Compose and Terraform ElastiCache module.
