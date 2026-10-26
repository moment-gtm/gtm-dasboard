"""Market Signals module tests (FR-MKT-01..04, MKT-01..04): access matrix, metrics, drill-downs, exports."""

from __future__ import annotations

import pytest

from tests.conftest import ALL_ROLES, as_role

ALLOWED_MKT_ROLES = {"gtm_lead", "leadership", "finance", "practice_lead", "marketing", "sales_ops"}
MKT = as_role("marketing")
GTM = as_role("gtm_lead")


@pytest.mark.parametrize("role", ALL_ROLES)
def test_market_signals_access_matrix(client, role):
    r = client.get("/api/market/thought-leadership", headers=as_role(role))
    assert r.status_code == (200 if role in ALLOWED_MKT_ROLES else 403)


def test_mkt01_thought_leadership_and_filters(client):
    res = client.get("/api/market/thought-leadership", headers=MKT).json()
    assert res["metric_id"] == "MKT-01"
    assert res["unit"] == "count"
    assert res["value"] >= 1
    assert len(res["breakdown"]) == 4
    assert sum(b["povs"] for b in res["breakdown"]) > 0
    assert res["meta"]["total_downloads"] > 0
    assert res["meta"]["total_engaged_visits"] > 0
    assert len(res["meta"]["assets"]) >= 1

    # Filter by practice narrows POVs and engagement
    filtered = client.get(
        "/api/market/thought-leadership?practice=DxP",
        headers=MKT,
    ).json()
    assert filtered["value"] <= res["value"]
    assert all(a["practice"] == "DxP" for a in filtered["meta"]["assets"])


def test_mkt02_workshop_funnel_and_drill_down(client):
    res = client.get("/api/market/workshop-funnel", headers=MKT).json()
    assert res["metric_id"] == "MKT-02"
    assert res["unit"] == "pct"
    assert res["goal"] == pytest.approx(0.50)
    assert res["status"] in ("on_track", "watch", "off_track")
    stages = {b["key"]: b for b in res["breakdown"]}
    assert set(stages) == {"workshops", "created", "qualified", "won"}
    assert (
        stages["workshops"]["count"]
        >= stages["created"]["count"]
        >= stages["qualified"]["count"]
        >= stages["won"]["count"]
    )
    expected_rate = stages["created"]["count"] / stages["workshops"]["count"]
    assert res["value"] == pytest.approx(expected_rate)

    # Drill-down reconciles to funnel counts
    for seg in ("created", "qualified", "won"):
        dd = client.get(f"/api/opportunities?metric_id=MKT-02&segment={seg}", headers=GTM).json()
        assert dd["total_count"] == stages[seg]["count"]
        assert dd["total_tcv"] == pytest.approx(stages[seg]["tcv"])


def test_mkt03_campaign_sourced_pipeline_and_drill_down(client):
    res = client.get("/api/market/campaign-sourced", headers=MKT).json()
    alias = client.get("/api/market/campaign-pipeline", headers=MKT).json()
    assert res["metric_id"] == "MKT-03"
    assert alias["value"] == pytest.approx(res["value"])
    assert res["value"] > 0
    assert len(res["breakdown"]) == 4
    by_camp = res["meta"]["by_campaign"]
    assert len(by_camp) >= 1
    assert sum(c["tcv"] for c in by_camp) == pytest.approx(res["value"])

    # Drill-down by campaign ID reconciles with campaign breakdown row
    top_camp = by_camp[0]
    dd_camp = client.get(
        f"/api/opportunities?metric_id=MKT-03&segment={top_camp['campaign_id']}",
        headers=GTM,
    ).json()
    assert dd_camp["total_count"] == top_camp["deals"]
    assert dd_camp["total_tcv"] == pytest.approx(top_camp["tcv"])

    # Drill-down by quarter reconciles with quarter breakdown row
    q_with_deals = next(b for b in res["breakdown"] if b["deals"] > 0)
    dd_q = client.get(
        f"/api/opportunities?metric_id=MKT-03&segment={q_with_deals['quarter']}",
        headers=GTM,
    ).json()
    assert dd_q["total_count"] == q_with_deals["deals"]
    assert dd_q["total_tcv"] == pytest.approx(q_with_deals["tcv"])


def test_mkt04_analyst_positioning_and_direction_indicators(client):
    res = client.get("/api/market/analyst-positioning", headers=MKT).json()
    assert res["metric_id"] == "MKT-04"
    assert len(res["breakdown"]) >= 6
    firms = {r["firm"] for r in res["breakdown"]}
    assert {"Gartner", "Forrester", "IDC", "Everest Group"} <= firms
    for r in res["breakdown"]:
        assert r["direction"] in ("up", "flat", "down")
        assert r["direction_icon"] in ("↑", "→", "↓")
        assert r["direction_label"] in ("Improved", "Unchanged", "Declined")
        assert r["current_placement"] and r["prior_placement"]


@pytest.mark.parametrize("mid", ["MKT-01", "MKT-02", "MKT-03", "MKT-04"])
def test_market_signals_widget_csv_exports(client, mid):
    r = client.get(f"/api/exports/widget?metric_id={mid}", headers=MKT)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert len(r.text.splitlines()) >= 2
