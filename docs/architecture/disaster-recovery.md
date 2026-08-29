# Disaster Recovery

Status: v1.0 draft
Related: operations/backup-restore.md, NFR-AVAIL-4, deployment-architecture.md

## 1. Targets

RPO ≤ 15 minutes, RTO ≤ 4 hours (NFR-AVAIL-4), covering the primary
PostgreSQL database and S3 document storage.

## 2. Backup Mechanisms

- **Database**: automated daily snapshots + continuous point-in-time
  recovery (RDS PITR) covering the RPO target; snapshots encrypted with
  the same KMS keys as the live database.
- **Object storage**: S3 versioning enabled on document buckets, plus
  cross-region replication for the disaster (not just accidental-delete)
  recovery case.
- **Infrastructure as code**: the full environment (infrastructure/
  terraform.md) is reproducible from source control, so a full-region
  failure can rebuild infrastructure from scratch, not just restore data.

## 3. Recovery Scenarios & Procedures

Full runbooks live in operations/runbooks.md; summary:
- **Accidental data corruption/deletion**: PITR restore to a point before
  the incident, into a new instance, verify, then cut over.
- **Full database instance failure**: Multi-AZ automatic failover
  (minutes, not a DR event in the traditional sense) or, if that fails,
  restore from the latest snapshot.
- **Full region outage**: rebuild infrastructure via Terraform in a
  secondary region, restore database from cross-region-replicated
  backups, restore documents from cross-region-replicated S3 — tested
  periodically as a game-day exercise, not assumed to work untested.

## 4. Testing

DR procedures are exercised on a defined periodic cadence (at minimum
before major architectural changes and annually otherwise) — an untested
backup is not a reliable backup.
