"""ELT orchestration: extract -> raw -> conformed -> marts, with a run log (NFR-12).

A failing source does not stop the run: its last good extract is re-used (data goes stale and
/api/health reports it), or its raw tables stay empty if it has never loaded — so the UI can
show the right staleness banner and empty/error states (FR-GEN-09, FR-GEN-13).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import duckdb

from app.config import settings
from app.connectors.base import SourceUnavailable
from app.connectors.mock import connectors
from app.platform.db import Platform, export_snapshot, run_sql_file
from app.platform.elt.admin_overlay import apply_admin_overlay
from app.platform.elt.extract_load import LOADERS
from app.platform.elt.raw_to_conformed import apply_dq, build_conformed, load_reference
from app.platform.snapshot import SnapshotBuilder

log = logging.getLogger(__name__)

# Survive store rebuilds: run history (elt_run_log) and last good extract per source.
RUN_HISTORY: list[dict] = []
_LAST_GOOD: dict[str, tuple[dict, datetime]] = {}
MAX_HISTORY = 500


def _record(
    source_key: str,
    step: str,
    status: str,
    rows: int,
    started: datetime,
    message: str | None = None,
    extracted_at: datetime | None = None,
) -> None:
    RUN_HISTORY.append(
        {
            "source_key": source_key,
            "step": step,
            "status": status,
            "rows": rows,
            "started_at": started,
            "finished_at": datetime.now(UTC).replace(tzinfo=None),
            "message": message,
            "extracted_at": extracted_at,
        }
    )
    del RUN_HISTORY[:-MAX_HISTORY]
    if status == "failed":
        # NFR-12: failures must reach the data team within 30 minutes (alert hook stub).
        log.error("ELT failure source=%s step=%s: %s", source_key, step, message)


def build_platform() -> Platform:
    built_at = datetime.now(UTC).replace(tzinfo=None)
    as_of = settings.demo_today
    conn = duckdb.connect(":memory:")
    run_sql_file(conn, "schema_raw.sql")

    for connector in connectors():
        started = datetime.now(UTC).replace(tzinfo=None)
        try:
            payload = connector.extract()
            _LAST_GOOD[connector.key] = (payload, started)
            rows = LOADERS[connector.key](conn, payload, as_of)
            _record(connector.key, "extract_load", "success", rows, started, extracted_at=started)
        except SourceUnavailable as exc:
            last = _LAST_GOOD.get(connector.key)
            rows = LOADERS[connector.key](conn, last[0], as_of) if last else 0
            _record(
                connector.key,
                "extract_load",
                "failed",
                rows,
                started,
                str(exc),
                extracted_at=last[1] if last else None,
            )

    started = datetime.now(UTC).replace(tzinfo=None)
    load_reference(conn, as_of, built_at)
    apply_admin_overlay(conn, as_of)  # saved targets / thresholds / reference edits
    build_conformed(conn)
    snapshots = SnapshotBuilder(conn)
    snapshots.create()
    snap_rows = snapshots.backfill(as_of)
    apply_dq(conn)
    run_sql_file(conn, "schema_marts.sql")
    _record("platform", "transform", "success", snap_rows, started)

    conn.execute("""CREATE TABLE elt_run_log (source_key VARCHAR, step VARCHAR, status VARCHAR,
                    rows BIGINT, started_at TIMESTAMP, finished_at TIMESTAMP, message VARCHAR,
                    extracted_at TIMESTAMP)""")
    conn.executemany(
        "INSERT INTO elt_run_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                r["source_key"],
                r["step"],
                r["status"],
                r["rows"],
                r["started_at"],
                r["finished_at"],
                r["message"],
                r["extracted_at"],
            )
            for r in RUN_HISTORY
        ],
    )

    export_snapshot(conn, settings.snapshot_db_path)
    return Platform(conn=conn, as_of_date=as_of, built_at=built_at)
