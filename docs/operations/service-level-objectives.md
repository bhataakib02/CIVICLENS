# CivicLens — Service Level Objectives (SLOs)

This document defines performance, latency, availability, and throughput target SLOs for CivicLens.

---

## SLO Metrics & Targets

| Metric | Target (SLO) | Measurement Method | Severity Level |
|---|---|---|---|
| **API Service Availability** | 99.9% Uptime | HTTP `/health/ready` probe (ALB metric) | CRITICAL |
| **API Response Latency (p95)** | < 120 ms | Prometheus `http_request_duration_seconds` | HIGH |
| **Eligibility Engine Latency** | < 10.0 ms | Internal benchmark suite (`test_performance_suite.py`) | HIGH |
| **Document Processing Time** | < 5.0 s (p95) | Celery task processing duration metric | MEDIUM |
| **RAG Query Latency** | < 1.5 s (p95) | FastAPI AI router timer | MEDIUM |
| **Notification Dispatch** | < 2.0 s (p95) | Transactional Outbox latency | MEDIUM |
