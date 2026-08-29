# CivicLens — System Context & Trust Boundaries

This document specifies system actor interactions and trust boundaries across untrusted, trusted, internal, and external domains.

---

## System Context Diagram

```mermaid
graph TB
    subgraph UNTRUSTED_BOUNDARY [Untrusted External World]
        CitizenUser[Citizen User]
        CSCAgent[CSC Operator / Agent]
        Attacker[Adversary / Web Scanner]
    end

    subgraph EDGE_BOUNDARY [Edge Protection & Ingress]
        WAF[WAF / AWS CloudFront]
        ALB[Application Load Balancer]
    end

    subgraph TRUSTED_INTERNAL_BOUNDARY [Trusted CivicLens VPC]
        API[FastAPI Application Cluster]
        Worker[Celery Background Workers]
        DB[(PostgreSQL + pgvector)]
        Redis[(Redis Session / Rate Limits)]
        S3[(AWS S3 Private Buckets)]
    end

    subgraph EXTERNAL_PROVIDERS [External Third-Party Services]
        LLM[AI Provider API - Gemini / OpenAI]
        SMS[SMS Gateway API - Twilio / Kaleyra]
        GovPortal[Government Submission API]
    end

    CitizenUser -->|TLS 1.3 / HTTPS| WAF
    CSCAgent -->|TLS 1.3 / HTTPS| WAF
    Attacker -->|Blocked Attack Requests| WAF
    WAF --> ALB
    ALB -->|Internal VPC Route| API
    
    API --> DB
    API --> Redis
    API --> S3
    API --> Worker
    Worker --> DB
    Worker --> S3
    
    API -.->|Least Privilege API Call| LLM
    Worker -.->|Short-lived API Call| SMS
    Worker -.->|Signed API Payload| GovPortal
```

---

## Boundary Controls

| Boundary | Interface | Authentication | Authorization | Validation | Failure Policy |
|---|---|---|---|---|---|
| **Untrusted -> Edge** | HTTPS (Port 443) | WAF Rules / TLS | Rate limiting per IP | Payload size check | HTTP 429 / 403 Block |
| **Edge -> API** | HTTP/2 (Port 8000) | JWT Bearer Token | Role check (`citizen`/`agent`/`admin`) | Pydantic strict parsing | HTTP 401 / 403 Response |
| **API -> DB** | TCP (Port 5432) | PostgreSQL TLS Credentials | Least privilege IAM / SQL User | Parameterized SQL | Transaction Rollback |
| **API -> Storage** | HTTPS S3 API | IAM Task Role | Short-lived signed S3 URLs | Magic byte inspection | HTTP 422 / 400 Error |
| **API -> Worker** | Redis Protocol (6379) | Auth Secret | Internal queue isolation | Typed Outbox envelope | Retry & Dead-letter queue |
| **Worker -> External**| HTTPS REST APIs | API Key / Bearer | Strict egress allowlist | Redacted PII payload | Circuit breaker & fallback |
