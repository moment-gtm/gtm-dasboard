"""Overlay saved Administration edits onto the freshly loaded platform (FR-ADM-01..03).

Runs after the seed `ref_*` tables are loaded and before the conformed zone is built, so edited
targets, thresholds and reference sets flow through every metric, status band and filter.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import duckdb

from app.platform import reference_sets
from app.platform.admin_store import get_admin_store

PCT_UNITS = {"pct", "ratio_to_pace", "ratio_to_goal"}


def _fmt(unit: str, value: float) -> str:
    if unit in PCT_UNITS:
        return f"{value * 100:g}%"
    if unit == "x":
        return f"{value:g}x"
    return f"{value:g}"


def band_label(unit: str, direction: str, on_track: float, watch: float) -> str:
    """Plain-language band description regenerated when a threshold is edited."""
    on, wa = _fmt(unit, on_track), _fmt(unit, watch)
    suffix = " days" if unit.startswith("days") else ""
    if direction == "higher":
        return f"{on}{suffix} or more / {wa} to {on}{suffix} / below {wa}{suffix}"
    return f"{on}{suffix} or fewer / {on} to {wa}{suffix} / over {wa}{suffix}"


def _targets(conn: duckdb.DuckDBPyConnection, as_of: date) -> None:
    store = get_admin_store()
    for v in store.target_versions():
        latest_source = conn.execute(
            "SELECT max(loaded_at) FROM raw_planning_target WHERE fiscal_year = ?", [v["fiscal_year"]]
        ).fetchone()[0]
        # Admin versions must outrank the planning source's own version of the same year.
        loaded_at = (latest_source or datetime.combine(as_of, datetime.min.time())) + timedelta(
            minutes=v["seq"]
        )
        conn.executemany(
            "INSERT INTO raw_planning_target VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    v["version"],
                    v["fiscal_year"],
                    r["quarter"],
                    r["practice"],
                    r["amount_usd"],
                    loaded_at,
                    as_of,
                )
                for r in store.target_rows(v["version"])
            ],
        )


def _thresholds(conn: duckdb.DuckDBPyConnection) -> None:
    for metric_id, t in get_admin_store().latest_thresholds().items():
        row = conn.execute(
            "SELECT direction, unit FROM ref_threshold WHERE metric_id = ?", [metric_id]
        ).fetchone()
        if row is None:
            continue
        direction, unit = row
        conn.execute(
            "UPDATE ref_threshold SET on_track = ?, watch = ?, label = ?, version = ? WHERE metric_id = ?",
            [
                t["on_track"],
                t["watch"],
                band_label(unit, direction, t["on_track"], t["watch"]),
                t["version"],
                metric_id,
            ],
        )


def apply_admin_overlay(conn: duckdb.DuckDBPyConnection, as_of: date) -> None:
    _targets(conn, as_of)
    _thresholds(conn)
    for key, saved in get_admin_store().latest_reference().items():
        if key in reference_sets.EDITABLE:
            reference_sets.apply(conn, key, saved["payload"])
