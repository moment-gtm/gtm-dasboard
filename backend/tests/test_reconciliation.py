"""AC-01 reconciliation: all 44 metrics across all 9 modules vs independent SQL on `raw_*` tables.

Every dashboard metric is recomputed here from the `raw_*` layer without going through the mart views,
and compared against the semantic layer within the 0.5% tolerance of AC-01 — including across three
consecutive ELT refresh cycles (`rebuild()`).
"""

from __future__ import annotations

from datetime import date, timedelta

from app.data import reference_data as ref
from app.data.capacity_data import ARCHITECT_ROLE
from app.platform.db import Platform, rebuild
from app.semantic import definitions, dq
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.filters import FilterParams
from app.semantic.metrics import acc, adm, cap, exe, mkt, off, par, pip, pur
from app.semantic.rls import resolve_user
from app.semantic.status import setting

TOL = 0.005  # AC-01: within 0.5% of the source system


def _ctx(platform, **kw) -> QueryContext:
    return QueryContext(
        platform=platform,
        params=FilterParams(**kw),
        user=resolve_user(platform, "gtm_lead"),
    )


def _raw_tcv(alias: str = "o") -> str:
    return f"round({alias}.amount * fx.rate_to_usd, 2)"


def _within(actual: float | None, expected: float | None, tol: float = TOL) -> bool:
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False
    if expected == 0:
        return abs(actual) <= 1e-6
    return abs(actual - expected) / max(abs(expected), 1e-9) <= tol


# =================================================================================================
# 1. Executive Summary (EXE-01 .. EXE-10)
# =================================================================================================
def test_exe01_bookings_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    expected = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won AND o.close_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )
    actual = exe.exe_01(c).value
    assert _within(actual, float(expected))


def test_exe02_coverage_reconciles_to_raw_crm_and_targets(platform):
    c = _ctx(platform)
    cq = h.quarter_key(c.today)
    nq = h.next_quarter(cq)
    w0, w1 = h.quarter_bounds(cq)[0], h.quarter_bounds(nq)[1]
    qualified = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND NOT o.is_closed
              AND o.stage IN ('Qualify','Propose','Orals','Negotiate')
              AND o.close_date BETWEEN ? AND ?""",
        [w0, w1],
    )
    booked = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won AND o.close_date BETWEEN ? AND ?""",
        [w0, min(c.today, w1)],
    )
    plan = platform.scalar(
        "SELECT coalesce(sum(amount_usd), 0) FROM raw_planning_target "
        "WHERE printf('%d-Q%d', fiscal_year, quarter) IN (?, ?)",
        [cq, nq],
    )
    expected = float(qualified) / (float(plan) - float(booked))
    actual = exe.exe_02(c).value
    assert _within(actual, expected)


def test_exe03_win_rate_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    row = platform.query(
        """SELECT count(*) FILTER (WHERE o.is_won) AS won,
                  count(*) FILTER (WHERE o.is_won OR o.stage = 'Closed Lost') AS decided
           FROM raw_crm_opportunity o
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND o.close_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )[0]
    expected = row["won"] / row["decided"]
    actual = exe.exe_03(c).value
    assert _within(actual, expected)


def test_exe04_new_pipeline_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    expected = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.created_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )
    actual = exe.exe_04(c).value
    assert _within(actual, float(expected))


def test_exe05_offering_led_share_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    row = platform.query(
        f"""SELECT coalesce(sum({_raw_tcv()}) FILTER (
                       WHERE o.offering IS NOT NULL
                         AND trim(o.offering) <> ''
                         AND o.offering <> 'Capability-led'
                   ), 0) AS led,
                   coalesce(sum({_raw_tcv()}), 0) AS total
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND NOT o.is_closed"""
    )[0]
    expected = row["led"] / row["total"]
    actual = exe.exe_05(c).value
    assert _within(actual, expected)


def test_exe06_avg_cycle_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    expected = platform.scalar(
        """SELECT avg(date_diff('day', o.created_date, o.close_date))
           FROM raw_crm_opportunity o
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND o.is_won AND o.close_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )
    actual = exe.exe_06(c).value
    assert _within(actual, float(expected))


def test_exe07_runway_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    fy_start = date(c.today.year, 1, 1)
    q0, q1 = h.quarter_bounds(h.quarter_key(c.today))
    booked = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won AND o.close_date BETWEEN ? AND ?""",
        [fy_start, c.today],
    )
    open_rows = platform.query(
        """SELECT o.stage, sum(round(o.amount * fx.rate_to_usd * sp.probability, 2)) AS w
           FROM raw_crm_opportunity o
           JOIN ref_fx_rate fx ON fx.currency = o.currency
           JOIN ref_stage_probability sp ON sp.stage = o.stage
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND NOT o.is_closed AND o.close_date BETWEEN ? AND ?
           GROUP BY o.stage""",
        [q0, q1],
    )
    commit = sum(r["w"] for r in open_rows if r["stage"] in ("Orals", "Negotiate"))
    best = sum(r["w"] for r in open_rows if r["stage"] in ("Qualify", "Propose"))
    res = exe.exe_07(c)
    by_comp = {b["component"]: b["value"] for b in res.breakdown}
    assert _within(by_comp["booked"], float(booked))
    assert _within(by_comp["commit"], float(commit))
    assert _within(by_comp["best_case"], float(best))
    assert _within(res.value, float(booked))


def test_exe08_09_concentration_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    res08 = exe.exe_08(c)
    raw08 = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0) FROM raw_crm_opportunity o
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won AND year(o.close_date) = ? AND o.close_date <= ?""",
        [c.today.year, c.today],
    )
    assert _within(sum(b["bookings"] for b in res08.breakdown), float(raw08))

    res09 = exe.exe_09(c)
    raw09 = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0) FROM raw_crm_opportunity o
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND NOT o.is_closed"""
    )
    assert _within(sum(b["total"] for b in res09.breakdown), float(raw09))


def test_exe10_attention_reconciles_to_raw_crm(platform):
    c = _ctx(platform)
    expected = platform.scalar(
        f"""WITH cur AS (
                SELECT opportunity_id, max(entered_date) AS stage_entered
                FROM raw_crm_opportunity_history
                GROUP BY 1
            )
            SELECT count(*)
            FROM raw_crm_opportunity o
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            LEFT JOIN cur ON cur.opportunity_id = o.opportunity_id
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND NOT o.is_closed
              AND {_raw_tcv()} >= 2000000
              AND (date_diff('day', coalesce(cur.stage_entered, o.created_date), ?) > 60
                   OR o.close_date < ?)""",
        [c.today, c.today],
    )
    assert exe.exe_10(c)[0].value == expected


def test_drilldown_reconciles_to_parent_metric(platform):
    c = _ctx(platform)
    bookings = exe.exe_01(c).value
    cond, args, _ = exe.drill_condition(c, "EXE-01", None)
    rows = exe.select_rows(c, cond, args, limit=1000)
    assert _within(sum(r.tcv for r in rows), bookings, tol=1e-6)

    res07 = exe.exe_07(c)
    by_comp = {b["component"]: b["value"] for b in res07.breakdown}
    for seg in ("commit", "best_case", "booked"):
        cond, args, _ = exe.drill_condition(c, "EXE-07", seg)
        rows = exe.select_rows(c, cond, args, limit=1000)
        tot = sum(r.tcv if seg == "booked" else r.weighted_tcv for r in rows)
        assert _within(tot, by_comp[seg], tol=1e-6)


# =================================================================================================
# 2. Pipeline (PIP-01 .. PIP-07)
# =================================================================================================
def test_pip_metrics_reconcile_to_raw(platform):
    c = _ctx(platform)
    # PIP-01: Trailing-4Q conversion Identify -> Closed Won from raw_crm_opportunity_history
    win_start = h.quarter_bounds(h.last_n_quarters(c.today, 4)[0])[0]
    reached_raw = {
        r["stage"]: r["n"]
        for r in platform.query(
            """SELECT hst.stage, count(DISTINCT hst.opportunity_id) AS n
               FROM raw_crm_opportunity_history hst
               JOIN raw_crm_opportunity o ON o.opportunity_id = hst.opportunity_id
               WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
                 AND o.created_date >= ?
               GROUP BY hst.stage""",
            [win_start],
        )
    }
    expected_pip01 = h.ratio(reached_raw.get("Closed Won", 0), reached_raw.get("Identify", 0))
    assert _within(pip.pip_01(c).value, expected_pip01)

    # PIP-02 & PIP-05 & PIP-06: Open deal count and total open TCV from raw_crm_opportunity
    open_raw = platform.query(
        f"""SELECT count(*) AS n, coalesce(sum({_raw_tcv()}), 0) AS tcv
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND NOT o.is_closed"""
    )[0]
    assert _within(pip.pip_02(c).value, float(open_raw["n"]))
    assert _within(pip.pip_05(c).value, float(open_raw["n"]))
    assert _within(pip.pip_06(c).value, float(open_raw["n"]))

    # PIP-03: Practice mix total from raw_crm_opportunity_line_item
    line_total = platform.scalar(
        """SELECT coalesce(sum(round(li.amount * fx.rate_to_usd, 2)), 0)
           FROM raw_crm_opportunity_line_item li
           JOIN raw_crm_opportunity o ON o.opportunity_id = li.opportunity_id
           JOIN ref_fx_rate fx ON fx.currency = o.currency
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND NOT o.is_closed"""
    )
    assert _within(pip.pip_03(c).value, float(line_total))

    # PIP-04: Platform mix total equals open TCV
    assert _within(pip.pip_04(c).value, float(open_raw["tcv"]))

    # PIP-07: Week-over-week net movement from replayed snapshot history
    snaps = [
        r["d"]
        for r in platform.query(
            "SELECT DISTINCT snapshot_date AS d FROM fact_opportunity_snapshot "
            "WHERE snapshot_date <= ? ORDER BY d DESC LIMIT 2",
            [c.today],
        )
    ]
    cur_s, prev_s = snaps[0], snaps[1]
    open_st = "('Identify','Qualify','Propose','Orals','Negotiate')"
    snap_totals = platform.query(
        f"""SELECT coalesce(sum(
                       CASE WHEN s.snapshot_date = ? AND s.stage IN {open_st} THEN s.tcv_usd END
                   ), 0) AS cur_tcv,
                   coalesce(sum(
                       CASE WHEN s.snapshot_date = ? AND s.stage IN {open_st} THEN s.tcv_usd END
                   ), 0) AS prev_tcv
            FROM fact_opportunity_snapshot s
            JOIN raw_crm_opportunity o ON o.opportunity_id = s.opportunity_id
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND s.snapshot_date IN (?, ?)""",
        [cur_s, prev_s, cur_s, prev_s],
    )[0]
    assert _within(pip.pip_07(c).value, float(snap_totals["cur_tcv"] - snap_totals["prev_tcv"]))


# =================================================================================================
# 3. Pursuits & Wins (PUR-01 .. PUR-06)
# =================================================================================================
def test_pur_metrics_reconcile_to_raw(platform):
    c = _ctx(platform)
    quarters4 = h.last_n_quarters(c.today, 4)
    qmarks4 = ",".join("?" * 4)

    # PUR-01 & PUR-03: Trailing-4Q win rate from raw_crm_opportunity
    wr_raw = platform.query(
        f"""SELECT count(*) FILTER (WHERE o.is_won) AS won,
                   count(*) FILTER (WHERE o.is_won OR o.stage = 'Closed Lost') AS decided
            FROM raw_crm_opportunity o
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND printf('%d-Q%d', year(o.close_date), quarter(o.close_date)) IN ({qmarks4})
              AND o.close_date <= ?""",
        [*quarters4, c.today],
    )[0]
    expected_wr = wr_raw["won"] / wr_raw["decided"]
    assert _within(pur.pur_01(c).value, expected_wr)
    assert _within(pur.pur_03(c).value, expected_wr)

    # PUR-02: Top loss reason share from raw_crm_opportunity
    loss_rows = platform.query(
        f"""SELECT coalesce(nullif(trim(o.loss_reason), ''), 'Not recorded') AS reason, count(*) AS n
            FROM raw_crm_opportunity o
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.stage = 'Closed Lost'
              AND printf('%d-Q%d', year(o.close_date), quarter(o.close_date)) IN ({qmarks4})
              AND o.close_date <= ?
            GROUP BY 1 ORDER BY n DESC""",
        [*quarters4, c.today],
    )
    total_lost = sum(r["n"] for r in loss_rows)
    top_recorded = next(r["n"] for r in loss_rows if r["reason"] != "Not recorded")
    assert _within(pur.pur_02(c).value, top_recorded / total_lost)

    # PUR-04 & PUR-05: Bid discipline & Orals conversion from raw_bid_pursuit + raw_crm_opportunity
    bid_win_start = h.quarter_bounds(quarters4[0])[0]
    bid_raw = platform.query(
        """SELECT count(*) AS total,
                  count(*) FILTER (WHERE lower(b.decision) IN ('no_bid', 'no bid', 'no-bid')) AS no_bid,
                  count(*) FILTER (WHERE b.orals_reached AND o.is_won) AS orals_won,
                  count(*) FILTER (
                      WHERE b.orals_reached AND (o.is_won OR o.stage = 'Closed Lost')
                  ) AS orals_decided
           FROM raw_bid_pursuit b
           JOIN raw_crm_opportunity o ON o.opportunity_id = b.opportunity_id
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND o.created_date >= ?""",
        [bid_win_start],
    )[0]
    assert _within(pur.pur_04(c).value, bid_raw["no_bid"] / bid_raw["total"])
    assert _within(pur.pur_05(c).value, bid_raw["orals_won"] / bid_raw["orals_decided"])

    # PUR-06: Margin erosion at bid vs delivery from raw_pricing_version + raw_finance_project_financials
    quarters8 = h.last_n_quarters(c.today, 8)
    qmarks8 = ",".join("?" * len(quarters8))
    m_raw = platform.query(
        f"""WITH latest_pv AS (
                SELECT opportunity_id, arg_max(bid_margin_pct, version) / 100.0 AS bid_m
                FROM raw_pricing_version GROUP BY 1
            ),
            latest_fin AS (
                SELECT opportunity_id, arg_max(delivery_margin_pct, as_of_month) / 100.0 AS del_m
                FROM raw_finance_project_financials GROUP BY 1
            )
            SELECT sum({_raw_tcv()} * pv.bid_m) / sum({_raw_tcv()}) AS bid_m,
                   sum({_raw_tcv()} * fin.del_m) / sum({_raw_tcv()}) AS del_m
            FROM raw_crm_opportunity o
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            JOIN latest_pv pv ON pv.opportunity_id = o.opportunity_id
            JOIN latest_fin fin ON fin.opportunity_id = o.opportunity_id
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won
              AND fin.del_m IS NOT NULL
              AND printf('%d-Q%d', year(o.close_date), quarter(o.close_date)) IN ({qmarks8})
              AND o.close_date <= ?""",
        [*quarters8, c.today],
    )[0]
    assert _within(pur.pur_06(c).value, float(m_raw["bid_m"] - m_raw["del_m"]))


# =================================================================================================
# 4. Offerings (OFF-01 .. OFF-05)
# =================================================================================================
def test_off_metrics_reconcile_to_raw(platform):
    c = _ctx(platform)
    # OFF-01: Offering-led share of open + FY won TCV
    row_off01 = platform.query(
        f"""SELECT coalesce(sum({_raw_tcv()}) FILTER (
                       WHERE o.offering IS NOT NULL
                         AND trim(o.offering) <> ''
                         AND o.offering <> 'Capability-led'
                   ), 0) AS led,
                   coalesce(sum({_raw_tcv()}), 0) AS total
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND (NOT o.is_closed OR (o.is_won AND o.close_date BETWEEN ? AND ?))""",
        [c.period.start, c.today],
    )[0]
    assert _within(off.off_01(c).value, row_off01["led"] / row_off01["total"])

    # OFF-02: Multi-practice attach rate on won deals in period from raw_crm_opportunity_line_item
    att_raw = platform.query(
        """SELECT count(*) AS total, count(*) FILTER (WHERE n_prac >= 2) AS multi FROM (
               SELECT o.opportunity_id, count(DISTINCT li.practice) AS n_prac
               FROM raw_crm_opportunity o
               LEFT JOIN raw_crm_opportunity_line_item li ON li.opportunity_id = o.opportunity_id
               WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
                 AND o.is_won AND o.close_date BETWEEN ? AND ?
               GROUP BY o.opportunity_id
           )""",
        [c.period.start, c.today],
    )[0]
    assert _within(off.off_02(c).value, att_raw["multi"] / att_raw["total"])

    # OFF-03: Unvalidated AI-led open TCV from raw_crm_opportunity + raw_validation_record
    unval_raw = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            LEFT JOIN raw_validation_record v
                   ON v.validation_id = o.validation_id AND v.opportunity_id = o.opportunity_id
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND NOT o.is_closed
              AND o.ai_led = TRUE
              AND coalesce(v.status, '') <> 'Validated'"""
    )
    assert _within(off.off_03(c).value, float(unval_raw))

    # OFF-04: Flagged assets (<low_reuse uses in 365d or >refresh_due_days since refresh) from raw_kb_asset
    low = int(setting(platform, "OFF-04.low_reuse_uses", 8))
    stale = int(setting(platform, "OFF-04.refresh_due_days", 180))
    since = c.today - timedelta(days=365)
    flagged_raw = platform.scalar(
        """SELECT count(*) FROM (
               SELECT a.asset_id, a.last_refreshed,
                      count(u.asset_id) FILTER (WHERE u.used_on > ?) AS uses
               FROM raw_kb_asset a
               LEFT JOIN (
                   SELECT ba.asset_id, ba.used_on
                   FROM raw_bid_proposal_asset ba
                   JOIN raw_crm_opportunity o ON o.opportunity_id = ba.opportunity_id
                   WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
               ) u ON u.asset_id = a.asset_id
               GROUP BY a.asset_id, a.last_refreshed
           ) WHERE uses < ? OR date_diff('day', last_refreshed, ?) > ?""",
        [since, low, c.today, stale],
    )
    assert _within(off.off_04(c).value, float(flagged_raw))

    # OFF-05: Released complete asset builds from raw_asset_build
    released_raw = platform.scalar(
        """SELECT count(*) FROM raw_asset_build
           WHERE status = 'Released' AND asset_id IS NOT NULL AND asset_type IS NOT NULL"""
    )
    assert _within(off.off_05(c).value, float(released_raw))


# =================================================================================================
# 5. Accounts (ACC-01 .. ACC-04)
# =================================================================================================
def test_acc_metrics_reconcile_to_raw(platform):
    c = _ctx(platform)
    fy_start = date(c.today.year, 1, 1)
    n_accounts = platform.scalar("SELECT count(*) FROM raw_crm_account")
    total_cells = n_accounts * len(ref.PRACTICES)

    cell_rows = platform.query(
        """SELECT o.account_id, li.practice,
                  bool_or(o.is_won AND o.close_date BETWEEN ? AND ?) AS sold,
                  bool_or(NOT o.is_closed) AS open_deal
           FROM raw_crm_opportunity o
           JOIN raw_crm_opportunity_line_item li ON li.opportunity_id = o.opportunity_id
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
           GROUP BY 1, 2""",
        [fy_start, c.today],
    )
    sold_cells = sum(1 for r in cell_rows if r["sold"])
    open_only_cells = sum(1 for r in cell_rows if not r["sold"] and r["open_deal"])
    whitespace_cells = total_cells - sold_cells

    # ACC-01 & ACC-02
    assert _within(acc.acc_01(c).value, sold_cells / total_cells)
    assert _within(acc.acc_02(c).value, open_only_cells / whitespace_cells)

    # ACC-03: Expansion share of won TCV from raw_crm_opportunity + raw_booking_history
    exp_raw = platform.query(
        f"""SELECT coalesce(sum({_raw_tcv()}) FILTER (WHERE EXISTS (
                       SELECT 1 FROM raw_booking_history bh
                       WHERE bh.account_id = o.account_id
                         AND CAST(bh.booked_month || '-01' AS DATE) < o.close_date
                         AND CAST(bh.booked_month || '-01' AS DATE) >= o.close_date - INTERVAL 24 MONTH
                   )), 0) AS exp_tcv,
                   coalesce(sum({_raw_tcv()}), 0) AS total_tcv
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won AND o.close_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )[0]
    assert _within(acc.acc_03(c).value, exp_raw["exp_tcv"] / exp_raw["total_tcv"])

    # ACC-04: Strategic account plans reviewed within current_days from raw_account_plan
    cur_days = setting(platform, "ACC-04.current_days", 90)
    plan_raw = platform.query(
        """SELECT count(*) AS total,
                  count(*) FILTER (
                      WHERE p.last_review_date IS NOT NULL
                        AND date_diff('day', p.last_review_date, ?) <= ?
                  ) AS current_n
           FROM raw_crm_account a
           LEFT JOIN raw_account_plan p ON p.account_id = a.account_id
           WHERE a.strategic = TRUE""",
        [c.today, cur_days],
    )[0]
    assert _within(acc.acc_04(c).value, plan_raw["current_n"] / plan_raw["total"])


# =================================================================================================
# 6. Partners (PAR-01 .. PAR-03)
# =================================================================================================
def test_par_metrics_reconcile_to_raw(platform):
    c = _ctx(platform)
    # PAR-01: Open partner pipeline from raw_crm_opportunity
    par_open = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND NOT o.is_closed
              AND o.partner IS NOT NULL AND trim(o.partner) <> ''"""
    )
    assert _within(par.par_01(c).value, float(par_open))

    # PAR-02: Co-sell win rate with partner from raw_crm_opportunity
    cosell_raw = platform.query(
        """SELECT count(*) FILTER (WHERE o.is_won) AS won,
                  count(*) FILTER (WHERE o.is_won OR o.stage = 'Closed Lost') AS decided
           FROM raw_crm_opportunity o
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND (o.is_won OR o.stage = 'Closed Lost')
             AND o.close_date BETWEEN ? AND ?
             AND o.partner IS NOT NULL AND trim(o.partner) <> ''""",
        [c.period.start, c.today],
    )[0]
    assert _within(par.par_02(c).value, cosell_raw["won"] / cosell_raw["decided"])

    # PAR-03: Partner certification attainment from raw_partner_tier + raw_partner_certification
    cert_rows = platform.query(
        """SELECT t.partner, t.required_certifications AS req,
                  count(c.partner) FILTER (WHERE c.expires_on >= ?) AS cert
           FROM raw_partner_tier t
           LEFT JOIN raw_partner_certification c ON c.partner = t.partner
           GROUP BY t.partner, t.required_certifications""",
        [c.today],
    )
    req_total = sum(int(r["req"]) for r in cert_rows)
    counted_total = sum(min(int(r["cert"]), int(r["req"])) for r in cert_rows)
    assert _within(par.par_03(c).value, counted_total / req_total)


# =================================================================================================
# 7. Solutions & Capacity (CAP-01 .. CAP-04)
# =================================================================================================
def test_cap_metrics_reconcile_to_raw(platform):
    c = _ctx(platform)
    # CAP-01: Architects over capacity (>watch open Qualify/Propose/Orals pursuits)
    arch_rows = platform.query(
        """SELECT r.resource_id, count(*) AS load
           FROM raw_crm_opportunity_team t
           JOIN raw_crm_opportunity o ON o.opportunity_id = t.opportunity_id
           JOIN raw_resource r ON r.resource_id = t.resource_id
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND t.role = ?
             AND o.stage IN ('Qualify', 'Propose', 'Orals')
           GROUP BY r.resource_id""",
        [ARCHITECT_ROLE],
    )
    over_raw = sum(1 for r in arch_rows if int(r["load"]) >= 5)
    assert _within(cap.cap_01(c).value, float(over_raw))

    quarters4 = h.last_n_quarters(c.today, 4)
    qmarks4 = ",".join("?" * 4)

    # CAP-02: SLA turnaround share from raw_bid_pursuit
    sla_raw = platform.query(
        f"""SELECT count(*) AS submitted,
                   count(*) FILTER (
                       WHERE date_diff('day', b.rfp_received, b.rfp_submitted) <= b.sla_target_days
                   ) AS on_time
            FROM raw_bid_pursuit b
            JOIN raw_crm_opportunity o ON o.opportunity_id = b.opportunity_id
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND b.rfp_submitted IS NOT NULL AND b.rfp_submitted <= ?
              AND printf('%d-Q%d', year(b.rfp_submitted), quarter(b.rfp_submitted)) IN ({qmarks4})""",
        [c.today, *quarters4],
    )[0]
    assert _within(cap.cap_02(c).value, sla_raw["on_time"] / sla_raw["submitted"])

    # CAP-03: Cost of sale from raw_timesheet_entry + raw_finance_cost_rate + raw_crm_opportunity
    cos_raw = platform.query(
        f"""WITH effort AS (
                SELECT ts.opportunity_id, sum(ts.hours * rc.rate_usd_hour) AS cost_usd
                FROM raw_timesheet_entry ts
                JOIN raw_resource rr ON rr.resource_id = ts.resource_id
                JOIN raw_finance_cost_rate rc ON rc.role = rr.role
                GROUP BY ts.opportunity_id
            )
            SELECT sum(e.cost_usd) AS cost, sum({_raw_tcv()}) AS tcv
            FROM effort e
            JOIN raw_crm_opportunity o ON o.opportunity_id = e.opportunity_id
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND (o.is_won OR o.stage = 'Closed Lost')
              AND printf('%d-Q%d', year(o.close_date), quarter(o.close_date)) IN ({qmarks4})
              AND o.close_date <= ?""",
        [*quarters4, c.today],
    )[0]
    assert _within(cap.cap_03(c).value, float(cos_raw["cost"] / cos_raw["tcv"]))

    # CAP-04: Proposal quality average score on won pursuits from raw_bid_quality_review
    qa_won_raw = platform.scalar(
        f"""SELECT avg(q.quality_score)
            FROM raw_bid_quality_review q
            JOIN raw_crm_opportunity o ON o.opportunity_id = q.opportunity_id
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won
              AND printf('%d-Q%d', year(o.close_date), quarter(o.close_date)) IN ({qmarks4})
              AND o.close_date <= ?""",
        [*quarters4, c.today],
    )
    assert _within(cap.cap_04(c).value, float(qa_won_raw))


# =================================================================================================
# 8. Market Signals (MKT-01 .. MKT-04) & Administration (ADM-01)
# =================================================================================================
def test_mkt03_campaign_pipeline_reconciles_crm_vs_marketing_automation(platform):
    """AC-01 / RSD §6.1: Campaign-sourced pipeline reconciles between SRC-01 and SRC-10 within 0.5%."""
    c = _ctx(platform)
    res = mkt.mkt_03(c)

    crm_tcv = platform.scalar(
        f"""SELECT coalesce(sum({_raw_tcv()}), 0)
            FROM raw_crm_opportunity o
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.campaign_id IS NOT NULL
              AND o.created_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )
    mktg_tcv = platform.scalar(
        """SELECT coalesce(sum(m.attributed_tcv_usd), 0)
           FROM raw_mktg_campaign_member m
           JOIN raw_crm_opportunity o ON o.opportunity_id = m.opportunity_id
           WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
             AND m.primary_source = TRUE
             AND o.created_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )
    assert _within(res.value, float(crm_tcv))
    assert _within(float(crm_tcv), float(mktg_tcv))
    assert res.meta["reconciled"] is True


def test_mkt_and_adm_metrics_reconcile_to_raw(platform):
    c = _ctx(platform)
    quarters4 = h.last_n_quarters(c.today, 4)
    qmarks4 = ",".join("?" * 4)

    # MKT-01: Thought leadership POVs published in trailing 4 quarters from raw_web_content_asset
    povs_raw = platform.scalar(
        f"""SELECT count(*) FROM raw_web_content_asset
            WHERE printf('%d-Q%d', year(published_date), quarter(published_date)) IN ({qmarks4})
              AND published_date <= ?""",
        [*quarters4, c.today],
    )
    assert _within(mkt.mkt_01(c).value, float(povs_raw))

    # MKT-02: Discovery workshop <=90d conversion rate from raw_crm_workshop
    ws_raw = platform.query(
        """SELECT count(*) AS held,
                  count(*) FILTER (
                      WHERE w.opportunity_id IS NOT NULL
                        AND w.days_to_opportunity BETWEEN 0 AND 90
                  ) AS conv
           FROM raw_crm_workshop w
           WHERE w.account_id IN (SELECT account_id FROM raw_crm_account)
             AND w.workshop_date BETWEEN ? AND ?""",
        [c.period.start, c.today],
    )[0]
    assert _within(mkt.mkt_02(c).value, ws_raw["conv"] / ws_raw["held"])

    # MKT-04: Analyst evaluations with Leader placement from raw_analyst_evaluation
    leaders_raw = platform.scalar(
        "SELECT count(*) FROM raw_analyst_evaluation WHERE current_placement = 'Leader'"
    )
    assert _within(mkt.mkt_04(c).value, float(leaders_raw))

    # ADM-01: Mandatory-field completeness of qualified opportunities in latest week
    qual_stages = ",".join(f"'{s}'" for s in dq.QUALIFIED_STAGES)
    adm_raw = platform.query(
        f"""WITH qualified AS (
                SELECT opportunity_id, min(entered_date) AS q_date
                FROM raw_crm_opportunity_history
                WHERE stage IN ({qual_stages})
                GROUP BY opportunity_id
            )
            SELECT count(*) AS qual,
                   count(*) FILTER (
                       WHERE o.offering IS NOT NULL AND trim(o.offering) <> ''
                         AND coalesce(trim(o.lead_practice), '') <> ''
                         AND coalesce(trim(o.primary_platform), '') <> ''
                         AND coalesce(trim(o.lead_source), '') <> ''
                         AND coalesce(trim(o.owner_upn), '') <> ''
                   ) AS comp
            FROM qualified q
            JOIN raw_crm_opportunity o ON o.opportunity_id = q.opportunity_id
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND q.q_date <= ?""",
        [c.today],
    )[0]
    assert _within(adm.adm_01(c).value, adm_raw["comp"] / adm_raw["qual"])


def test_finance_month_end_reconciliation_within_half_percent(platform):
    """RSD §6.1: SRC-04 Finance month-end close reconciles to booked actuals within 0.5%."""
    row = platform.query(
        f"""SELECT count(*) AS n,
                   max(abs(fc.amount_usd - {_raw_tcv()}) / nullif({_raw_tcv()}, 0)) AS max_var
            FROM raw_finance_contract fc
            JOIN raw_crm_opportunity o ON o.opportunity_id = fc.crm_opportunity_id
            JOIN ref_fx_rate fx ON fx.currency = o.currency
            WHERE o.account_id IN (SELECT account_id FROM raw_crm_account)
              AND o.is_won"""
    )[0]
    assert int(row["n"]) > 0
    assert float(row["max_var"] or 0.0) <= TOL


# =================================================================================================
# 9. AC-01 Gate: All 44 Metrics Reconcile Across Three Consecutive Refresh Cycles
# =================================================================================================
ALL_METRIC_EVALUATORS = {
    **{f"EXE-{i:02d}": getattr(exe, f"exe_{i:02d}") for i in range(1, 10)},
    "EXE-10": lambda c: exe.exe_10(c)[0],
    **pip.FUNCTIONS,
    **pur.FUNCTIONS,
    **pur.RESTRICTED_FUNCTIONS,
    **off.FUNCTIONS,
    **acc.FUNCTIONS,
    **par.FUNCTIONS,
    **cap.FUNCTIONS,
    **cap.RESTRICTED_FUNCTIONS,
    **mkt.FUNCTIONS,
    "ADM-01": adm.adm_01,
}


def test_all_44_metrics_registered_and_reconcile_across_three_consecutive_refreshes():
    """AC-01: All 44 registered metrics reconcile within 0.5% across 3 consecutive refresh cycles."""
    assert set(ALL_METRIC_EVALUATORS.keys()) == set(definitions.METRICS.keys())
    assert len(ALL_METRIC_EVALUATORS) == 44

    baseline_values: dict[str, float | None] = {}
    baseline_row_counts: dict[str, int] = {}

    for cycle in range(1, 4):
        p: Platform = rebuild()
        c = _ctx(p)
        for mid, fn in ALL_METRIC_EVALUATORS.items():
            res = fn(c)
            assert res.metric_id == mid, f"Cycle {cycle}: metric_id mismatch for {mid}"
            assert res.value is not None, f"Cycle {cycle}: {mid} returned None value"
            if cycle == 1:
                baseline_values[mid] = float(res.value)
            else:
                assert _within(float(res.value), baseline_values[mid]), (
                    f"Cycle {cycle} drift on {mid}: {res.value} vs {baseline_values[mid]}"
                )

        # Also verify key mart row counts remain invariant across consecutive ELT rebuilds
        for table in ("mart_opportunity", "mart_opportunity_snapshot", "mart_target", "dq_finding"):
            cnt = int(p.scalar(f"SELECT count(*) FROM {table}"))
            if cycle == 1:
                baseline_row_counts[table] = cnt
            else:
                assert cnt == baseline_row_counts[table], (
                    f"Cycle {cycle} row count drift on {table}: {cnt} vs {baseline_row_counts[table]}"
                )
