"""DQ engine: rule registry, the nine rules, and the completeness gate (FR-ADM-04, AC-05).

The seed has no DQ-05 violations, so that rule is exercised on a private platform with injected
bad records rather than by distorting the seed.
"""

from __future__ import annotations

import pytest

from app.platform.elt.run import build_platform
from app.semantic import dq
from tests.conftest import as_role


def test_registry_has_nine_rules_all_active():
    assert [r.rule_id for r in dq.RULES] == [f"DQ-0{i}" for i in range(1, 10)]
    assert all(r.active for r in dq.RULES)


def test_findings_cover_active_rules_with_owner_and_detail(platform):
    rows = platform.query("SELECT rule_id, count(*) n FROM dq_finding GROUP BY 1")
    by_rule = {r["rule_id"]: r["n"] for r in rows}
    assert {"DQ-01", "DQ-02", "DQ-04", "DQ-06", "DQ-07", "DQ-08", "DQ-09"} <= set(by_rule)
    assert by_rule["DQ-09"] == 3  # seeded released build items without Asset ID / type
    assert platform.scalar("SELECT count(*) FROM dq_finding WHERE detail IS NULL OR severity IS NULL") == 0


def test_legacy_summary_shape_is_unchanged(client):
    rows = client.get("/api/dq/summary").json()
    assert rows and set(rows[0]) >= {"rule_id", "description", "handling", "records"}


@pytest.fixture(scope="module")
def injected():
    p = build_platform()
    lost = p.scalar("SELECT opportunity_id FROM fact_opportunity WHERE stage_group = 'lost' LIMIT 1")
    p.conn.execute("UPDATE fact_opportunity SET loss_reason = NULL WHERE opportunity_id = ?", [lost])
    acct = p.query("SELECT account_id, name, client_partner_upn FROM dim_account LIMIT 1")[0]
    p.conn.execute(
        "INSERT INTO dim_account VALUES ('ACC-DUP', ?, NULL, 'Unmapped', NULL, false, ?)",
        [acct["name"], acct["client_partner_upn"]],
    )
    p.conn.execute("UPDATE raw_crm_opportunity SET account_id = 'ACC-GONE' WHERE opportunity_id = ?", [lost])
    return p, lost


def _run(p, rule_id: str) -> list[dict]:
    return [row for c in dq.BY_ID[rule_id].checks for row in p.query(c.sql)]


def test_dq03_flags_lost_deal_without_reason(injected):
    p, lost = injected
    assert lost in [r["record_id"] for r in _run(p, "DQ-03")]


def test_dq05_flags_duplicate_and_orphan_accounts(injected):
    p, lost = injected
    details = [r["detail"] for r in _run(p, "DQ-05")]
    assert sum(d.startswith("Duplicate account name") for d in details) == 2
    assert any("ACC-GONE" in d for d in details)


def test_completeness_series_and_gate(platform):
    rows = platform.query("SELECT * FROM completeness_metric ORDER BY week_start")
    assert len(rows) == dq.HISTORY_WEEKS
    assert all(0 <= r["complete"] <= r["qualified"] for r in rows)


def test_adm01_metric_and_gate_from_api(client):
    m = client.get("/api/admin/dq/completeness", headers=as_role("sales_ops")).json()
    assert m["metric_id"] == "ADM-01" and m["unit"] == "pct"
    assert len(m["meta"]["series"]) == dq.HISTORY_WEEKS
    assert m["meta"]["gate"]["weeks"] == 2 and isinstance(m["meta"]["gate"]["met"], bool)
