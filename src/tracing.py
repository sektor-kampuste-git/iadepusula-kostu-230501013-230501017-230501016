"""Yerel, içerik taşımayan JSONL çalışma izi; gerçek başvuruları diske yazmaz."""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.agent import RunReport


def write_trace(report: RunReport, path: Path) -> None:
    """Yalnız izinli özet alanlarını yaz; draft alanı hiçbir zaman dahil edilmez."""
    safe = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        **report.model_dump(
            mode="json",
            include={
                "request_id",
                "reason",
                "model_calls",
                "tool_calls",
                "accounted_usd",
                "known_usage_usd",
                "cost_contains_reservation",
                "elapsed_ms",
                "events",
                "insan_onayi_gerekiyor_mu",
            },
        ),
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(safe, ensure_ascii=False) + "\n")
