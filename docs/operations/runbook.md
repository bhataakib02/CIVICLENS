# CivicLens — Operational Runbook & Incident Response

This runbook details step-by-step procedures for diagnosing and mitigating operational incidents across the CivicLens platform.

---

## Incident Response Procedures

### 1. API Outage / High Error Rate (HTTP 5xx)
- **Symptoms**: Elevated 500/502 errors on ALB metrics; container liveness probes failing.
- **Diagnosis**:
  ```bash
  docker compose logs --tail=100 backend
  ```
- **Recovery**:
  ```bash
  docker compose restart backend
  ```
- **Verification**: `curl -f http://localhost:8000/api/v1/health/ready`

---

### 2. Database Connection Exhaustion (PostgreSQL)
- **Symptoms**: `sqlalchemy.exc.TimeoutError: QueuePool limit exceeded`.
- **Diagnosis**: Inspect active connections:
  ```sql
  SELECT count(*), state FROM pg_stat_activity GROUP BY state;
  ```
- **Recovery**: Terminate idle transactions and restart FastAPI container:
  ```bash
  docker compose restart backend
  ```

---

### 3. Redis / Worker Outage
- **Symptoms**: Notifications delayed; document OCR processing jobs remaining in `PENDING` state.
- **Diagnosis**: Inspect Redis ping & Celery worker logs:
  ```bash
  docker compose exec redis redis-cli ping
  docker compose logs --tail=100 worker
  ```
- **Recovery**: Restart Redis & Celery worker cluster:
  ```bash
  docker compose restart redis worker
  ```
