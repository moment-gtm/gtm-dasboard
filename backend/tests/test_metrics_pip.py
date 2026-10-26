"""PIP-01..07: conversion math and ageing/size/movement counts reconcile to direct queries on the
fixed seed (AC-01), drill-downs add up to their aggregate, and the Pipeline role matrix (AC-03)."""

from __future__ import annotations

import pytest

from app.semantic.metrics import pip
from tests.conftest import ALL_ROLES, as_role

PIPELINE_ROLES = [
    "gtm_lead",
    "leadership",
    "finance",
    "practice_lead",
    "client_partner",
    "sales_ops",
    "solutions_lead",
]
PIP_ENDPOINTS = [
    "/api/pipeline/funnel",
    "/api/pipeline/ageing",
    "/api/pipeline/by-practice",
    "/api/pipeline/by-platform",
    "/api/pipeline/size-distribution",
    "/api/pipeline/register",
    "/api/pipeline/stage-movement",
]


def test_funnel_reconciles_to_stage_history(ctx, platform):
    m = pip.pip_01(ctx())
    start = m.meta["window_start"]
    direct = {
        r["stage"]: r["n"]
        for r in platform.query(
            """SELECT h.stage, count(DISTINCT h.opportunity_id) AS n FROM fact_stage_history h
               JOIN fact_opportunity o USING (opportunity_id) WHERE o.created_date >= ? GROUP BY 1""",
            [start],
        )
    }
    rows = {r["stage"]: r for r in m.breakdown}
    for i, stage in enumerate(pip.FUNNEL_STAGES[:-1]):
        nxt = pip.FUNNEL_STAGES[i + 1]
        assert rows[stage]["reached"] == direct[stage]
        assert rows[stage]["conversion"] == pytest.approx(direct[nxt] / direct[stage])
    assert sum(r["open_count"] for r in m.breakdown) == platform.scalar(
        "SELECT count(*) FROM fact_opportunity WHERE stage_group = 'open'"
    )


def test_ageing_buckets_partition_open_pipeline(ctx, platform):
    m = pip.pip_02(ctx())
    keys = [b["key"] for b in m.meta["buckets"]]
    assert keys == ["0-30", "31-60", "61-90", "90+"]
    assert sum(r[k]["count"] for r in m.breakdown for k in keys) == m.value
    stalled = platform.scalar(
        "SELECT count(*) FROM fact_opportunity WHERE stage_group = 'open' AND days_in_stage > 90"
    )
    assert sum(r["90+"]["count"] for r in m.breakdown) == stalled


def test_mix_and_size_totals_match_open_pipeline(ctx, platform):
    open_tcv = float(platform.scalar("SELECT sum(tcv_usd) FROM fact_opportunity WHERE stage_group = 'open'"))
    assert pip.pip_04(ctx()).value == pytest.approx(open_tcv)
    assert pip.pip_03(ctx()).value == pytest.approx(open_tcv, rel=0.005)
    size = pip.pip_05(ctx())
    assert sum(b["tcv"] for b in size.breakdown) == pytest.approx(open_tcv)
    assert size.value == pytest.approx(
        platform.scalar("SELECT count(*) FROM fact_opportunity WHERE stage_group = 'open'")
    )


def test_stage_movement_reflects_two_snapshots(ctx, platform):
    m = pip.pip_07(ctx())
    prev, cur = m.meta["previous_snapshot"], m.meta["latest_snapshot"]
    assert prev < cur
    by = {r["movement"]: r for r in m.breakdown}
    assert by["created"]["count"] == platform.scalar(
        """SELECT count(*) FROM fact_opportunity_snapshot c WHERE c.snapshot_date = ? AND NOT EXISTS
           (SELECT 1 FROM fact_opportunity_snapshot p WHERE p.snapshot_date = ?
            AND p.opportunity_id = c.opportunity_id)""",
        [cur, prev],
    )
    assert m.value == pytest.approx(m.meta["latest_tcv"] - m.meta["previous_tcv"])


@pytest.mark.parametrize(
    "metric_id, segments",
    [
        ("PIP-01", ["Identify", "Negotiate"]),
        ("PIP-02", ["Propose|61-90", "Identify|90+"]),
        ("PIP-05", ["1-2.5", "10+"]),
        ("PIP-07", ["created", "advanced", "slipped", "closed"]),
    ],
)
def test_drilldown_adds_up_to_aggregate(client, ctx, metric_id, segments):
    m = pip.FUNCTIONS[metric_id](ctx())
    for seg in segments:
        page = client.get(
            "/api/opportunities", params={"metric_id": metric_id, "segment": seg, "page_size": 1}
        ).json()
        if metric_id == "PIP-01":
            expected = next(r["open_count"] for r in m.breakdown if r["stage"] == seg)
        elif metric_id == "PIP-02":
            stage, key = seg.split("|")
            expected = next(r[key]["count"] for r in m.breakdown if r["stage"] == stage)
        elif metric_id == "PIP-05":
            expected = next(r["count"] for r in m.breakdown if r["band"] == seg)
        else:
            expected = next(r["count"] for r in m.breakdown if r["movement"] == seg)
        assert page["total_count"] == expected, seg


def test_register_flags_and_invalid_segment(client):
    page = client.get("/api/opportunities?metric_id=PIP-06&page_size=200&sort=days_in_stage").json()
    assert page["total_count"] > 0
    stalled = [r for r in page["rows"] if (r["days_in_stage"] or 0) > 90]
    assert stalled and all(r["flag"] == "Stalled" for r in stalled)
    assert client.get("/api/opportunities?metric_id=PIP-01&segment=Nope").status_code == 422
    assert client.get("/api/opportunities?metric_id=PIP-02&segment=Propose").status_code == 422


@pytest.mark.parametrize("role", ALL_ROLES)
@pytest.mark.parametrize("path", PIP_ENDPOINTS)
def test_pipeline_access_matrix(client, role, path):
    r = client.get(path, headers=as_role(role))
    assert r.status_code == (200 if role in PIPELINE_ROLES else 403), r.text


@pytest.mark.parametrize("role", ALL_ROLES)
def test_pipeline_drilldown_and_exports_respect_access(client, role):
    expected = 200 if role in PIPELINE_ROLES else 403
    assert client.get("/api/opportunities?metric_id=PIP-06", headers=as_role(role)).status_code == expected
    assert client.get(f"/api/exports/widget?metric_id=PIP-02&role={role}").status_code == expected
    assert client.get(f"/api/exports/widget?metric_id=PIP-06&role={role}").status_code == expected


def test_practice_lead_sees_other_practices_only_in_aggregate(client):
    page = client.get(
        "/api/opportunities?metric_id=PIP-06&page_size=200", headers=as_role("practice_lead")
    ).json()
    assert page["aggregated_other"]["count"] > 0
    assert {r["lead_practice"] for r in page["rows"]} == {"DxP"}
    full = client.get("/api/pipeline/register", headers=as_role("practice_lead")).json()
    assert full["value"] == page["total_count"] + page["aggregated_other"]["count"]
