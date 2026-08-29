# Backup & Restore

Status: v1.0 draft
Related: architecture/disaster-recovery.md, security/data-protection.md §5, product/non-functional-requirements.md (NFR-AVAIL-4)

## 1. Targets

RPO ≤ 15 minutes, RTO ≤ 4 hours (NFR-AVAIL-4).

## 2. Database (PostgreSQL/RDS)

- Automated daily full snapshots, retained per retention-policy.md's
  backup-lifecycle schedule.
- Continuous point-in-time recovery (WAL-based), satisfying the 15-minute
  RPO target.
- Snapshots encrypted with the same KMS keys as the live database
  (security/data-protection.md §1).
- Cross-region snapshot copy for disaster-recovery scenarios
  (architecture/disaster-recovery.md §2).

## 3. Object Storage (S3)

- Versioning enabled on all document/PDF buckets — protects against
  accidental overwrite/delete, not just full-bucket loss.
- Cross-region replication for the region-outage disaster scenario.

## 4. Restore Procedure (summary — full runbook in runbooks.md)

1. Identify target restore point (specific timestamp for PITR, or a
   specific snapshot).
2. Restore into a **new** RDS instance (never restore over the live
   instance in place) — verify data integrity and application health
   against the restored instance before cutover.
3. Cut over (DNS/connection string update) once verified.
4. Post-restore: audit what data (if any) was lost in the gap between the
   restore point and the incident, and whether any citizen-facing
   communication is warranted.

## 5. Testing

Restore procedures are exercised periodically (at minimum before major
architectural changes and on a recurring schedule otherwise) as a game-day
exercise — per architecture/disaster-recovery.md §4, an untested backup is
not treated as a verified recovery capability.
