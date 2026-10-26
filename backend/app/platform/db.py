"""DuckDB data platform: connection lifecycle and query helpers.

The prototype builds the whole platform (raw -> conformed -> marts) into a fresh in-memory
DuckDB on each ELT run and swaps it in atomically, so readers never see a half-built store.
A read-only file copy is written for inspection tools (e.g. the DuckDB MCP server).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb

log = logging.getLogger(__name__)
SQL_DIR = Path(__file__).resolve().parent


@dataclass
class Platform:
    conn: duckdb.DuckDBPyConnection
    as_of_date: date
    built_at: datetime

    def query(self, sql: str, args: list[Any] | None = None) -> list[dict]:
        cur = self.conn.cursor()  # one cursor per call: safe across request threads
        try:
            rel = cur.execute(sql, args or [])
            cols = [d[0] for d in rel.description]
            return [dict(zip(cols, row)) for row in rel.fetchall()]
        finally:
            cur.close()

    def scalar(self, sql: str, args: list[Any] | None = None) -> Any:
        rows = self.query(sql, args)
        return next(iter(rows[0].values())) if rows else None


_current: Platform | None = None
_lock = threading.Lock()


def run_sql_file(conn: duckdb.DuckDBPyConnection, name: str) -> None:
    conn.execute((SQL_DIR / name).read_text(encoding="utf8"))


def get_platform() -> Platform:
    global _current
    if _current is None:
        rebuild()
    assert _current is not None
    return _current


def rebuild() -> Platform:
    """Run the full ELT into a new store and swap it in."""
    from app.platform.elt.run import build_platform  # local import: avoid cycle

    global _current
    with _lock:
        platform = build_platform()
        old, _current = _current, platform
    if old is not None:
        old.conn.close()
    return platform


def export_snapshot(conn: duckdb.DuckDBPyConnection, path: Path) -> None:
    """Write a file copy of the platform for read-only inspection (best effort)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp.duckdb")
        if tmp.exists():
            tmp.unlink()
        conn.execute(f"ATTACH '{tmp.as_posix()}' AS snap")
        conn.execute("COPY FROM DATABASE memory TO snap")
        conn.execute("DETACH snap")
        tmp.replace(path)
    except Exception as exc:  # file locked by a reader, read-only disk, etc.
        log.warning("Platform snapshot export skipped: %s", exc)
