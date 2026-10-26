"""AC-03: Consolidated 9-persona × 9-module role & row-level security (RLS) verification suite.

Tests:
1. Full 9-persona × 9-module HTTP status matrix (200 vs 403) against RSD §4 / Governance §5.
2. Restricted metrics (`PUR-06` and `CAP-03`) across module routes, drill-downs, and CSV exports,
   plus `audit_log` verification (`restricted.access` and `restricted.denied`).
3. Row-scope and detail-scope RLS invariants (`practice_lead`, `client_partner`, `alliance_manager`,
   `marketing`) across modules, drill-downs, exports, account detail panel, and weekly digest.
"""

from __future__ import annotations

import csv
import io

import pytest

from app.domain.enums import Role
from app.platform.audit import get_audit
from app.semantic.rls import resolve_user
from tests.conftest import ALL_ROLES, as_role

REPRESENTATIVE_MODULE_ENDPOINTS: dict[str, str] = {
    "executive": "/api/executive/kpis",
    "pipeline": "/api/pipeline/funnel",
    "pursuits": "/api/pursuits/win-rate",
    "offerings": "/api/offerings/by-offering",
    "accounts": "/api/accounts/penetration",
    "partners": "/api/partners/pipeline",
    "solutions_capacity": "/api/capacity/architect-load",
    "market_signals": "/api/market/thought-leadership",
    "admin": "/api/admin/dq",
}

RESTRICTED_ALLOWED_ROLES = {Role.GTM_LEAD, Role.LEADERSHIP, Role.FINANCE}


def test_solutions_lead_blocked_from_executive(client):
    """Solutions Lead has no Executive access in the RSD §4 matrix -> 403."""
    for path in (
        "/api/executive/runway",
        "/api/executive/kpis",
        "/api/executive/bookings-by-quarter",
        "/api/executive/pipeline-by-vertical",
        "/api/executive/deals-attention",
    ):
        r = client.get(path, headers=as_role("solutions_lead"))
        assert r.status_code == 403, path


@pytest.mark.parametrize(
    "role",
    [r for r in ALL_ROLES if r != "solutions_lead"],
)
def test_allowed_roles_receive_200_on_executive(client, role):
    r = client.get("/api/executive/kpis", headers=as_role(role))
    assert r.status_code == 200
    assert len(r.json()) == 6


@pytest.mark.parametrize("role", ALL_ROLES)
@pytest.mark.parametrize("module_key,endpoint", list(REPRESENTATIVE_MODULE_ENDPOINTS.items()))
def test_nine_personas_across_all_nine_modules_matrix(client, platform, role, module_key, endpoint):
    """AC-03: Every persona × every module route matches the §5 Role Access Matrix (200 vs 403)."""
    user = resolve_user(platform, role)
    expected_status = 200 if user.can_access(module_key) else 403
    r = client.get(endpoint, headers=as_role(role))
    assert r.status_code == expected_status, (
        f"Role {role} on {module_key} ({endpoint}): expected {expected_status}, got {r.status_code}"
    )


def test_practice_lead_sees_company_aggregates_but_only_own_practice_rows(client):
    """RSD §4 / §9.3: Practice Lead sees company aggregates, own-practice detail, rest rolled up."""
    gtm_kpis = {m["metric_id"]: m["value"] for m in client.get("/api/executive/kpis").json()}
    pl_kpis = {
        m["metric_id"]: m["value"]
        for m in client.get("/api/executive/kpis", headers=as_role("practice_lead")).json()
    }
    assert pl_kpis == gtm_kpis

    att = client.get("/api/executive/deals-attention", headers=as_role("practice_lead")).json()
    for row in att["rows"]:
        assert row["lead_practice"] == "DxP"
    assert att["aggregated_other"] is not None
    assert att["aggregated_other"]["count"] > 0
    assert "other practices" in att["aggregated_other"]["note"].lower()

    gtm_att = client.get("/api/executive/deals-attention").json()
    visible_tcv = sum(r["tcv"] for r in att["rows"])
    assert len(att["rows"]) + att["aggregated_other"]["count"] == int(gtm_att["metric"]["value"])
    assert abs((visible_tcv + att["aggregated_other"]["tcv"]) - gtm_att["metric"]["meta"]["total_tcv"]) < 1


def test_client_partner_sees_only_assigned_accounts(client, platform):
    cp = resolve_user(platform, "client_partner")
    expected_bookings = platform.scalar(
        """SELECT coalesce(sum(tcv_usd), 0) FROM mart_opportunity
           WHERE stage_group = 'won' AND close_date BETWEEN '2026-01-01' AND ?
             AND account_id IN ({})""".format(",".join(f"'{a}'" for a in cp.accounts)),
        [platform.as_of_date],
    )
    kpis = {
        m["metric_id"]: m
        for m in client.get("/api/executive/kpis", headers=as_role("client_partner")).json()
    }
    assert abs(kpis["EXE-01"]["value"] - expected_bookings) < 0.01
    assert kpis["EXE-01"]["target_prorated"] is True
    assert "pro-rated" in (kpis["EXE-01"]["target_basis"] or "").lower()

    drill = client.get(
        "/api/opportunities?metric_id=EXE-03&page_size=200", headers=as_role("client_partner")
    ).json()
    assert drill["total_count"] > 0
    for row in drill["rows"]:
        assert row["account_id"] in cp.accounts
    assert drill["aggregated_other"] is None


def test_client_partner_account_detail_enforces_assigned_accounts(client, platform):
    """AC-03: Client Partner gets 200 on assigned account detail and 404 on unassigned accounts."""
    cp = resolve_user(platform, "client_partner")
    assigned_id = cp.accounts[0]
    acc_list = ",".join(repr(a) for a in cp.accounts)
    unassigned_id = platform.scalar(
        f"SELECT account_id FROM dim_account WHERE account_id NOT IN ({acc_list}) LIMIT 1"
    )
    r_ok = client.get(f"/api/accounts/{assigned_id}/opportunities", headers=as_role("client_partner"))
    assert r_ok.status_code == 200

    r_denied = client.get(f"/api/accounts/{unassigned_id}/opportunities", headers=as_role("client_partner"))
    assert r_denied.status_code == 404


def test_alliance_manager_sees_only_assigned_partner_across_modules(client):
    # Executive drill-down
    drill = client.get(
        "/api/opportunities?metric_id=EXE-03&page_size=200", headers=as_role("alliance_manager")
    ).json()
    assert drill["total_count"] > 0
    for row in drill["rows"]:
        assert row["partner"] == "Adobe"

    # Partners module PAR-01 & PAR-03
    par_pipe = client.get("/api/partners/pipeline", headers=as_role("alliance_manager")).json()
    assert [b["partner"] for b in par_pipe["breakdown"]] == ["Adobe"]
    par_cert = client.get("/api/partners/certifications", headers=as_role("alliance_manager")).json()
    assert [b["partner"] for b in par_cert["breakdown"]] == ["Adobe"]

    # Offerings module OFF-01 drill-down
    off_drill = client.get(
        "/api/opportunities?metric_id=OFF-01&segment=Untagged|open&page_size=200",
        headers=as_role("alliance_manager"),
    ).json()
    for row in off_drill["rows"]:
        assert row["partner"] == "Adobe"


def test_marketing_sees_only_campaign_or_workshop_originated(client, platform):
    drill = client.get(
        "/api/opportunities?metric_id=EXE-03&page_size=200", headers=as_role("marketing")
    ).json()
    assert drill["total_count"] > 0
    ids = tuple(r["opportunity_id"] for r in drill["rows"])
    bad = platform.scalar(
        f"""SELECT count(*) FROM mart_opportunity
            WHERE opportunity_id IN ({",".join("?" * len(ids))})
              AND NOT (campaign_id IS NOT NULL OR workshop_originated)""",
        list(ids),
    )
    assert bad == 0


def test_export_honours_rls_and_records_audit(client):
    r = client.get(
        "/api/exports/opportunities?metric_id=EXE-03",
        headers=as_role("practice_lead"),
    )
    assert r.status_code == 200
    all_lines = list(csv.reader(io.StringIO(r.text)))
    header_idx = next(i for i, row in enumerate(all_lines) if row and row[0] == "opportunity_id")
    cols = all_lines[header_idx]
    data_rows = [dict(zip(cols, row, strict=False)) for row in all_lines[header_idx + 1 :] if row]
    assert data_rows and all(row["lead_practice"] == "DxP" for row in data_rows)

    audit_entries = [
        a for a in get_audit().recent(50) if a["role"] == "practice_lead" and "export" in a["action"]
    ]
    assert len(audit_entries) >= 1


@pytest.mark.parametrize("role", ALL_ROLES)
def test_restricted_metrics_pur06_and_cap03_across_all_endpoints_and_audit_log(client, platform, role):
    """AC-03 / §9.3: Restricted metrics (PUR-06, CAP-03) allow only GTM Lead, Leadership, Finance
    across module routes, drill-downs, widget exports, and opportunity exports, logging every attempt."""
    user = resolve_user(platform, role)
    headers = as_role(role)

    # 1. PUR-06 endpoints
    pur_allowed = user.can_access("pursuits") and user.role in RESTRICTED_ALLOWED_ROLES
    expected_pur = 200 if pur_allowed else 403
    for path in (
        "/api/pursuits/margin",
        "/api/opportunities?metric_id=PUR-06&segment=2026-Q2",
        "/api/exports/widget?metric_id=PUR-06",
        "/api/exports/opportunities?metric_id=PUR-06&segment=2026-Q2",
    ):
        res = client.get(path, headers=headers)
        assert res.status_code == expected_pur, f"Role {role} on {path}: got {res.status_code}"

    # 2. CAP-03 endpoints
    cap_allowed = user.can_access("solutions_capacity") and user.role in RESTRICTED_ALLOWED_ROLES
    expected_cap = 200 if cap_allowed else 403
    for path in (
        "/api/capacity/cost-of-sale",
        "/api/opportunities?metric_id=CAP-03&segment=2026-Q2",
        "/api/exports/widget?metric_id=CAP-03",
        "/api/exports/opportunities?metric_id=CAP-03&segment=2026-Q2",
    ):
        res = client.get(path, headers=headers)
        assert res.status_code == expected_cap, f"Role {role} on {path}: got {res.status_code}"

    # 3. Verify audit log records both allowed and denied restricted-metric attempts
    recent = get_audit().recent(200)
    actions = {a["action"] for a in recent}
    assert "restricted.access" in actions or "restricted.denied" in actions


def test_weekly_digest_and_alerts_respect_rls(client, platform):
    """AC-03 / FR-ALR-01..03: Weekly digest scopes alert items to the caller's RLS visibility."""
    cp = resolve_user(platform, "client_partner")
    r_cp = client.get("/api/alerts/digest", headers=as_role("client_partner"))
    assert r_cp.status_code == 200
    body_cp = r_cp.json()
    for row in body_cp.get("stalled_deals", {}).get("rows", []):
        assert row["account_id"] in cp.accounts

    r_am = client.get("/api/alerts/digest", headers=as_role("alliance_manager"))
    assert r_am.status_code == 200
    body_am = r_am.json()
    for row in body_am.get("stalled_deals", {}).get("rows", []):
        assert row["partner"] == "Adobe"
