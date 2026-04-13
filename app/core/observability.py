import statistics
import threading
import time
from collections import deque
from typing import Deque, Dict, List, Optional

from loguru import logger


def _format_fields(fields: Dict[str, object]) -> str:
    parts = []
    for key, value in fields.items():
        if value is None:
            continue
        sanitized = str(value).replace("\n", " ").strip()
        parts.append(f"{key}={sanitized}")
    return " | ".join(parts)


def log_event(level: str, event: str, **fields: object) -> None:
    message = event if not fields else f"{event} | {_format_fields(fields)}"
    getattr(logger, level)(message)


class ObservabilityService:
    def __init__(self) -> None:
        self.started_at = time.time()
        self._lock = threading.Lock()
        self._http_metrics: Dict[str, Dict[str, object]] = {}
        self._llm_metrics: Dict[str, Dict[str, object]] = {}

    def _ensure_metric(self, store: Dict[str, Dict[str, object]], key: str) -> Dict[str, object]:
        metric = store.get(key)
        if metric is None:
            metric = {
                "count": 0,
                "errors": 0,
                "durations_ms": deque(maxlen=200),
                "last_status": None,
                "last_error": None,
                "last_seen_at": None,
            }
            store[key] = metric
        return metric

    def record_http(
        self,
        route: str,
        method: str,
        status_code: int,
        duration_ms: float,
        error: Optional[str] = None,
    ) -> None:
        key = f"{method} {route}"
        with self._lock:
            metric = self._ensure_metric(self._http_metrics, key)
            metric["count"] += 1
            if status_code >= 400 or error:
                metric["errors"] += 1
            metric["durations_ms"].append(duration_ms)
            metric["last_status"] = status_code
            metric["last_error"] = error
            metric["last_seen_at"] = time.time()

    def record_llm(
        self,
        provider: str,
        model: str,
        stage: str,
        duration_ms: float,
        success: bool,
        error_category: Optional[str] = None,
    ) -> None:
        key = f"{provider}:{model}:{stage}"
        with self._lock:
            metric = self._ensure_metric(self._llm_metrics, key)
            metric["count"] += 1
            if not success:
                metric["errors"] += 1
            metric["durations_ms"].append(duration_ms)
            metric["last_status"] = "success" if success else "failed"
            metric["last_error"] = error_category
            metric["last_seen_at"] = time.time()

    def _summarize_metric(self, key: str, metric: Dict[str, object]) -> Dict[str, object]:
        durations = list(metric["durations_ms"])
        average_ms = round(statistics.mean(durations), 2) if durations else 0.0
        max_ms = round(max(durations), 2) if durations else 0.0
        p95_ms = round(self._percentile(durations, 0.95), 2) if durations else 0.0
        return {
            "key": key,
            "count": metric["count"],
            "errors": metric["errors"],
            "average_ms": average_ms,
            "p95_ms": p95_ms,
            "max_ms": max_ms,
            "last_status": metric["last_status"],
            "last_error": metric["last_error"],
            "last_seen_at": metric["last_seen_at"],
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        if not data:
            return 0.0
        ordered = sorted(data)
        index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * percentile))))
        return ordered[index]

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            http_items = [
                self._summarize_metric(key, metric) for key, metric in self._http_metrics.items()
            ]
            llm_items = [
                self._summarize_metric(key, metric) for key, metric in self._llm_metrics.items()
            ]

        http_items.sort(key=lambda item: item["average_ms"], reverse=True)
        llm_items.sort(key=lambda item: item["average_ms"], reverse=True)

        return {
            "status": "ok",
            "uptime_seconds": round(time.time() - self.started_at, 2),
            "http": {
                "total_routes": len(http_items),
                "routes": http_items,
                "slowest_routes": http_items[:5],
            },
            "llm": {
                "total_models": len(llm_items),
                "models": llm_items,
                "slowest_models": llm_items[:5],
            },
        }

    def reset(self) -> None:
        with self._lock:
            self.started_at = time.time()
            self._http_metrics = {}
            self._llm_metrics = {}


observability_service = ObservabilityService()
