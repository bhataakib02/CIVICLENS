# Security Testing

Status: v1.0 draft
Related: testing-strategy.md §8, security/threat-model.md, security/security-architecture.md §6, infrastructure/ci-cd.md §1

## 1. Automated (every merge)

- **SAST** (static analysis) on every PR — catches common vulnerability
  classes (injection, insecure deserialization, hardcoded secrets) before
  merge.
- **Dependency scanning** — flags known-vulnerable packages in both
  backend and frontend dependency trees; a critical/high finding blocks
  merge pending a fix or an explicitly reviewed exception.
- **Secret scanning** — prevents committing credentials/keys, including a
  pre-commit hook layer in addition to the CI-level check
  (security/secrets-management.md §2).

## 2. Automated (periodic, staging)

- **DAST** (dynamic scanning) against the staging deployment on a
  recurring schedule, and after any significant auth/authorization change.

## 3. Manual / Threat-Model-Driven

Each entry in security/threat-model.md maps to at least one test case
here — this list is reviewed and extended whenever the threat model
gains a new entry, so the two documents stay in lockstep rather than
drifting apart:

| Threat | Test approach |
|---|---|
| Cross-user document access | Automated test: citizen A's token cannot fetch citizen B's document by ID |
| Privilege escalation | Automated test: role/ownership checks hold under crafted requests (e.g., role claimed in a manipulated token) |
| Eligibility-rule tampering | Automated test: DSL rejects out-of-grammar/out-of-registry rule payloads |
| Prompt injection | Manual + automated probe set (ai/ai-evaluation.md §1) with injected instructions embedded in synthetic retrieved content |
| API abuse / rate limiting | Automated test: limits enforced and return correct 429 shape |

## 4. Penetration Testing

Independent third-party penetration test required before production
handles real citizen documents (NFR-SEC-4, security/security-architecture.md
§6), and periodically thereafter (at minimum annually or after major
architectural changes).

## 5. Findings Handling

Findings are triaged by severity into incident-response.md's tiers (a
critical pre-production finding blocks launch; a post-launch finding
follows the standard incident process) and tracked to resolution, not
just logged.
