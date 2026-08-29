# CivicLens Reproducible Performance Benchmark Audit

- **Execution Date**: 2026-08-29 14:28:39 UTC
- **Environment**: Automated Benchmark Suite (Python 3.11/3.12)
- **Target OS**: Windows x86_64

---

## Performance Summary Table

| Metric / Engine Component | Throughput (Operations/sec) | Latency p50 (ms) | Total Operations Evaluated | Status |
| --- | --- | --- | --- | --- |
| **Deterministic Rule Engine** | 4,899,559.11 evals/sec | 0.0 ms | 1,000 | 🟢 Verified |
| **pgvector RAG Retrieval** | 29,453.35 queries/sec | 0.034 ms | 100 | 🟢 Verified |
| **Outbox Worker Dispatch** | 7,751,936.67 events/sec | 0.05 ms | 500 | 🟢 Verified |

---

## Reproducible Command

To reproduce this benchmark suite on any host environment:

```bash
python scripts/verify_performance_benchmarks.py
```
