"""Global filters (FR-GEN-02/03) and filtered target comparison / pro-rating (FR-GEN-04)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.data import reference_data as ref
from app.semantic.filters import FilterParams, resolve_period
from app.semantic.metrics import exe
from app.semantic.targets import target_slice

TODAY = date(2026, 8, 14)


def test_period_resolution():
    assert resolve_period(FilterParams(), TODAY).label == "FY26 YTD"
    qtd = resolve_period(FilterParams(period="qtd"), TODAY)
    assert (qtd.start, qtd.end, qtd.label) == (date(2026, 7, 1), TODAY, "FY26 Q3 QTD")
    q = resolve_period(FilterParams(period="quarter", quarter="2026-Q1"), TODAY)
    assert (q.start, q.end) == (date(2026, 1, 1), date(2026, 3, 31))


@pytest.mark.parametrize(
    "bad",
    [
        {"period": "quarter"},
        {"period": "quarter", "quarter": "2026-Q9"},
        {"period": "custom", "start": "2026-03-01"},
        {"period": "custom", "start": "2026-03-01", "end": "2026-01-01"},
    ],
)
def test_invalid_period_rejected(bad):
    with pytest.raises(ValidationError):
        FilterParams(**bad)


def test_vertical_filters_partition_the_total(ctx):
    total = exe.exe_09(ctx()).value
    parts = sum(exe.exe_09(ctx(vertical=[v])).value for v in ref.VERTICALS)
    assert parts == pytest.approx(total)


def test_filters_apply_to_every_kpi(ctx):
    all_ = {m.metric_id: m.value for m in (fn(ctx()) for fn in exe.KPI_FUNCTIONS)}
    bfsi = {m.metric_id: m.value for m in (fn(ctx(vertical=["BFSI"])) for fn in exe.KPI_FUNCTIONS)}
    assert bfsi["EXE-01"] < all_["EXE-01"] and bfsi["EXE-04"] < all_["EXE-04"]


def test_quarter_period_changes_bookings(ctx):
    q2 = exe.exe_01(ctx(period="quarter", quarter="2026-Q2"))
    q2_row = next(r for r in exe.exe_08(ctx()).breakdown if r["quarter"] == "2026-Q2")
    assert q2.value == pytest.approx(q2_row["bookings"])
    assert q2.target == pytest.approx(q2_row["target"])  # completed quarter: pace = full target
    assert q2.goal == pytest.approx(q2.target)


def test_exact_target_at_practice_grain(ctx):
    ts = target_slice(ctx(practice=["DxP"]), ["2026-Q1"])
    assert not ts.prorated
    assert ts.by_quarter["2026-Q1"] == pytest.approx(225e6 * 0.22 * ref.PRACTICE_TARGET_SHARE["DxP"])


def test_vertical_filter_prorates_and_labels(ctx):
    c = ctx(vertical=["BFSI"])
    ts = target_slice(c, ["2026-Q1", "2026-Q2"])
    assert ts.prorated and "Pro-rated" in ts.basis
    share = ts.shares[2026]
    assert 0 < share < 1
    assert ts.by_quarter["2026-Q1"] == pytest.approx(225e6 * 0.22 * share)
    m = exe.exe_01(c)
    assert m.target_prorated and m.target_basis.startswith("Pro-rated")


def test_shares_across_verticals_sum_to_one(ctx):
    total = sum(target_slice(ctx(vertical=[v]), ["2026-Q1"]).shares[2026] for v in ref.VERTICALS)
    assert total == pytest.approx(1.0)


def test_practice_plus_vertical_prorates_practice_target(ctx):
    ts = target_slice(ctx(practice=["DxP"], vertical=["BFSI"]), ["2026-Q1"])
    assert ts.prorated and ts.basis.startswith("Pro-rated: practice-level")


def test_narrow_row_scope_prorates_without_filters(ctx):
    ts = target_slice(ctx("client_partner"), ["2026-Q1"])
    assert ts.prorated and "your data scope" in ts.basis
