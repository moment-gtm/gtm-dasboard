"""EXE-01..10 unit tests: calendar/pace helpers on hand-computed values, status banding from
ref_threshold, narrative wording, and drill-downs adding up to the metric they came from."""

from __future__ import annotations

from datetime import date

import pytest

from app.semantic import helpers as h
from app.semantic.metrics import exe
from app.semantic.status import band


# --- helpers (hand-computed) ------------------------------------------------------------------
def test_quarter_calendar():
    assert h.quarter_key(date(2026, 8, 14)) == "2026-Q3"
    assert h.quarter_bounds("2026-Q3") == (date(2026, 7, 1), date(2026, 9, 30))
    assert h.next_quarter("2026-Q4") == "2027-Q1"
    assert h.prev_quarter("2026-Q1") == "2025-Q4"
    assert h.quarter_label("2026-Q3") == "FY26 Q3"
    assert h.last_n_quarters(date(2026, 8, 14), 4) == ["2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3"]


def test_plan_pace_counts_completed_quarters_plus_elapsed_share():
    targets = {"2026-Q1": 100.0, "2026-Q2": 100.0, "2026-Q3": 92.0, "2026-Q4": 100.0}
    # 14 Aug = 45 of 92 days of Q3 elapsed (today counted) -> 100 + 100 + 92 * 45/92 = 245
    assert h.plan_pace(targets, date(2026, 1, 1), date(2026, 12, 31), date(2026, 8, 14)) == pytest.approx(
        245.0
    )
    assert h.period_target(targets, date(2026, 1, 1), date(2026, 12, 31)) == pytest.approx(392.0)
    assert h.elapsed_share("2026-Q3", date(2026, 8, 14)) == pytest.approx(45 / 92)


def test_money_format_is_musd_one_decimal():
    assert h.fmt_musd(1_234_567) == "$1.2M"
    assert h.fmt_musd(-23_960_000) == "-$24.0M"
    assert h.fmt_musd(None) == "n/a"


# --- status bands (Appendix B via ref_threshold) ----------------------------------------------
@pytest.mark.parametrize(
    "metric_id, value, expected",
    [
        ("EXE-01", 0.97, "on_track"),
        ("EXE-01", 0.9, "watch"),
        ("EXE-01", 0.84, "off_track"),
        ("EXE-02", 3.0, "on_track"),
        ("EXE-02", 2.5, "watch"),
        ("EXE-02", 2.49, "off_track"),
        ("EXE-03", 0.40, "on_track"),
        ("EXE-03", 0.32, "watch"),
        ("EXE-03", 0.31, "off_track"),
        ("EXE-04", 1.0, "on_track"),
        ("EXE-04", 0.85, "watch"),
        ("EXE-04", 0.8, "off_track"),
        ("EXE-05", 0.6, "on_track"),
        ("EXE-05", 0.55, "watch"),
        ("EXE-05", 0.49, "off_track"),
        ("EXE-06", 120, "on_track"),
        ("EXE-06", 150, "watch"),
        ("EXE-06", 151, "off_track"),
    ],
)
def test_status_bands(platform, metric_id, value, expected):
    assert band(platform, metric_id, value).value == expected


def test_runway_narrative_ahead_and_behind():
    behind = exe.runway_narrative(100e6, 120e6, 30e6, 225e6)
    assert behind == (
        "Bookings of $100.0M are $20.0M behind plan pace of $120.0M; after "
        "weighted commit of $30.0M, $95.0M remains to the full-year target of $225.0M."
    )
    assert "ahead of plan pace" in exe.runway_narrative(130e6, 120e6, 30e6, 225e6)
    assert "would cover the full-year target" in exe.runway_narrative(200e6, 120e6, 30e6, 225e6)


# --- metric invariants ------------------------------------------------------------------------
def test_kpis_have_value_goal_status_and_four_quarter_sparkline(ctx):
    c = ctx()
    for fn in exe.KPI_FUNCTIONS:
        m = fn(c)
        assert m.value is not None and m.goal is not None, m.metric_id
        assert m.status in ("on_track", "watch", "off_track"), m.metric_id
        assert len(m.sparkline) == 4 and m.sparkline[-1].partial, m.metric_id


def test_exe01_target_is_full_period_and_pace_is_prorated(ctx):
    fytd = exe.exe_01(ctx())
    assert fytd.target == pytest.approx(225e6)  # whole FY target, not pace
    assert fytd.goal < fytd.target  # plan pace pro-rated to today
    assert fytd.meta["pct_of_target"] == pytest.approx(fytd.value / 225e6)
    qtd = exe.exe_01(ctx(period="qtd"))
    assert qtd.target == pytest.approx(225e6 * 0.26) and qtd.goal < qtd.target


def test_runway_components_and_pace(ctx):
    m = exe.exe_07(ctx())
    assert m.meta["commit"] > 0 and m.meta["best_case"] > 0
    assert m.meta["plan_pace"] < m.meta["fy_target"]
    assert m.narrative and ("ahead of" in m.narrative or "behind" in m.narrative)


def test_bookings_by_quarter_marks_current_and_future(ctx):
    rows = exe.exe_08(ctx()).breakdown
    assert [r["quarter"] for r in rows] == ["2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"]
    assert rows[2]["is_current"] and rows[2]["label"].endswith("QTD")
    assert rows[3]["is_future"] and rows[3]["bookings"] == 0 and rows[3]["met"] is None


def test_pipeline_by_vertical_sums_to_open_pipeline(ctx, platform):
    m = exe.exe_09(ctx())
    open_tcv = platform.scalar("SELECT sum(tcv_usd) FROM mart_opportunity WHERE stage_group='open'")
    assert m.value == pytest.approx(open_tcv)
    assert len(m.breakdown) == 5


def test_deals_needing_attention_flags(ctx):
    metric, rows, _ = exe.exe_10(ctx())
    assert rows and metric.value == len(rows)
    for r in rows:
        assert r.tcv >= 2_000_000
        if r.flag == "Stalled":
            assert r.days_in_stage > 90
        elif r.flag == "Ageing":
            assert 60 < r.days_in_stage <= 90
        else:
            assert r.flag == "Past close date" and date.fromisoformat(r.close_date) < date(2026, 8, 14)


def test_deals_needing_attention_by_vertical_matches_headline(ctx):
    metric, _, _ = exe.exe_10(ctx())
    bv = metric.meta["by_vertical"]
    assert sum(v["count"] for v in bv) == metric.value
    for f in exe.ATTENTION_FLAGS:
        cond, args, _t = exe.drill_condition(ctx(), "EXE-10", f)
        assert cond and args


def test_deals_needing_attention_flag_drill_partitions_headline(ctx):
    c = ctx()
    metric, _, _ = exe.exe_10(c)
    total = 0
    for f in exe.ATTENTION_FLAGS:
        cond, args, _t = exe.drill_condition(c, "EXE-10", f)
        where, w_args = c.where(cond, args=args)
        total += c.platform.scalar(f"SELECT count(*) FROM mart_opportunity o WHERE {where}", w_args)
    assert total == metric.value


@pytest.mark.parametrize(
    "metric_id, segment, value_of",
    [
        ("EXE-01", None, lambda c: exe.exe_01(c).value),
        ("EXE-02", None, lambda c: exe.exe_02(c).meta["qualified_pipeline"]),
        ("EXE-04", None, lambda c: exe.exe_04(c).value),
        ("EXE-07", "booked", lambda c: exe.exe_07(c).meta["booked"]),
        ("EXE-08", "2026-Q2", lambda c: exe.exe_08(c).breakdown[1]["bookings"]),
        ("EXE-09", "BFSI|qualified", lambda c: exe.exe_09(c).breakdown[0]["qualified"]),
        ("EXE-05", "Untagged", lambda c: exe.exe_05(c).breakdown[2]["tcv"]),
    ],
)
def test_drilldown_adds_up_to_the_aggregate(ctx, metric_id, segment, value_of):
    c = ctx()
    cond, args, _ = exe.drill_condition(c, metric_id, segment)
    rows = exe.select_rows(c, cond, args)
    assert sum(r.tcv for r in rows) == pytest.approx(value_of(c))


def test_commit_drilldown_weighted_matches_runway(ctx):
    c = ctx()
    cond, args, _ = exe.drill_condition(c, "EXE-07", "commit")
    assert sum(r.weighted_tcv for r in exe.select_rows(c, cond, args)) == pytest.approx(
        exe.exe_07(c).meta["commit"]
    )


def test_invalid_segment_rejected(ctx):
    with pytest.raises(exe.InvalidSegment):
        exe.drill_condition(ctx(), "EXE-07", "everything")
