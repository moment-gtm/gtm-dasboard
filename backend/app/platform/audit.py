"""audit_log (NFR-07): restricted-metric access, target/threshold changes and exports, kept 12 months.

Stored in its own DuckDB file so it survives platform rebuilds.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path

import duckdb

RETENTION_MONTHS = 12


class AuditLog:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = duckdb.connect(str(path))
        self._conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
                   ts TIMESTAMP, upn VARCHAR, role VARCHAR, action VARCHAR, resource VARCHAR,
                   status INTEGER, detail VARCHAR)""")
        self._conn.execute(f"DELETE FROM audit_log WHERE ts < now() - INTERVAL {RETENTION_MONTHS} MONTH")

    def record(
        self,
        *,
        upn: str | None,
        role: str | None,
        action: str,
        resource: str,
        status: int,
        detail: dict | None = None,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    datetime.now(UTC).replace(tzinfo=None),
                    upn,
                    role,
                    action,
                    resource,
                    status,
                    json.dumps(detail or {}, default=str),
                ],
            )

    def recent(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rel = self._conn.execute("SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", [limit])
            cols = [d[0] for d in rel.description]
            return [dict(zip(cols, r)) for r in rel.fetchall()]

    def close(self) -> None:
        self._conn.close()


_audit: AuditLog | None = None


def get_audit() -> AuditLog:
    global _audit
    if _audit is None:
        from app.config import settings

        _audit = AuditLog(settings.audit_db_path)
    return _audit
