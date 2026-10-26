"""Administration store (FR-ADM-01..03, §10.2): versioned targets, threshold / reference-data edits
and the metric change-request log.

The platform is rebuilt from scratch on every ELT run, so admin edits live in their own DuckDB file
(like `audit_log`) and are overlaid onto the ref_* / planning tables by `elt/admin_overlay.py`.
Nothing is ever updated in place: every change appends a new version, so history is the audit trail.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

_DDL = [
    """CREATE TABLE IF NOT EXISTS target_version (version VARCHAR, fiscal_year INTEGER, seq INTEGER,
       note VARCHAR, created_by VARCHAR, created_at TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS target_row (version VARCHAR, quarter INTEGER, practice VARCHAR,
       amount_usd DOUBLE)""",
    """CREATE TABLE IF NOT EXISTS threshold_version (metric_id VARCHAR, version INTEGER, on_track DOUBLE,
       watch DOUBLE, reason VARCHAR, changed_by VARCHAR, changed_at TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS reference_version (set_name VARCHAR, version INTEGER, payload VARCHAR,
       reason VARCHAR, changed_by VARCHAR, changed_at TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS change_request (id INTEGER, metric_id VARCHAR, title VARCHAR,
       description VARCHAR, requested_by VARCHAR, status VARCHAR, assessments VARCHAR, decision_by VARCHAR,
       decision_note VARCHAR, release_window VARCHAR, created_at TIMESTAMP, updated_at TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS alert_rule (rule_id VARCHAR, name VARCHAR, description VARCHAR,
       metric_id VARCHAR, kind VARCHAR, operator VARCHAR, threshold DOUBLE, unit VARCHAR,
       severity VARCHAR, channels VARCHAR, enabled BOOLEAN, created_by VARCHAR, updated_at TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS alert_subscription (upn VARCHAR, target_id VARCHAR,
       email BOOLEAN, teams BOOLEAN, updated_at TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS digest_config (id INTEGER, enabled BOOLEAN, day_of_week VARCHAR,
       hour_utc INTEGER, channels VARCHAR, updated_by VARCHAR, updated_at TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS digest_run (run_id INTEGER, triggered_by VARCHAR,
       recipient_upn VARCHAR, recipient_role VARCHAR, channels VARCHAR, kpi_count INTEGER,
       stalled_deal_count INTEGER, over_capacity_count INTEGER, triggered_alert_count INTEGER,
       status VARCHAR, sent_at TIMESTAMP)""",
]
_TABLES = (
    "target_row",
    "target_version",
    "threshold_version",
    "reference_version",
    "change_request",
    "alert_rule",
    "alert_subscription",
    "digest_config",
    "digest_run",
)

DEFAULT_ALERT_RULES = [
    {
        "rule_id": "coverage_drop",
        "name": "Pipeline coverage below 2.5×",
        "description": (
            "Fires when qualified 2-quarter pipeline coverage (EXE-02) drops below 2.5× remaining target."
        ),
        "metric_id": "EXE-02",
        "kind": "coverage_drop",
        "operator": "lt",
        "threshold": 2.5,
        "unit": "x",
        "severity": "critical",
        "channels": ["email", "teams"],
        "enabled": True,
    },
    {
        "rule_id": "large_deal_slip",
        "name": "Large deal (≥ $5.0M) stalled or past close date",
        "description": (
            "Fires when any open opportunity ≥ $5.0M TCV in scope is past its close date "
            "or stalled in stage (> 60 days)."
        ),
        "metric_id": "EXE-10",
        "kind": "large_deal_slip",
        "operator": "gte",
        "threshold": 5_000_000.0,
        "unit": "usd",
        "severity": "critical",
        "channels": ["email", "teams"],
        "enabled": True,
    },
    {
        "rule_id": "unvalidated_ai_propose",
        "name": "Unvalidated AI-led deal in Propose or later",
        "description": (
            "Fires when any open AI-led opportunity is in Propose, Orals, or Negotiate "
            "without a completed technical validation (OFF-03)."
        ),
        "metric_id": "OFF-03",
        "kind": "unvalidated_ai_propose",
        "operator": "gt",
        "threshold": 0.0,
        "unit": "count",
        "severity": "warning",
        "channels": ["email", "teams"],
        "enabled": True,
    },
]


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AdminStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = duckdb.connect(str(path))
        for ddl in _DDL:
            self._conn.execute(ddl)
        self._seed_alerts()

    def _seed_alerts(self) -> None:
        with self._lock:
            now = _now()
            n_rules = self._conn.execute("SELECT count(*) FROM alert_rule").fetchone()[0]
            if n_rules == 0:
                for r in DEFAULT_ALERT_RULES:
                    self._conn.execute(
                        "INSERT INTO alert_rule VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        [
                            r["rule_id"],
                            r["name"],
                            r["description"],
                            r["metric_id"],
                            r["kind"],
                            r["operator"],
                            r["threshold"],
                            r["unit"],
                            r["severity"],
                            json.dumps(r["channels"]),
                            r["enabled"],
                            "system",
                            now,
                        ],
                    )
            n_cfg = self._conn.execute("SELECT count(*) FROM digest_config").fetchone()[0]
            if n_cfg == 0:
                self._conn.execute(
                    "INSERT INTO digest_config VALUES (1, TRUE, 'Monday', 7, ?, 'system', ?)",
                    [json.dumps(["email", "teams"]), now],
                )

    def _rows(self, sql: str, args: list[Any] | None = None) -> list[dict]:
        with self._lock:
            rel = self._conn.execute(sql, args or [])
            cols = [d[0] for d in rel.description]
            return [dict(zip(cols, r)) for r in rel.fetchall()]

    def _run(self, sql: str, args: list[Any] | None = None) -> None:
        with self._lock:
            self._conn.execute(sql, args or [])

    def reset(self) -> None:
        """Drop every admin edit (tests and demo reset); the seed reference data applies again."""
        with self._lock:
            for t in _TABLES:
                self._conn.execute(f"DELETE FROM {t}")
        self._seed_alerts()

    # --- targets (FR-ADM-01) -------------------------------------------------------------------
    def add_target_version(self, fiscal_year: int, rows: list[dict], note: str, user: str) -> str:
        with self._lock:
            seq = self._conn.execute(
                "SELECT count(*) FROM target_version WHERE fiscal_year = ?", [fiscal_year]
            ).fetchone()[0]
            # FYxx-Plan-v1 is the planning source's own version, so admin versions start at v2.
            version = f"FY{fiscal_year % 100}-Plan-v{seq + 2}-admin"
            self._conn.execute(
                "INSERT INTO target_version VALUES (?, ?, ?, ?, ?, ?)",
                [version, fiscal_year, seq + 1, note, user, _now()],
            )
            self._conn.executemany(
                "INSERT INTO target_row VALUES (?, ?, ?, ?)",
                [(version, r["quarter"], r["practice"], r["amount_usd"]) for r in rows],
            )
        return version

    def target_versions(self) -> list[dict]:
        return self._rows("SELECT * FROM target_version ORDER BY fiscal_year, seq")

    def target_rows(self, version: str) -> list[dict]:
        return self._rows(
            "SELECT quarter, practice, amount_usd FROM target_row WHERE version = ? ORDER BY 1, 2", [version]
        )

    # --- thresholds (FR-ADM-02) ----------------------------------------------------------------
    def add_threshold(self, metric_id: str, on_track: float, watch: float, reason: str, user: str) -> int:
        with self._lock:
            n = self._conn.execute(
                "SELECT count(*) FROM threshold_version WHERE metric_id = ?", [metric_id]
            ).fetchone()[0]
            version = n + 2  # the seed definition is version 1
            self._conn.execute(
                "INSERT INTO threshold_version VALUES (?, ?, ?, ?, ?, ?, ?)",
                [metric_id, version, on_track, watch, reason, user, _now()],
            )
        return version

    def latest_thresholds(self) -> dict[str, dict]:
        rows = self._rows("""SELECT * FROM threshold_version
               QUALIFY row_number() OVER (PARTITION BY metric_id ORDER BY version DESC) = 1""")
        return {r["metric_id"]: r for r in rows}

    def threshold_history(self, metric_id: str) -> list[dict]:
        return self._rows(
            "SELECT * FROM threshold_version WHERE metric_id = ? ORDER BY version DESC", [metric_id]
        )

    # --- reference data (FR-ADM-03) ------------------------------------------------------------
    def add_reference(self, set_name: str, payload: list, reason: str, user: str) -> int:
        with self._lock:
            n = self._conn.execute(
                "SELECT count(*) FROM reference_version WHERE set_name = ?", [set_name]
            ).fetchone()[0]
            self._conn.execute(
                "INSERT INTO reference_version VALUES (?, ?, ?, ?, ?, ?)",
                [set_name, n + 2, json.dumps(payload), reason, user, _now()],
            )
        return n + 2

    def latest_reference(self) -> dict[str, dict]:
        rows = self._rows("""SELECT * FROM reference_version
               QUALIFY row_number() OVER (PARTITION BY set_name ORDER BY version DESC) = 1""")
        return {r["set_name"]: {**r, "payload": json.loads(r["payload"])} for r in rows}

    def reference_history(self, set_name: str) -> list[dict]:
        return self._rows(
            """SELECT set_name, version, reason, changed_by, changed_at FROM reference_version
               WHERE set_name = ? ORDER BY version DESC""",
            [set_name],
        )

    # --- metric change control (§10.2) ---------------------------------------------------------
    def add_change_request(self, metric_id: str | None, title: str, description: str, user: str) -> dict:
        with self._lock:
            new_id = self._conn.execute("SELECT coalesce(max(id), 0) + 1 FROM change_request").fetchone()[0]
            now = _now()
            self._conn.execute(
                "INSERT INTO change_request VALUES (?, ?, ?, ?, ?, 'logged', '[]', NULL, NULL, NULL, ?, ?)",
                [new_id, metric_id, title, description, user, now, now],
            )
        return self.change_request(new_id)  # type: ignore[return-value]

    def change_requests(self) -> list[dict]:
        rows = self._rows("SELECT * FROM change_request ORDER BY id DESC")
        return [{**r, "assessments": json.loads(r["assessments"])} for r in rows]

    def change_request(self, request_id: int) -> dict | None:
        return next((r for r in self.change_requests() if r["id"] == request_id), None)

    def update_change_request(self, request_id: int, **fields: Any) -> dict:
        if "assessments" in fields:
            fields["assessments"] = json.dumps(fields["assessments"])
        sets = ", ".join(f"{k} = ?" for k in fields)
        self._run(
            f"UPDATE change_request SET {sets}, updated_at = ? WHERE id = ?",
            [*fields.values(), _now(), request_id],
        )
        return self.change_request(request_id)  # type: ignore[return-value]

    # --- alerts & weekly digest (FR-ALR-01..03) ------------------------------------------------
    def alert_rules(self) -> list[dict]:
        rows = self._rows("SELECT * FROM alert_rule ORDER BY rule_id")
        return [
            {
                **r,
                "channels": json.loads(r["channels"]),
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        ]

    def alert_rule(self, rule_id: str) -> dict | None:
        return next((r for r in self.alert_rules() if r["rule_id"] == rule_id), None)

    def upsert_alert_rule(self, rule: dict, user: str) -> dict:
        now = _now()
        with self._lock:
            self._conn.execute("DELETE FROM alert_rule WHERE rule_id = ?", [rule["rule_id"]])
            self._conn.execute(
                "INSERT INTO alert_rule VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    rule["rule_id"],
                    rule["name"],
                    rule["description"],
                    rule["metric_id"],
                    rule.get("kind", "metric_threshold"),
                    rule["operator"],
                    float(rule["threshold"]),
                    rule.get("unit", "count"),
                    rule.get("severity", "warning"),
                    json.dumps(rule.get("channels", ["email", "teams"])),
                    bool(rule.get("enabled", True)),
                    user,
                    now,
                ],
            )
        return self.alert_rule(rule["rule_id"])  # type: ignore[return-value]

    def subscriptions_for(self, upn: str) -> dict[str, dict]:
        rows = self._rows(
            "SELECT target_id, email, teams, updated_at FROM alert_subscription WHERE upn = ?",
            [upn],
        )
        return {
            r["target_id"]: {
                "target_id": r["target_id"],
                "email": bool(r["email"]),
                "teams": bool(r["teams"]),
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in rows
        }

    def set_subscriptions(self, upn: str, items: list[dict]) -> dict[str, dict]:
        now = _now()
        with self._lock:
            for item in items:
                target_id = item["target_id"]
                self._conn.execute(
                    "DELETE FROM alert_subscription WHERE upn = ? AND target_id = ?",
                    [upn, target_id],
                )
                self._conn.execute(
                    "INSERT INTO alert_subscription VALUES (?, ?, ?, ?, ?)",
                    [upn, target_id, bool(item["email"]), bool(item["teams"]), now],
                )
        return self.subscriptions_for(upn)

    def digest_config(self) -> dict:
        rows = self._rows("SELECT * FROM digest_config WHERE id = 1")
        if not rows:
            self._seed_alerts()
            rows = self._rows("SELECT * FROM digest_config WHERE id = 1")
        r = rows[0]
        return {
            "enabled": bool(r["enabled"]),
            "day_of_week": r["day_of_week"],
            "hour_utc": int(r["hour_utc"]),
            "channels": json.loads(r["channels"]),
            "updated_by": r["updated_by"],
            "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
        }

    def set_digest_config(
        self, enabled: bool, day_of_week: str, hour_utc: int, channels: list[str], user: str
    ) -> dict:
        now = _now()
        with self._lock:
            self._conn.execute("DELETE FROM digest_config WHERE id = 1")
            self._conn.execute(
                "INSERT INTO digest_config VALUES (1, ?, ?, ?, ?, ?, ?)",
                [bool(enabled), day_of_week, int(hour_utc), json.dumps(channels), user, now],
            )
        return self.digest_config()

    def record_digest_run(
        self,
        triggered_by: str,
        recipient_upn: str,
        recipient_role: str,
        channels: list[str],
        kpi_count: int,
        stalled_deal_count: int,
        over_capacity_count: int,
        triggered_alert_count: int,
        status: str = "delivered",
    ) -> dict:
        now = _now()
        with self._lock:
            run_id = self._conn.execute("SELECT coalesce(max(run_id), 0) + 1 FROM digest_run").fetchone()[0]
            self._conn.execute(
                "INSERT INTO digest_run VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    run_id,
                    triggered_by,
                    recipient_upn,
                    recipient_role,
                    json.dumps(channels),
                    int(kpi_count),
                    int(stalled_deal_count),
                    int(over_capacity_count),
                    int(triggered_alert_count),
                    status,
                    now,
                ],
            )
        return {
            "run_id": run_id,
            "triggered_by": triggered_by,
            "recipient_upn": recipient_upn,
            "recipient_role": recipient_role,
            "channels": channels,
            "kpi_count": kpi_count,
            "stalled_deal_count": stalled_deal_count,
            "over_capacity_count": over_capacity_count,
            "triggered_alert_count": triggered_alert_count,
            "status": status,
            "sent_at": now.isoformat(),
        }

    def digest_runs(self, recipient_upn: str | None = None, limit: int = 25) -> list[dict]:
        if recipient_upn:
            rows = self._rows(
                "SELECT * FROM digest_run WHERE recipient_upn = ? ORDER BY run_id DESC LIMIT ?",
                [recipient_upn, limit],
            )
        else:
            rows = self._rows("SELECT * FROM digest_run ORDER BY run_id DESC LIMIT ?", [limit])
        return [
            {
                **r,
                "channels": json.loads(r["channels"]),
                "sent_at": r["sent_at"].isoformat() if r["sent_at"] else None,
            }
            for r in rows
        ]


_store: AdminStore | None = None


def get_admin_store() -> AdminStore:
    global _store
    if _store is None:
        from app.config import settings

        _store = AdminStore(settings.admin_db_path)
    return _store
