"""Lightweight in-process metrics (prompt §51, Part XII).

No external metrics backend is configured, so this is a thread-safe in-memory
counter/gauge registry that structured logs and a debug endpoint can read. In
production these would be exported to Prometheus/CloudWatch; the interface here
(incr/observe/gauge) is what a real exporter would wrap.

Metric names:
  outbox_events_created / _processed / _failed / _dead_lettered
  notifications_created / _sent / _failed
  notification_delivery_latency_ms (observation)
  outbox_queue_depth (gauge)
  websocket_connections (gauge) / websocket_delivery_failures (counter)
  notification_retry_count (counter)
  opportunity_crawl_runs_total / _failures_total
  opportunity_discovered_total / _updated_total / _closed_total
  opportunity_link_failures_total / _extraction_failures_total
  opportunity_crawl_duration_seconds / _publication_delay_seconds (observations)
"""
from __future__ import annotations

import threading
from collections import defaultdict


class _Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._observations: dict[str, list[float]] = defaultdict(list)

    def incr(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[name] += value

    def gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            obs = self._observations[name]
            obs.append(value)
            # Bound memory: keep the last 1000 observations.
            if len(obs) > 1000:
                del obs[: len(obs) - 1000]

    def snapshot(self) -> dict:
        with self._lock:
            def _summ(vals: list[float]) -> dict:
                if not vals:
                    return {"count": 0}
                s = sorted(vals)
                return {
                    "count": len(s),
                    "min": s[0],
                    "max": s[-1],
                    "avg": sum(s) / len(s),
                    "p95": s[min(len(s) - 1, int(len(s) * 0.95))],
                }

            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "observations": {k: _summ(v) for k, v in self._observations.items()},
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._observations.clear()


metrics = _Metrics()
