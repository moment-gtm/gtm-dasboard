"""PUR-01..06: win-rate math reconciles to direct queries on the fixed seed (AC-01), no-bid and
cancelled deals never count, drill-downs add up to their aggregate, the bid-discipline callout
rule, unmatched bid rows reach the DQ queue, and the Pursuits role matrix (AC-03)."""

from __future__ import annotations

import pytest

from app.data import reference_data as ref
from app.semantic import helpers as h
from app.semantic.metrics import exe, pur
from tests.conftest import ALL_ROLES, as_role

PURSUIT_ROLES = ["gtm_lead", "leadership", "finance", "practice_lead", "sales_ops", "solutions_lead"]
DENIED_ROLES = [r for r in ALL_ROLES if r not in PURSUIT_ROLES]
PUR_ENDPOINTS = [
    "/api/pursuits/win-rate",
    "/api/pursuits/loss-reasons",
    "/api/pursuits/source-mix",
    "/api/pursuits/bid-discipline",
    "/api/pursuits/orals-conversion",
]


def test_win_rate_reconciles_and_excludes_no_bid_and_cancelled(ctx, platform):
    c = ctx()
    m = pur.pur_01(c)
    assert len(m.breakdown) == pur.TREND_QUARTERS
    quarters = h.last_n_quarters(c.today, pur.TREND_QUARTERS)
    direct = {
        r["close_quarter"]: r
        for r in platform.query(
            f"""SELECT close_quarter,
                       count(*) FILTER (WHERE stage = 'Closed Won') AS won,
                       count(*) FILTER (WHERE stage = 'Closed Lost') AS lost
                FROM fact_opportunity
                WHERE close_quarter IN ({", ".join("?" * len(quarters))}) AND close_date <= ?
                GROUP BY 1""",
            [*quarters, c.today],
        )
    }
    for row in m.breakdown:
        d = direct.get(row["quarter"], {"won": 0, "lost": 0})
        assert (row["won"], row["lost"]) == (d["won"], d["lost"])
        assert row["decided"] == row["won"] + row["lost"]
    last4 = m.breakdown[-4:]
    assert m.value == pytest.approx(sum(r["won"] for r in last4) / sum(r["decided"] for r in last4))
    assert m.goal == 0.40


def test_loss_reasons_sum_to_lost_and_flag_one_top_reason(ctx):
    m = pur.pur_02(ctx())
    assert sum(r["count"] for r in m.breakdown) == m.meta["lost"]
    assert sum(r["share"] for r in m.breakdown) == pytest.approx(1.0)
    flagged = [r for r in m.breakdown if r["most_frequent"]]
    assert len(flagged) == 1 and flagged[0]["reason"] != pur.NOT_RECORDED
    assert flagged[0]["count"] == max(r["count"] for r in m.breakdown if r["reason"] != pur.NOT_RECORDED)
    assert {r["reason"] for r in m.breakdown} <= {*ref.LOSS_REASONS, pur.NOT_RECORDED}


def test_source_mix_covers_every_source_and_totals(ctx):
    c = ctx()
    m = pur.pur_03(c)
    assert [r["source"] for r in m.breakdown] == ref.LEAD_SOURCES
    assert sum(r["decided"] for r in m.breakdown) == m.meta["decided"]
    assert sum(r["share"] for r in m.breakdown) == pytest.approx(1.0)
    assert m.value == pytest.approx(
        sum(r["won"] for r in m.breakdown) / sum(r["decided"] for r in m.breakdown)
    )


def test_bid_callout_rule():
    assert pur.bid_callout(0.08, 0.30, 0.20, 0.35)  # both low -> fires
    assert pur.bid_callout(0.25, 0.30, 0.20, 0.35) is None  # healthy no-bid rate
    assert pur.bid_callout(0.08, 0.40, 0.20, 0.35) is None  # pursued RFPs win well
    assert pur.bid_callout(None, 0.30, 0.20, 0.35) is None


def test_bid_discipline_measures_and_seeded_callout(ctx, platform):
    c = ctx()
    m = pur.pur_04(c)
    by = {r["key"]: r for r in m.breakdown}
    start = pur._bid_window(c)
    total, no_bid = (
        platform.query(
            """SELECT count(*) AS t, count(*) FILTER (WHERE p.decision = 'no_bid') AS n
               FROM fact_pursuit p JOIN fact_opportunity o USING (opportunity_id)
               WHERE o.created_date >= ?""",
            [start],
        )[0][k]
        for k in ("t", "n")
    )
    assert m.meta["total"] == total and m.meta["no_bid"] == no_bid
    assert by["no_bid_rate"]["value"] == pytest.approx(no_bid / total)
    assert by["no_bid_rate"]["status"] and by["pursued_win_rate"]["status"]
    # The callout must agree with the rule applied to the thresholds (it is silent on healthy data).
    nb_t = platform.query("SELECT on_track FROM ref_threshold WHERE metric_id = 'PUR-04'")[0]["on_track"]
    win_t = platform.query("SELECT on_track FROM ref_threshold WHERE metric_id = 'PUR-04-WIN'")[0]["on_track"]
    expected = pur.bid_callout(by["no_bid_rate"]["value"], by["pursued_win_rate"]["value"], nb_t, win_t)
    assert m.narrative == expected == m.meta["callout"]


def test_orals_conversion_counts(ctx, platform):
    c = ctx()
    m = pur.pur_05(c)
    start = pur._bid_window(c)
    won = platform.scalar(
        """SELECT count(*) FROM fact_pursuit p JOIN fact_opportunity o USING (opportunity_id)
           WHERE p.orals_reached AND o.stage_group = 'won' AND o.created_date >= ?""",
        [start],
    )
    assert m.meta["won"] == won
    assert m.value == pytest.approx(won / (won + m.meta["lost"]))


@pytest.mark.parametrize(
    "metric_id,segments",
    [
        ("PUR-01", ["{q}", "{q}|won", "{q}|lost"]),
        ("PUR-02", [*ref.LOSS_REASONS, pur.NOT_RECORDED]),
        ("PUR-03", [*ref.LEAD_SOURCES, f"{ref.LEAD_SOURCES[0]}|won"]),
        ("PUR-04", ["", "no_bid", "pursued", "won", "lost", "late"]),
        ("PUR-05", ["won", "lost", "open"]),
    ],
)
def test_drilldown_counts_match_aggregates(ctx, client, metric_id, segments):
    c = ctx()
    q = h.last_n_quarters(c.today, pur.TREND_QUARTERS)[-2]
    for seg in segments:
        seg = seg.format(q=q)
        r = client.get("/api/opportunities", params={"metric_id": metric_id, "segment": seg, "page_size": 5})
        assert r.status_code == 200, (metric_id, seg, r.text)
        body = r.json()
        cond, args, _ = pur.drill_condition(c, metric_id, seg)
        where, wargs = c.where(cond, args=args, detail=True)
        assert body["total_count"] == c.platform.scalar(
            f"SELECT count(*) FROM mart_opportunity o WHERE {where}", wargs
        )


def test_drilldown_totals_equal_metric_numbers(ctx, client):
    c = ctx()
    loss = pur.pur_02(c)
    for row in loss.breakdown:
        r = client.get("/api/opportunities", params={"metric_id": "PUR-02", "segment": row["reason"]})
        assert r.json()["total_count"] == row["count"]
    sm = pur.pur_03(c)
    for row in sm.breakdown:
        r = client.get("/api/opportunities", params={"metric_id": "PUR-03", "segment": row["source"]})
        assert r.json()["total_count"] == row["decided"]


@pytest.mark.parametrize("metric_id,seg", [("PUR-01", "FY1900-Q1"), ("PUR-02", "Nope"), ("PUR-04", "x")])
def test_invalid_segments_rejected(client, metric_id, seg):
    r = client.get("/api/opportunities", params={"metric_id": metric_id, "segment": seg})
    assert r.status_code == 422


def test_unmatched_bid_rows_go_to_dq_queue(platform, dataset):
    orphans = [b for b in dataset.bid_pursuits if b["Pursuit_Id"].startswith("BID-9")]
    assert orphans
    found = platform.query("SELECT record_id FROM dq_finding WHERE rule_id = 'DQ-04'")
    assert {r["record_id"] for r in found} == {b["Pursuit_Id"] for b in orphans}
    assert platform.scalar("SELECT count(*) FROM fact_pursuit WHERE pursuit_id LIKE 'BID-9%'") == 0


def test_loss_reason_only_on_lost_deals(platform):
    assert (
        platform.scalar(
            "SELECT count(*) FROM fact_opportunity WHERE loss_reason IS NOT NULL AND stage_group <> 'lost'"
        )
        == 0
    )
    assert (
        platform.scalar(
            "SELECT count(*) FROM fact_opportunity WHERE stage_group = 'lost' AND loss_reason IS NULL"
        )
        > 0
    )


@pytest.mark.parametrize("role", ALL_ROLES)
@pytest.mark.parametrize("path", PUR_ENDPOINTS)
def test_pursuits_role_matrix(client, role, path):
    r = client.get(path, headers=as_role(role))
    assert r.status_code == (200 if role in PURSUIT_ROLES else 403), (role, path)


@pytest.mark.parametrize("role", DENIED_ROLES)
def test_denied_roles_cannot_drill_or_export_pursuits(client, role):
    assert client.get("/api/opportunities?metric_id=PUR-02", headers=as_role(role)).status_code == 403
    assert client.get("/api/exports/widget?metric_id=PUR-02", headers=as_role(role)).status_code == 403


def test_pursuits_export_for_allowed_role(client):
    r = client.get("/api/exports/widget?metric_id=PUR-03&format=csv", headers=as_role("gtm_lead"))
    assert r.status_code == 200 and "Client RFP" in r.text


def test_margin_drilldown_for_restricted_role(client):
    body = client.get("/api/pursuits/margin", headers=as_role("finance")).json()
    row = next(r for r in body["breakdown"] if r["deals"])
    page = client.get(
        f"/api/opportunities?metric_id=PUR-06&segment={row['quarter']}", headers=as_role("finance")
    ).json()
    assert page["total_count"] == row["deals"]


def test_unused_helpers_stay_importable():
    assert exe.InvalidSegment and pur.FUNCTIONS.keys() == {f"PUR-0{i}" for i in range(1, 6)}
