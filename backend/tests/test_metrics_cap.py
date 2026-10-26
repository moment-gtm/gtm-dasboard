"""CAP-01..04: Solutions Capacity endpoints, invariants, drill-down, export and role matrix."""

from __future__ import annotations

import pytest

from tests.conftest import as_role

OPEN = ["architect-load", "rfp-turnaround", "quality-scores"]
NO_MODULE = ["client_partner", "alliance_manager", "marketing"]


def _cap(client, path, role="gtm_lead"):
    return client.get(f"/api/capacity/{path}", headers=as_role(role))


@pytest.mark.parametrize("path", [*OPEN, "cost-of-sale"])
def test_capacity_endpoints_return_metric(client, path):
    r = _cap(client, path)
    assert r.status_code == 200, r.text
    assert r.json()["metric_id"].startswith("CAP-")


@pytest.mark.parametrize("role", NO_MODULE)
def test_module_denied_without_access(client, role):
    for path in [*OPEN, "cost-of-sale"]:
        assert _cap(client, path, role).status_code == 403


def test_architect_load_bands_and_callout(client):
    body = _cap(client, "architect-load").json()
    rows = body["breakdown"]
    assert rows == sorted(rows, key=lambda r: (-r["open_pursuits"], r["architect"]))
    for r in rows:
        expected = (
            "off_track" if r["open_pursuits"] >= 5 else "watch" if r["open_pursuits"] == 4 else "on_track"
        )
        assert r["band"] == expected
    over = [r for r in rows if r["band"] == "off_track"]
    assert body["value"] == len(over) > 0
    assert all(r["architect"] in body["narrative"] for r in over)
    assert body["meta"]["healthy"] + body["meta"]["stretched"] + body["meta"]["over_capacity"] == len(rows)


def test_architect_load_drilldown_matches_count(client):
    top = _cap(client, "architect-load").json()["breakdown"][0]
    page = client.get(
        f"/api/opportunities?metric_id=CAP-01&segment={top['resource_id']}", headers=as_role("gtm_lead")
    ).json()
    assert page["total_count"] == top["open_pursuits"]
    bad = client.get("/api/opportunities?metric_id=CAP-01&segment=NOPE", headers=as_role("gtm_lead"))
    assert bad.status_code == 422


def test_rfp_turnaround_share_is_consistent(client):
    body = _cap(client, "rfp-turnaround").json()
    submitted = sum(r["submitted"] for r in body["breakdown"])
    on_time = sum(r["on_time"] for r in body["breakdown"])
    assert body["meta"]["submitted"] == submitted > 0
    assert body["value"] == pytest.approx(on_time / submitted)


def test_quality_score_won_above_lost(client):
    body = _cap(client, "quality-scores").json()
    assert body["meta"]["won_avg"] > body["meta"]["lost_avg"]
    assert [r["outcome"] for r in body["breakdown"]] == ["won", "lost"]


def test_cost_of_sale_is_cost_over_tcv(client):
    body = _cap(client, "cost-of-sale").json()
    assert body["value"] == pytest.approx(body["meta"]["cost"] / body["meta"]["tcv"])
    assert body["goal"] == 0.02


def test_widget_export_of_open_capacity_metric(client):
    r = client.get("/api/exports/widget?metric_id=CAP-01", headers=as_role("solutions_lead"))
    assert r.status_code == 200
    assert client.get("/api/exports/widget?metric_id=CAP-01", headers=as_role("marketing")).status_code == 403
