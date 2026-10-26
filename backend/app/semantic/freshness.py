"""Per-source freshness from the ELT run log (FR-GEN-07 last refresh, FR-GEN-09 staleness)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.config import settings
from app.platform.db import Platform


def last_success(platform: Platform, key: str) -> datetime | None:
    """Time of the extract currently loaded for a source (older than the run if it failed)."""
    return platform.scalar(
        "SELECT max(extracted_at) FROM elt_run_log WHERE source_key = ? AND rows > 0", [key]
    )


def iso(ts: datetime | None) -> str | None:
    return None if ts is None else ts.replace(tzinfo=UTC).isoformat()


def source_health(platform: Platform) -> list[dict]:
    now = datetime.now(UTC).replace(tzinfo=None)
    out = []
    for s in platform.query("SELECT * FROM ref_source ORDER BY source_id"):
        last = platform.query(
            """SELECT status, message, started_at, rows FROM elt_run_log
               WHERE source_key = ? ORDER BY started_at DESC LIMIT 1""",
            [s["key"]],
        )
        attempt = last[0] if last else None
        ok_at = last_success(platform, s["key"])
        if attempt is None or attempt["status"] == "failed":
            status = "failed"
        elif (
            s["key"] in settings.mock_stale_sources
            or ok_at is None
            or now - ok_at > timedelta(hours=s["sla_hours"])
        ):
            status = "stale"
        else:
            status = "fresh"
        message = attempt["message"] if attempt else "Never loaded"
        if status == "stale" and not message:
            message = f"Older than its refresh SLA ({s['cadence']})"
        out.append(
            {
                "source_id": s["source_id"],
                "key": s["key"],
                "name": s["name"],
                "cadence": s["cadence"],
                "last_success": iso(ok_at),
                "last_attempt": iso(attempt["started_at"]) if attempt else None,
                "status": status,
                "rows": int(attempt["rows"]) if attempt else 0,
                "message": message,
            }
        )
    return out
