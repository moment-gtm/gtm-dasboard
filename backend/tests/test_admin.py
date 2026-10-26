"""Administration API (FR-ADM-01..04, change control): gating, versioning, validation, audit."""

from __future__ import annotations

import pytest

from app.platform.admin_store import get_admin_store
from app.platform.db import rebuild
from tests.conftest import ALL_ROLES, as_role

ADMIN = as_role("gtm_lead")
OPS = as_role("sales_ops")


@pytest.fixture(autouse=True)
def clean_admin(client):
    get_admin_store().reset()
    rebuild()
    yield
    get_admin_store().reset()
    rebuild()


@pytest.mark.parametrize("role", ALL_ROLES)
def test_only_gtm_lead_and_sales_ops_can_use_admin(client, role):
    r = client.get("/api/admin/dq", headers=as_role(role))
    assert r.status_code == (200 if role in ("gtm_lead", "sales_ops") else 403)


def test_threshold_edit_is_versioned_and_changes_statuses(client):
    before = {t["metric_id"]: t for t in client.get("/api/reference/thresholds").json()}["PUR-05"]
    body = {"on_track": 0.6, "watch": 0.45, "reason": "Raised after FY26 review"}
    r = client.put("/api/admin/thresholds/PUR-05", json=body, headers=ADMIN)
    assert r.status_code == 200 and r.json()["version"] == 2
    after = {t["metric_id"]: t for t in client.get("/api/reference/thresholds").json()}["PUR-05"]
    assert (after["on_track"], after["watch"]) == (0.6, 0.45) and after["label"] != before["label"]
    hist = client.get("/api/admin/thresholds/PUR-05/history", headers=ADMIN).json()
    assert hist[0]["reason"] == body["reason"] and hist[0]["changed_by"]


def test_threshold_validation(client):
    bad = {"on_track": 0.3, "watch": 0.45, "reason": "wrong order"}
    assert client.put("/api/admin/thresholds/PUR-05", json=bad, headers=ADMIN).status_code == 422
    ok = {"on_track": 0.6, "watch": 0.45, "reason": "x" * 3}
    assert client.put("/api/admin/thresholds/NOPE-01", json=ok, headers=ADMIN).status_code == 404
    assert (
        client.put("/api/admin/thresholds/PUR-05", json={**ok, "reason": ""}, headers=ADMIN).status_code
        == 422
    )


def _grid(client, scale=1.0):
    t = client.get("/api/admin/targets", headers=ADMIN).json()
    fy = t["active"][0]["fiscal_year"]
    rows = [
        {"quarter": g["quarter"], "practice": g["practice"], "amount_usd": g["amount_usd"] * scale}
        for g in t["grid"]
        if g["fiscal_year"] == fy
    ]
    return fy, rows


def test_new_target_version_becomes_active_and_keeps_history(client):
    fy, rows = _grid(client, 1.1)
    r = client.post(
        "/api/admin/targets", json={"fiscal_year": fy, "note": "Plan uplift", "rows": rows}, headers=ADMIN
    )
    assert r.status_code == 201
    version = r.json()["version"]
    t = client.get("/api/admin/targets", headers=ADMIN).json()
    active = next(a for a in t["active"] if a["fiscal_year"] == fy)
    assert active["version"] == version
    assert {v["version"]: v["active"] for v in t["versions"] if v["fiscal_year"] == fy}[version]
    assert len([v for v in t["versions"] if v["fiscal_year"] == fy]) == 2
    assert client.get(f"/api/admin/targets/{version}", headers=ADMIN).json()["rows"]


def test_target_version_requires_full_grid(client):
    fy, rows = _grid(client)
    r = client.post(
        "/api/admin/targets", json={"fiscal_year": fy, "note": "partial", "rows": rows[:-1]}, headers=ADMIN
    )
    assert r.status_code == 422 and "all 4 quarters" in r.json()["detail"]


def test_reference_edit_flows_into_global_filters(client):
    current = client.get("/api/admin/reference/verticals", headers=ADMIN).json()["values"]
    body = {"values": [*current, "Space"], "reason": "New vertical"}
    assert client.put("/api/admin/reference/verticals", json=body, headers=ADMIN).status_code == 200
    opts = client.get("/api/reference/filters").json()["verticals"]
    assert "Space" in [o["value"] for o in opts]


def test_reference_rejects_invalid_and_in_use_removals(client):
    practices = client.get("/api/admin/reference/practices", headers=ADMIN).json()["values"]
    gone = {"values": practices[1:], "reason": "drop first"}
    r = client.put("/api/admin/reference/practices", json=gone, headers=ADMIN)
    assert r.status_code == 409 and practices[0] in r.json()["detail"]
    dup = {"values": [practices[0], practices[0]], "reason": "dup"}
    assert client.put("/api/admin/reference/practices", json=dup, headers=ADMIN).status_code == 422
    ro = {"values": [], "reason": "nope"}
    assert client.put("/api/admin/reference/offerings", json=ro, headers=ADMIN).status_code == 405
    stages = client.get("/api/admin/reference/stage_probability", headers=ADMIN).json()["values"]
    stages[1]["probability"] = 0.0
    r = client.put(
        "/api/admin/reference/stage_probability", json={"values": stages, "reason": "bad"}, headers=ADMIN
    )
    assert r.status_code == 422


def test_size_band_gap_is_rejected(client):
    bands = client.get("/api/admin/reference/size_bands", headers=ADMIN).json()["values"]
    bands[1]["min_usd"] += 1
    r = client.put("/api/admin/reference/size_bands", json={"values": bands, "reason": "gap"}, headers=ADMIN)
    assert r.status_code == 422 and "gap" in r.json()["detail"]


def test_dq_console_summary_findings_and_export(client):
    s = client.get("/api/admin/dq", headers=OPS).json()
    assert len(s["rules"]) == 9 and s["gate"]["weeks"] == 2
    rule = next(r for r in s["rules"] if r["rule_id"] == "DQ-06")
    page = client.get("/api/admin/dq/findings?rule_id=DQ-06&page_size=10", headers=OPS).json()
    assert page["total"] == rule["records"] and len(page["rows"]) == 10
    csv = client.get("/api/admin/dq/export?rule_id=DQ-04", headers=OPS)
    assert csv.headers["content-type"].startswith("text/csv") and csv.text.startswith("rule_id,")
    trail = client.get("/api/admin/audit", headers=ADMIN).json()
    assert any(a["action"] == "admin.dq.export" for a in trail)


def test_change_request_workflow(client):
    r = client.post(
        "/api/admin/change-requests",
        json={"metric_id": "PIP-01", "title": "Weighted pipeline", "description": "Use rep probability"},
        headers=OPS,
    )
    cid = r.json()["id"]
    base = f"/api/admin/change-requests/{cid}"
    note = {"note": "Low impact"}
    assert (
        client.post(
            f"{base}/decide", json={"decision": "approve", "note": "Approved"}, headers=ADMIN
        ).status_code
        == 409
    )
    assert client.post(f"{base}/assess", json=note, headers=OPS).json()["status"] == "logged"
    assert client.post(f"{base}/assess", json=note, headers=ADMIN).json()["status"] == "assessed"
    assert (
        client.post(
            f"{base}/decide", json={"decision": "approve", "note": "Approved"}, headers=OPS
        ).status_code
        == 403
    )
    d = client.post(f"{base}/decide", json={"decision": "approve", "note": "Approved"}, headers=ADMIN).json()
    assert d["status"] == "approved" and d["release_window"]
    assert client.post(f"{base}/release", headers=OPS).json()["status"] == "released"
    assert client.post(f"{base}/release", headers=OPS).status_code == 409
    bad = {"metric_id": "ZZZ-99", "title": "abc", "description": "abc"}
    assert client.post("/api/admin/change-requests", json=bad, headers=OPS).status_code == 422


def test_writes_are_audited_with_before_and_after(client):
    body = {"on_track": 0.6, "watch": 0.45, "reason": "audit check"}
    client.put("/api/admin/thresholds/PUR-05", json=body, headers=ADMIN)
    entry = next(
        a
        for a in client.get("/api/admin/audit", headers=ADMIN).json()
        if a["action"] == "admin.threshold.edit"
    )
    assert entry["detail"]["before"]["on_track"] == 0.5 and entry["detail"]["after"]["on_track"] == 0.6
