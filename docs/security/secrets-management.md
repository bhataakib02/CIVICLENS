# Secrets Management

Status: v1.0 draft
Related: security-architecture.md, infrastructure/environments.md, infrastructure/terraform.md

## 1. What Counts as a Secret

Database credentials, JWT signing keys, LLM/OCR/SMS provider API keys,
object storage credentials, KMS key references, third-party webhook
signing secrets.

## 2. Storage

All secrets live in a managed secrets store (e.g. AWS Secrets Manager /
Parameter Store), never in source control, `.env` files committed to the
repo, CI logs, or application config baked into container images. Local
development uses a `.env` file explicitly gitignored, seeded from
`.env.example` (which contains only placeholder values).

## 3. Access

- Backend services and workers assume least-privilege IAM roles that grant
  read access only to the specific secrets they need.
- Secrets are injected at runtime (environment variables populated from
  the secrets store at container start), never written to disk in plain
  form.
- Secret access is logged; unusual access patterns feed into
  operations/alerting.md.

## 4. Rotation

- Database credentials and API keys: rotated on a defined schedule and
  immediately on suspected compromise.
- JWT signing keys: supports dual-key rotation (old key still validates
  in-flight tokens for a grace period while new tokens are signed with the
  new key).

## 5. CI/CD

Secrets used in CI/CD pipelines (deploy credentials, etc.) are stored in
the CI platform's encrypted secrets store, scoped per-environment
(staging secrets never usable against production), and never printed to
build logs (infrastructure/ci-cd.md).
