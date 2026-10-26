"""Alerts & weekly digest engine tests (FR-ALR-01..03): rules, RLS scoping, subscriptions, digest."""

from __future__ import annotations

import pytest

from app.platform.admin_store import get_admin_store
from tests.conftest import ALL_ROLES, as_role

ADMIN = as_role("gtm_lead")
OPS = as_role("sales_ops")
CP = as_role("client_partner")
PL = as_role("practice_lead")
MKT = as_role("marketing")


@pytest.fixture(autouse=True)
def reset_alerts(client):
    get_admin_store().reset()
    yield
    get_admin_store().reset()


def test_default_alert_rules_evaluate_and_respect_rls(client):
    gtm_res = client.get("/api/alerts/rules", headers=ADMIN).json()
    assert gtm_res["can_manage"] is True
    rules = {r["rule_id"]: r for r in gtm_res["rules"]}
    assert {"coverage_drop", "large_deal_slip", "unvalidated_ai_propose"} <= set(rules)

    # Client partner only sees deals belonging to sarah.chen@moment.example
    cp_res = client.get("/api/alerts/rules", headers=CP).json()
    assert cp_res["can_manage"] is False
    cp_rules = {r["rule_id"]: r for r in cp_res["rules"]}
    assert cp_rules["large_deal_slip"]["observed_value"] <= rules["large_deal_slip"]["observed_value"]

    # Practice lead only sees detail rows in DxP practice
    pl_res = client.get("/api/alerts/rules", headers=PL).json()
    pl_rules = {r["rule_id"]: r for r in pl_res["rules"]}
    for deal in pl_rules["large_deal_slip"]["matching_deals"]:
        assert deal["lead_practice"] == "DxP"
    for deal in pl_rules["unvalidated_ai_propose"]["matching_deals"]:
        assert deal["lead_practice"] == "DxP"


def test_admin_can_create_and_update_alert_rules_and_restricted_metrics_are_gated(client):
    # Non-admin cannot create rules
    forbidden = client.post(
        "/api/alerts/rules",
        json={
            "name": "Win rate below 40%",
            "description": "Alert when win rate drops below 40%",
            "metric_id": "EXE-03",
            "operator": "lt",
            "threshold": 0.40,
            "unit": "pct",
            "severity": "warning",
            "channels": ["email"],
        },
        headers=MKT,
    )
    assert forbidden.status_code == 403

    # Admin creates a custom rule on restricted metric CAP-03
    created = client.post(
        "/api/alerts/rules",
        json={
            "rule_id": "cos_spike",
            "name": "Cost of sale above 4% of won TCV",
            "description": "Alert Finance and Leadership if cost of sale exceeds 4%",
            "metric_id": "CAP-03",
            "operator": "gt",
            "threshold": 0.01,
            "unit": "pct",
            "severity": "critical",
            "channels": ["email", "teams"],
        },
        headers=ADMIN,
    )
    assert created.status_code == 201
    assert created.json()["rule_id"] == "cos_spike"

    # Restricted metric rule is visible to GTM Lead / Leadership / Finance,
    # and hidden from Marketing / Practice Lead
    for role in ("gtm_lead", "leadership", "finance"):
        r_ids = {r["rule_id"] for r in client.get("/api/alerts/rules", headers=as_role(role)).json()["rules"]}
        assert "cos_spike" in r_ids
    for role in ("practice_lead", "client_partner", "marketing", "sales_ops", "solutions_lead"):
        r_ids = {r["rule_id"] for r in client.get("/api/alerts/rules", headers=as_role(role)).json()["rules"]}
        assert "cos_spike" not in r_ids


def test_user_subscriptions_opt_in_out_per_channel(client):
    sub_before = client.get("/api/alerts/subscriptions", headers=MKT).json()
    assert sub_before["role"] == "marketing"
    targets = {s["target_id"]: s for s in sub_before["subscriptions"]}
    assert "weekly_digest" in targets and "coverage_drop" in targets
    assert targets["weekly_digest"]["email"] is True

    # Marketing user opts out of email for weekly_digest and teams for coverage_drop
    updated = client.put(
        "/api/alerts/subscriptions",
        json={
            "subscriptions": [
                {"target_id": "weekly_digest", "email": False, "teams": True},
                {"target_id": "coverage_drop", "email": True, "teams": False},
            ]
        },
        headers=MKT,
    )
    assert updated.status_code == 200
    after_targets = {s["target_id"]: s for s in updated.json()["subscriptions"]}
    assert after_targets["weekly_digest"] == {
        **after_targets["weekly_digest"],
        "email": False,
        "teams": True,
    }
    assert after_targets["coverage_drop"]["teams"] is False

    # GTM Lead's subscriptions remain unaffected
    gtm_subs = {
        s["target_id"]: s
        for s in client.get("/api/alerts/subscriptions", headers=ADMIN).json()["subscriptions"]
    }
    assert gtm_subs["weekly_digest"]["email"] is True


@pytest.mark.parametrize("role", ALL_ROLES)
def test_weekly_digest_preview_is_rls_scoped_for_every_role(client, role):
    r = client.get("/api/alerts/digest", headers=as_role(role))
    assert r.status_code == 200
    d = r.json()
    assert d["recipient"]["role"] == role
    assert len(d["kpis"]) == 6
    assert d["email_preview"]["to"] == d["recipient"]["upn"]
    assert d["teams_preview"]["title"].startswith("[Moment GTM Digest]")
    assert len(d["dashboard_links"]) >= 1
    if role == "practice_lead":
        for deal in d["stalled_deals"]["deals"]:
            assert deal["lead_practice"] == "DxP"


def test_weekly_digest_preview_matches_frontend_contract(client):
    """Keys the DigestConfig preview renders (frontend/src/api/admin.ts DigestResponse)."""
    d = client.get("/api/alerts/digest", headers=ADMIN).json()
    assert d["recipient"]["display_name"] == d["recipient"]["name"]
    assert d["recipient"]["role_label"]
    assert d["stalled_deals"]["metric_id"] == "EXE-10"
    assert d["stalled_deals"]["formatted_tcv"].startswith("$")
    assert d["stalled_deals"]["deep_link"] == "/executive"
    cap = d["over_capacity_architects"]
    assert cap["metric_id"] == "CAP-01"
    assert cap["deep_link"] == "/solutions-capacity"
    assert isinstance(cap["healthy_count"], int) and cap["healthy_count"] >= 0
    assert d["email_preview"]["body_markdown"].startswith("# Moment GTM Weekly Digest")
    assert d["teams_preview"]["channel"] == "#moment-gtm-leadership"
    assert d["teams_preview"]["summary"]
    assert all(link["path"].startswith("/") for link in d["dashboard_links"])


def test_digest_schedule_and_dispatch_logged_in_history_and_audit(client):
    # Admin updates schedule
    sched = client.put(
        "/api/alerts/digest/schedule",
        json={"enabled": True, "day_of_week": "Tuesday", "hour_utc": 8, "channels": ["email", "teams"]},
        headers=OPS,
    )
    assert sched.status_code == 200
    assert sched.json()["day_of_week"] == "Tuesday" and sched.json()["hour_utc"] == 8

    # Dispatch digest to all subscribed personas
    sent = client.post(
        "/api/alerts/digest",
        json={"scope": "all_subscribed"},
        headers=ADMIN,
    )
    assert sent.status_code == 200
    body = sent.json()
    assert body["dispatched"] == len(ALL_ROLES)
    assert len(body["runs"]) == len(ALL_ROLES)
    assert len(body["digest"]["history"]) >= len(ALL_ROLES)

    # Audit trail records the digest dispatch
    audit = client.get("/api/admin/audit", headers=ADMIN).json()
    assert any(a["action"] == "admin.digest.send" for a in audit)
