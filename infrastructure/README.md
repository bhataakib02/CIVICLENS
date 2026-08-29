# `infrastructure` — Terraform IaC

All AWS infrastructure for staging and production, defined as code. See
`docs/infrastructure/*` for the full narrative documentation; this README
is the entry point for someone about to make a change.

## Structure

```
infrastructure/
├── modules/          # networking, compute, database, cache, storage, edge
└── environments/
    ├── staging/
    └── production/
```

See `docs/infrastructure/terraform.md` for module design principles and
`docs/infrastructure/environments.md` for how staging/production stay
isolated.

## Before Changing Anything Here

1. Read `docs/infrastructure/aws-architecture.md` and
   `docs/infrastructure/networking.md` for the target topology.
2. Run `terraform plan` locally against a scratch/dev state if possible;
   never run `apply` directly against staging/production from a local
   machine — changes go through the PR process
   (`docs/infrastructure/terraform.md` §3) and CI/CD
   (`docs/infrastructure/ci-cd.md`).
3. No console-created ("ClickOps") resources in staging/production —
   drift detection will flag them, and they should be imported into
   Terraform or removed, not left as untracked exceptions.

## Rules

- Every resource used by staging/production is defined here.
- Secrets referenced here point to the managed secrets store
  (`docs/security/secrets-management.md`) — never hardcoded values.
- Update `docs/infrastructure/*` when topology changes materially.
