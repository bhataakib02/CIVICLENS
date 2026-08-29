# CivicLens — Performance & Load Benchmark Report

This document records empirical performance test results for CivicLens across core application subsystems.

---

## Performance Test Results Summary

| Benchmark | Environment | Sample Size | Observed Result | Target Budget | Status |
|---|---|---|---|---|---|
| **Deterministic Engine Eval** | Local Python 3.11 | 50 iterations | **1.82 ms** / eval | < 10.0 ms | **PASSED** |
| **Argon2id Password Verify** | Local CPU (Single Core) | 10 iterations | **174.5 ms** / verify | < 500.0 ms | **PASSED** |
| **API Throughput Baseline** | FastAPI + Uvicorn | 100 req/sec | **280 req/sec** peak | > 100 req/sec | **PASSED** |
| **Pagination Hard-Cap** | FastAPI Router | 1,000,000 limit | **HTTP 422 Rejected** | Max 100 limit | **PASSED** |
