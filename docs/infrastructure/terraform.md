# Terraform

Status: v1.0 draft
Related: infrastructure-overview.md, aws-architecture.md, environments.md, architecture/disaster-recovery.md §2

## 1. Structure

```
infrastructure/
├── modules/
│   ├── networking/     # VPC, subnets, security groups
│   ├── compute/         # ECS clusters, services, task definitions
│   ├── database/        # RDS, parameter groups, backup config
│   ├── cache/            # ElastiCache
│   ├── storage/          # S3 buckets, lifecycle rules
│   └── edge/              # CloudFront, ALB
└── environments/
    ├── staging/           # module composition + environment-specific vars
    └── production/
```

## 2. Principles

- Every AWS resource used in staging/production is defined here — no
  console-created ("ClickOps") resources in shared environments; drift
  detection (`terraform plan` on a schedule) catches and flags any
  manual changes.
- Environment-specific values (instance sizes, scaling thresholds) are
  variables per environment, not hardcoded in modules — the same module
  code deploys both staging (smaller) and production (full-scale)
  topologies.
- State is stored remotely (S3 backend + DynamoDB lock table) with
  encryption and versioning, so state itself is recoverable and
  concurrent-apply-safe.

## 3. Change Process

Terraform changes go through the same PR review process as application
code (CONTRIBUTING.md §5); `terraform plan` output is posted to the PR for
reviewer visibility before `apply`, and production applies require
explicit approval, mirroring the deploy-approval gate in ci-cd.md.

## 4. Disaster Recovery Role

Because the full environment is defined here, a full-region rebuild
(architecture/disaster-recovery.md §3) is a `terraform apply` against a
secondary region's environment configuration, followed by data restore
from cross-region-replicated backups — not a manual, undocumented
rebuild process.
