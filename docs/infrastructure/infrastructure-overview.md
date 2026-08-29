# Infrastructure Overview

Status: v1.0 draft
Related: aws-architecture.md, docker.md, terraform.md, ci-cd.md, environments.md, networking.md

## 1. Cloud Provider

AWS, chosen for breadth of managed services matching this system's needs
(RDS with pgvector-compatible PostgreSQL, ElastiCache, ECS/Fargate, S3,
KMS, Secrets Manager) and mainstream familiarity for hiring/operating.

## 2. Core Managed Services in Use

| Need | Service |
|---|---|
| Compute (API + workers) | ECS/Fargate |
| Relational + vector database | RDS PostgreSQL (pgvector extension) |
| Cache/broker | ElastiCache Redis |
| Object storage | S3 |
| CDN/static hosting | CloudFront |
| Secrets | Secrets Manager |
| Encryption keys | KMS |
| IaC | Terraform |
| CI/CD | See ci-cd.md |

## 3. Read Order

1. **docker.md** — local development environment (the same shape as
   production, minus managed-service equivalents).
2. **aws-architecture.md** — production topology in detail.
3. **networking.md** — VPC, subnets, security groups.
4. **terraform.md** — how the above is defined as code.
5. **environments.md** — how local/staging/production differ and stay
   isolated.
6. **ci-cd.md** — how code moves from PR to production.

## 4. Guiding Principle

Infrastructure is defined as code (Terraform) and reproducible from
source control — this is both an operational-efficiency choice and a
disaster-recovery requirement (architecture/disaster-recovery.md §2).
