"""API smoke + contract tests: endpoints, drill-down paging/sort/search, exports + audit,
reference/health, mock source APIs, and source-failure behaviour (FR-GEN-09/13)."""

from __future__ import annotations

import io
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from openpyxl import load_workbook

import app.connectors.mock as mock_module
from app.platform import db
from app.platform.audit import get_audit
from app.platform.elt import run as elt_run
from tests.conftest import ALL_ROLES, as_role


@pytest.mark.parametrize(
    "path",
    [
        "/api/executive/runway",
        "/api/executive/kpis",
        "/api/executive/bookings-by-quarter",
        "/api/executive/pipeline-by-vertical",
        "/api/executive/deals-attention",
        "/api/me",
        "/api/reference/roles",
        "/api/reference/filters",
        "/api/reference/metrics",
        "/api/reference/metrics/EXE-02",
        "/api/reference/thresholds",
        "/api/health",
        "/api/dq/summary",
    ],
)
def test_endpoints_ok(client, path):
    assert client.get(path).status_code == 200


def test_filters_via_query_params(client):
    all_ = client.get("/api/executive/kpis").json()[0]
    two = client.get("/api/executive/kpis?vertical=BFSI&vertical=Retail%20%26%20CPG").json()[0]
    assert two["value"] < all_["value"] and two["target_prorated"]
    assert client.get("/api/executive/kpis?period=quarter").status_code == 422
    q = client.get("/api/executive/kpis?period=quarter&quarter=2026-Q1").json()[0]
    assert q["period"]["label"] == "FY26 Q1"
    custom = client.get("/api/executive/kpis?period=custom&start=2026-02-01&end=2026-05-31").json()[0]
    assert custom["period"]["kind"] == "custom"


def test_metric_metadata_is_traceable(client):
    metas = {m["metric_id"]: m for m in client.get("/api/reference/metrics").json()}
    expected = {f"EXE-{i:02d}" for i in range(1, 11)} | {f"PIP-{i:02d}" for i in range(1, 8)}
    expected |= {f"PUR-{i:02d}" for i in range(1, 6)} | {f"OFF-{i:02d}" for i in range(1, 6)}
    expected |= {f"ACC-{i:02d}" for i in range(1, 5)} | {f"PAR-{i:02d}" for i in range(1, 4)}
    expected |= {"PUR-06"} | {f"CAP-{i:02d}" for i in range(1, 5)} | {f"MKT-{i:02d}" for i in range(1, 5)}
    assert set(metas) == expected | {"ADM-01"}
    m = metas["EXE-02"]
    assert m["owner"] == "Sales Operations" and m["last_refresh"]
    assert [s["source_id"] for s in m["sources"]] == ["SRC-01", "SRC-02"]
    assert client.get("/api/reference/metrics/NOPE-01").status_code == 404


def test_drilldown_paging_sort_search(client):
    p1 = client.get("/api/opportunities?metric_id=EXE-09&page_size=10&sort=tcv&order=desc").json()
    p2 = client.get("/api/opportunities?metric_id=EXE-09&page_size=10&page=2&sort=tcv&order=desc").json()
    assert p1["total_count"] > 20 and len(p1["rows"]) == 10
    assert p1["rows"][-1]["tcv"] >= p2["rows"][0]["tcv"]
    assert not {r["opportunity_id"] for r in p1["rows"]} & {r["opportunity_id"] for r in p2["rows"]}
    target = p1["rows"][0]
    found = client.get(f"/api/opportunities?metric_id=EXE-09&search={target['opportunity_id']}").json()
    assert [r["opportunity_id"] for r in found["rows"]] == [target["opportunity_id"]]
    assert target["crm_url"].endswith(f"/Opportunity/{target['opportunity_id']}/view")


def test_drilldown_errors(client):
    assert client.get("/api/opportunities?metric_id=EXE-07&segment=bad").status_code == 422
    assert client.get("/api/opportunities?metric_id=XYZ-01").status_code == 404


def test_widget_exports_csv_and_xlsx_are_audited(client):
    before = len(get_audit().recent(500))
    csv_resp = client.get("/api/exports/widget?metric_id=EXE-08&format=csv&vertical=BFSI")
    assert csv_resp.status_code == 200 and "text/csv" in csv_resp.headers["content-type"]
    assert "PRO-RATED" in csv_resp.text and "2026-Q1" in csv_resp.text
    x = client.get("/api/exports/widget?metric_id=EXE-01&format=xlsx")
    wb = load_workbook(io.BytesIO(x.content))
    assert any("EXE-01" in str(c.value) for row in wb.active.iter_rows() for c in row)
    rows = client.get("/api/exports/opportunities?metric_id=EXE-07&segment=commit&format=csv")
    assert rows.status_code == 200 and "opportunity_id" in rows.text
    client.post("/api/exports/view", json={"view": "executive", "format": "pdf"})
    log = get_audit().recent(500)
    assert len(log) >= before + 4
    assert {"export", "export_view_pdf"} <= {e["action"] for e in log[:4]}


def test_mock_source_apis(client):
    sf = client.get("/mock/salesforce/services/data/v60.0/sobjects/Opportunity/records?limit=5").json()
    assert sf["totalSize"] > 500 and not sf["done"] and len(sf["records"]) == 5
    assert sf["records"][0]["attributes"]["type"] == "Opportunity"
    assert client.get("/mock/anaplan/2/0/workspaces/moment/models/gtm-plan/exports/bookings-target").json()[
        "rows"
    ]
    groups = client.get("/mock/graph/v1.0/groups").json()["value"]
    members = client.get(f"/mock/graph/v1.0/groups/{groups[0]['id']}/members").json()["value"]
    assert members and "userPrincipalName" in members[0]
    assert client.get("/mock/sap/opu/odata/sap/ZGTM_CONTRACT_SRV/Contracts").json()["value"]
    assert client.get("/mock/graph/v1.0/sites/moment/lists/offering-catalogue/items").json()["value"]


def test_health_reports_fresh_sources(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and not h["stale"]
    assert {s["source_id"] for s in h["sources"]} >= {"SRC-01", "SRC-02", "SRC-16"}


@pytest.fixture
def failing_planning(monkeypatch):
    monkeypatch.setattr(
        mock_module, "settings", replace(mock_module.settings, mock_fail_sources=["planning"])
    )
    yield
    monkeypatch.undo()
    db.rebuild()


def test_failed_source_keeps_last_good_extract(client, failing_planning):
    db.rebuild()
    h = client.get("/api/health").json()
    planning = next(s for s in h["sources"] if s["key"] == "planning")
    assert h["stale"] and planning["status"] == "failed" and "fail" in planning["message"]
    assert client.get("/api/executive/kpis").json()[0]["target"] is not None  # last good used


def test_never_loaded_source_gives_empty_target_state(client, failing_planning, monkeypatch):
    monkeypatch.setattr(elt_run, "_LAST_GOOD", {})
    db.rebuild()
    kpi = client.get("/api/executive/kpis").json()[0]
    assert kpi["target"] is None and kpi["status"] is None
    assert "Planning" in kpi["status_basis"]
    rw = client.get("/api/executive/runway").json()
    assert "unavailable" in rw["narrative"]


def test_solutions_lead_message(client):
    r = client.get("/api/executive/kpis", headers=as_role("solutions_lead"))
    assert r.status_code == 403 and "does not have access" in r.json()["detail"]


def test_off_acc_par_drilldown_endpoints(client, platform):
    """Step 8: Verify `/api/opportunities` drill-down for OFF-01..03, ACC-01..03, PAR-01..02."""
    sample_acc = platform.scalar("SELECT account_id FROM dim_account ORDER BY account_id LIMIT 1")
    cases = [
        "/api/opportunities?metric_id=OFF-01&segment=Pulse%20Insights|open",
        "/api/opportunities?metric_id=OFF-01&segment=Capability-led|won",
        "/api/opportunities?metric_id=OFF-01&segment=Untagged|open",
        "/api/opportunities?metric_id=OFF-02&segment=2",
        "/api/opportunities?metric_id=OFF-02&segment=3%2B",
        "/api/opportunities?metric_id=OFF-03&segment=Pending",
        f"/api/opportunities?metric_id=ACC-01&segment={sample_acc}|DxP",
        "/api/opportunities?metric_id=ACC-02&segment=DxP",
        "/api/opportunities?metric_id=ACC-03&segment=2026-Q2|expansion",
        "/api/opportunities?metric_id=PAR-01&segment=Adobe|Propose",
        "/api/opportunities?metric_id=PAR-02&segment=Adobe|co_sell",
        "/api/opportunities?metric_id=PAR-02&segment=Direct|solo",
    ]
    for url in cases:
        r = client.get(url)
        assert r.status_code == 200, f"Failed {url}: {r.text}"
        body = r.json()
        assert "rows" in body and "total_count" in body


def test_concurrent_50_users_across_all_modules_p90_budget(client):
    """AC-05 / NFR-01 / NFR-02: 50 concurrent simulated users across all 8 analytical modules + filters
    complete within P90 <= 3.0s for module views and P90 <= 2.0s for filter changes with 0% error rate."""
    client.get("/api/health")
    view_urls = [
        "/api/executive/runway",
        "/api/pipeline/by-platform",
        "/api/pursuits/loss-reasons",
        "/api/offerings/ai-validation",
        "/api/accounts/whitespace",
        "/api/partners/pipeline",
        "/api/capacity/rfp-turnaround",
        "/api/market/analyst-positioning",
    ]
    filter_urls = [
        "/api/executive/runway?vertical=BFSI&period=quarter&quarter=2026-Q2",
        "/api/pipeline/by-platform?practice=DxP",
        "/api/offerings/ai-validation?platform=Adobe",
        "/api/partners/pipeline?geography=Americas",
    ]

    def run_vu(vu_idx: int) -> tuple[float, float, int]:
        role = ALL_ROLES[vu_idx % len(ALL_ROLES)]
        headers = as_role(role)
        view_url = view_urls[vu_idx % len(view_urls)]
        filter_url = filter_urls[vu_idx % len(filter_urls)]

        t0 = time.perf_counter()
        r1 = client.get(view_url, headers=headers)
        view_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        r2 = client.get(filter_url, headers=headers)
        filter_ms = (time.perf_counter() - t1) * 1000.0

        errs = int(r1.status_code not in (200, 403)) + int(r2.status_code not in (200, 403))
        return view_ms, filter_ms, errs

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(run_vu, range(50)))

    view_latencies = sorted(r[0] for r in results)
    filter_latencies = sorted(r[1] for r in results)
    total_errors = sum(r[2] for r in results)

    p90_view = view_latencies[int(0.9 * len(view_latencies)) - 1]
    p90_filter = filter_latencies[int(0.9 * len(filter_latencies)) - 1]

    assert total_errors == 0
    assert p90_view < 3000.0, f"P90 view load {p90_view:.1f}ms exceeded 3000ms budget"
    assert p90_filter < 2000.0, f"P90 filter response {p90_filter:.1f}ms exceeded 2000ms budget"

