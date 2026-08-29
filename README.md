# CivicLens — Public Welfare Scheme Discovery & Application Platform

CivicLens is a civic tech platform built to empower citizens with automated welfare scheme discovery, eligibility evaluation, document verification, application tracking, and operational case management.

---

## 🚀 Quick Start: Local Full-Stack Setup (Docker Compose)

Clone the repository and spin up the complete local environment in a single command:

```bash
# 1. Clone repository
git clone https://github.com/bhataakib02/CIVICLENS.git
cd CIVICLENS

# 2. Copy environment template
cp .env.example .env

# 3. Spin up full stack (PostgreSQL+pgvector, Redis, API, Worker, Web, Admin)
docker compose up -d

# 4. Run database migrations
docker compose exec api alembic upgrade head

# 5. Run test suite
docker compose exec api pytest -v
```

### Access Local Services:
- **Citizen Web App**: [http://localhost:3000](http://localhost:3000)
- **Admin / CSC Operations Console**: [http://localhost:3001](http://localhost:3001)
- **FastAPI OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic
- **Database**: PostgreSQL 16 + `pgvector`
- **Cache & Queue**: Redis 7
- **Citizen Frontend**: Next.js 14 + React 18 + Tailwind CSS
- **Admin Console**: Next.js 14 + Capability-based Authorization + Policy Simulation Engine
- **Containerization**: Multi-stage Docker build files
- **Infrastructure as Code**: Terraform AWS Modules (`networking`, `database`, `redis`, `storage`, `ecs`, `load-balancer`, `iam`, `secrets`, `monitoring`)
- **CI/CD Pipeline**: GitHub Actions with Ruff, Pytest, OpenAPI validation, Bandit SAST, and Trivy security scanning.
