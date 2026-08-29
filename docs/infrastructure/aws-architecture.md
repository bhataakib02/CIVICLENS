# AWS Architecture

Status: v1.0 draft
Related: infrastructure-overview.md, architecture/deployment-architecture.md, networking.md, terraform.md

## 1. Account Structure

Separate AWS accounts (or, at minimum, fully isolated VPCs/resource sets)
per environment (staging, production) per environments.md — no shared
database or bucket between environments, ever, precisely to prevent a
staging bug from touching production citizen data.

## 2. Compute

ECS/Fargate for both the API service and the Celery worker service —
serverless container operation avoids managing EC2 fleets directly;
Fargate task definitions set explicit CPU/memory per service, sized
against load-testing.md results, not guessed.

## 3. Database

RDS PostgreSQL, Multi-AZ for production (automatic failover), with the
`pgvector` extension enabled. Automated backups + PITR per
architecture/disaster-recovery.md. Parameter group tuned for the
`knowledge_chunks` vector-search workload alongside standard OLTP queries.

## 4. Cache/Broker

ElastiCache Redis, Multi-AZ for production. Used for Celery broker,
eligibility-result caching, and rate-limit counters (security/rate-limiting.md)
— a single Redis cluster serves all three, since none of these workloads
individually justifies a separate cluster at launch scale.

## 5. Storage

S3 for documents and generated PDFs, private buckets, KMS server-side
encryption, versioning enabled, cross-region replication for DR
(architecture/disaster-recovery.md §2).

## 6. Edge/CDN

CloudFront in front of S3-hosted static frontend builds (`apps/web`,
`apps/admin`), with the API origin behind an ALB for dynamic requests.

## 7. Security Boundary

All compute and data services live in private subnets; only the ALB and
CloudFront have public-facing endpoints (networking.md). IAM roles are
scoped per-service (least privilege) — the OCR worker's role, for
instance, cannot read the full breadth of S3 buckets, only the documents
prefix it needs.
