"""SnapshotBuilder — weekly snapshot of open opportunities (FR-GEN-11).

Production: capture every Monday 00:00 IST, retained 3 years (RSD 7.3).
Prototype: the store is rebuilt from the mock extract each run, so history is backfilled by
replaying stage history to each Monday. Close date and TCV use the current record values
(the mock CRM has no field history for them) — the stage at each snapshot is exact.
"""

from __future__ import annotations

from datetime import date

import duckdb

SNAPSHOT_START = date(2025, 1, 6)  # first Monday of FY25
RETENTION_YEARS = 3

OPEN_STAGES_SQL = "('Identify', 'Qualify', 'Propose', 'Orals', 'Negotiate')"


class SnapshotBuilder:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def create(self) -> None:
        self.conn.execute("""CREATE TABLE fact_opportunity_snapshot (
                   snapshot_date DATE, opportunity_id VARCHAR, stage VARCHAR, tcv_usd DOUBLE,
                   close_date DATE, std_probability DOUBLE)""")

    def backfill(self, as_of: date) -> int:
        """Replay stage history to every Monday from SNAPSHOT_START to as_of."""
        self.conn.execute(
            f"""
            INSERT INTO fact_opportunity_snapshot
            WITH snaps AS (
                SELECT CAST(d AS DATE) AS snapshot_date
                FROM range(CAST(? AS TIMESTAMP), CAST(? AS TIMESTAMP) + INTERVAL 1 DAY,
                           INTERVAL 7 DAY) t(d)
            )
            SELECT s.snapshot_date, h.opportunity_id, h.stage, f.tcv_usd, f.close_date,
                   sp.probability
            FROM snaps s
            JOIN fact_stage_history h
              ON h.entered_date <= s.snapshot_date
             AND (h.exited_date IS NULL OR h.exited_date > s.snapshot_date)
            JOIN fact_opportunity f USING (opportunity_id)
            JOIN ref_stage_probability sp ON sp.stage = h.stage
            WHERE h.stage IN {OPEN_STAGES_SQL}
            """,
            [SNAPSHOT_START, as_of],
        )
        return self.conn.execute("SELECT count(*) FROM fact_opportunity_snapshot").fetchone()[0]

    def capture(self, snapshot_date: date) -> int:
        """Weekly capture of the current open book (scheduler job, Mon 00:00 IST)."""
        self.conn.execute("DELETE FROM fact_opportunity_snapshot WHERE snapshot_date = ?", [snapshot_date])
        self.conn.execute(
            f"""INSERT INTO fact_opportunity_snapshot
                SELECT ?, opportunity_id, stage, tcv_usd, close_date, std_probability
                FROM fact_opportunity WHERE stage IN {OPEN_STAGES_SQL}""",
            [snapshot_date],
        )
        self.conn.execute(
            "DELETE FROM fact_opportunity_snapshot "
            f"WHERE snapshot_date < ? - INTERVAL {RETENTION_YEARS} YEAR",
            [snapshot_date],
        )
        return self.conn.execute(
            "SELECT count(*) FROM fact_opportunity_snapshot WHERE snapshot_date = ?", [snapshot_date]
        ).fetchone()[0]
