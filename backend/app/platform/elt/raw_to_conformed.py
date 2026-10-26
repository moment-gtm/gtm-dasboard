"""RAW -> CONFORMED: load governed reference data, run conformed SQL, apply DQ rules."""

from __future__ import annotations

import json
from datetime import date, datetime

import duckdb

from app.data import reference_data as ref
from app.platform.db import run_sql_file
from app.semantic import definitions
from app.semantic.dq import run_rules


def load_reference(conn: duckdb.DuckDBPyConnection, as_of: date, built_at: datetime) -> None:
    """ref_* tables (admin seed, Step 0.7). Editable through Administration in Step 4."""
    conn.execute("CREATE TABLE ref_run_context (as_of_date DATE, built_at TIMESTAMP)")
    conn.execute("INSERT INTO ref_run_context VALUES (?, ?)", [as_of, built_at])

    conn.execute(
        "CREATE TABLE ref_stage_probability (stage VARCHAR, probability DOUBLE, stage_order INTEGER)"
    )
    conn.executemany(
        "INSERT INTO ref_stage_probability VALUES (?, ?, ?)",
        [(s, p, ref.STAGE_ORDER[s]) for s, p in ref.STAGE_PROBABILITY.items()],
    )

    conn.execute("CREATE TABLE ref_fx_rate (currency VARCHAR, rate_to_usd DOUBLE)")
    conn.executemany("INSERT INTO ref_fx_rate VALUES (?, ?)", list(ref.PLAN_FX_TO_USD.items()))

    conn.execute("CREATE TABLE ref_industry_vertical (industry VARCHAR, vertical VARCHAR)")
    conn.executemany(
        "INSERT INTO ref_industry_vertical VALUES (?, ?)", list(ref.INDUSTRY_TO_VERTICAL.items())
    )

    conn.execute("""CREATE TABLE ref_threshold (metric_id VARCHAR, direction VARCHAR,
                    on_track DOUBLE, watch DOUBLE, unit VARCHAR, label VARCHAR, version INTEGER)""")
    conn.executemany(
        "INSERT INTO ref_threshold VALUES (?, ?, ?, ?, ?, ?, 1)",
        [
            (t["metric_id"], t["direction"], t["on_track"], t["watch"], t["unit"], t["label"])
            for t in ref.THRESHOLDS
        ],
    )

    conn.execute("""CREATE TABLE ref_bucket (bucket_key VARCHAR, label VARCHAR, min_days INTEGER,
                    max_days INTEGER, review BOOLEAN, sort_order INTEGER)""")
    conn.executemany(
        "INSERT INTO ref_bucket VALUES (?, ?, ?, ?, ?, ?)",
        [
            (b["key"], b["label"], b["min_days"], b["max_days"], b["review"], i)
            for i, b in enumerate(ref.AGEING_BUCKETS)
        ],
    )
    conn.execute("""CREATE TABLE ref_size_band (band_key VARCHAR, label VARCHAR, min_usd DOUBLE,
                    max_usd DOUBLE, sort_order INTEGER)""")
    conn.executemany(
        "INSERT INTO ref_size_band VALUES (?, ?, ?, ?, ?)",
        [(b["key"], b["label"], b["min_usd"], b["max_usd"], i) for i, b in enumerate(ref.SIZE_BANDS)],
    )

    conn.execute("CREATE TABLE ref_setting (key VARCHAR, value DOUBLE)")
    conn.executemany("INSERT INTO ref_setting VALUES (?, ?)", list(ref.SETTINGS.items()))

    for name, values in (
        ("dim_vertical", ref.VERTICALS),
        ("dim_practice", ref.PRACTICES),
        ("dim_platform", ref.PLATFORMS),
    ):
        conn.execute(f"CREATE TABLE {name} (name VARCHAR, sort_order INTEGER)")
        conn.executemany(f"INSERT INTO {name} VALUES (?, ?)", [(v, i) for i, v in enumerate(values)])

    conn.execute("""CREATE TABLE ref_metric_definition (metric_id VARCHAR, name VARCHAR,
                    definition VARCHAR, calculation VARCHAR, sources VARCHAR, owner VARCHAR,
                    refresh VARCHAR, dimensions VARCHAR)""")
    conn.executemany(
        "INSERT INTO ref_metric_definition VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                mid,
                m["name"],
                m["definition"],
                m["calculation"],
                json.dumps(m["sources"]),
                m["owner"],
                m["refresh"],
                json.dumps(m["dimensions"]),
            )
            for mid, m in definitions.METRICS.items()
        ],
    )

    conn.execute("""CREATE TABLE ref_source (source_id VARCHAR, key VARCHAR, name VARCHAR,
                    cadence VARCHAR, sla_hours INTEGER)""")
    conn.executemany(
        "INSERT INTO ref_source VALUES (?, ?, ?, ?, ?)",
        [(s["source_id"], s["key"], s["name"], s["cadence"], s["sla_hours"]) for s in ref.SOURCES],
    )


def build_conformed(conn: duckdb.DuckDBPyConnection) -> None:
    run_sql_file(conn, "schema_conformed.sql")


def apply_dq(conn: duckdb.DuckDBPyConnection) -> None:
    run_rules(conn)  # DQ-01..09 findings and the completeness series (app/semantic/dq.py)
