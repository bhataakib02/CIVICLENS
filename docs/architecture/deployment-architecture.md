# Deployment Architecture

Status: v1.0 draft
Related: system-architecture.md, infrastructure/aws-architecture.md, infrastructure/environments.md, infrastructure/ci-cd.md

## 1. Topology (AWS, summary — full detail in infrastructure/aws-architecture.md)

```
Internet
   │
   ▼
CloudFront (static assets, apps/web + apps/admin build output)
   │
   ▼
ALB (TLS termination)
   │
   ▼
ECS/Fargate service — FastAPI backend (autoscaling, stateless)
   │              │
   ▼              ▼
RDS PostgreSQL   ElastiCache Redis
(+ pgvector,     (Celery broker,
 Multi-AZ)        cache)
   │
   ▼
ECS/Fargate — Celery worker service (autoscaling on queue depth)
   │
   ▼
S3 (documents, generated PDFs) — private, KMS-encrypted
```

## 2. Environments

Local (Docker Compose) → staging → production, each with fully isolated
RDS instances, S3 buckets, and secrets (infrastructure/environments.md).
Staging mirrors production topology at reduced scale for realistic
pre-release testing (load tests, E2E per testing/e2e-testing.md and
testing/load-testing.md).

## 3. Scaling

- API tier: horizontal autoscaling on request concurrency/CPU (ADR-001,
  NFR-SCALE-1).
- Worker tier: horizontal autoscaling on Celery queue depth
  (NFR-SCALE-2).
- Database: vertical scaling + read replicas if read load grows;
  `knowledge_chunks` vector search is the most likely first bottleneck to
  watch (NFR-SCALE-3).

## 4. CI/CD

See infrastructure/ci-cd.md for the full pipeline; summary: PR → lint/
test/contract-test/security-scan gates → merge → build container images →
deploy to staging automatically → deploy to production on manual approval
(or automatic for patch-level changes, per the release policy).

## 5. Zero-Downtime Deploys

Rolling deploys behind the ALB (old and new task versions briefly coexist);
database migrations follow the two-step deprecate/backfill/remove pattern
for anything backward-incompatible (database/migration-strategy.md), so a
mid-deploy request never hits a schema mismatch.
