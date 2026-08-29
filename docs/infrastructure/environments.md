# Environments

Status: v1.0 draft
Related: aws-architecture.md, terraform.md, security/secrets-management.md

## 1. Environment List

| Environment | Purpose | Data |
|---|---|---|
| Local | Individual development (Docker Compose, docker.md) | Synthetic/fixture only |
| Staging | Pre-release validation, E2E and load testing | Synthetic/fixture only — never real citizen PII |
| Production | Live citizen traffic | Real citizen data, full security controls active |

## 2. Isolation Guarantees

- Fully separate AWS accounts (or equivalently isolated VPCs) per
  environment (aws-architecture.md §1).
- Fully separate databases, object storage buckets, and secrets — no
  environment reads or writes another's data under any circumstance.
- Separate LLM/OCR/SMS provider API keys per environment, so staging load
  tests never consume production rate limits or vice versa, and a staging
  incident can't leak into production provider account state.

## 3. Data Flow Between Environments

Data flows one direction only: schema/migrations and application code
promote from local → staging → production via the CI/CD pipeline
(ci-cd.md). Data itself never flows backward (production data is never
copied into staging, even for debugging) — debugging uses synthetic
fixtures reproducing the reported issue's shape, consistent with
testing/testing-strategy.md §10's "no real PII outside production" rule.

## 4. Access Control

Production access (database, SSH/exec into containers, direct AWS console
access) is restricted to a minimal on-call/ops set of accounts, MFA-
required, and itself audit-logged — access to citizen data in production
is treated with the same seriousness as any other sensitive-data access
path described in security/authorization-model.md.
