"""Executive summary metrics EXE-01 … EXE-10 (RSD v0.9.1 §5, exactly as defined there).

Metric-module contract: one function per metric ID returning a MetricResult. Every query is
built through QueryContext.where (global filters + RLS). Drill-down conditions reuse the same
predicates as the metrics, so a drill-down always adds up to the number it came from.
"""

from __future__ import annotations

from datetime import date

from app.config import settings
from app.schemas.common import AggregatedOther, MetricResult, OpportunityRow, SparkPoint
from app.semantic import definitions
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.freshness import iso, last_success
from app.semantic.status import band, setting, threshold
from app.semantic.targets import TargetSlice, target_slice

WON = "o.stage_group = 'won'"
OPEN = "o.stage_group = 'open'"
QUALIFIED = "o.stage IN ('Qualify', 'Propose', 'Orals', 'Negotiate')"
COMMIT = "o.stage IN ('Orals', 'Negotiate')"
BEST_CASE = "o.stage IN ('Qualify', 'Propose')"
SUM_TCV = "coalesce(sum(o.tcv_usd), 0)"


# --- shared plumbing --------------------------------------------------------------------------
def _result(ctx: QueryContext, metric_id: str, unit: str, value: float | None, **kw) -> MetricResult:
    meta = definitions.get(metric_id)
    return MetricResult(
        metric_id=metric_id,
        name=meta["name"],
        unit=unit,
        value=value,
        goal_label=kw.pop("goal_label", meta["goal_label"]),
        period=ctx.period.to_info(),
        as_of=iso(last_success(ctx.platform, "crm")),
        sources=meta["sources"],
        **kw,
    )


def _status(ctx: QueryContext, metric_id: str, value: float | None):
    s = band(ctx.platform, metric_id, value)
    return None if s is None else s.value


def _actuals_end(ctx: QueryContext) -> date:
    return min(ctx.period.end, ctx.today)


def _no_target_basis(ts: TargetSlice) -> str | None:
    return None if ts.available else ts.basis


def _per_quarter(
    ctx: QueryContext, condition: str, select: str, date_col: str, quarters: list[str]
) -> dict[str, float | None]:
    marks = ", ".join("?" * len(quarters))
    col = "close_quarter" if date_col == "close_date" else "created_quarter"
    rows = ctx.rows(
        ctx.where(condition, f"o.{col} IN ({marks})", f"o.{date_col} <= ?", args=[*quarters, ctx.today]),
        select=f"o.{col} AS q, {select} AS v",
        tail=f"GROUP BY o.{col}",
    )
    found = {r["q"]: (None if r["v"] is None else float(r["v"])) for r in rows}
    return {q: found.get(q) for q in quarters}


def _spark(ctx: QueryContext, values: dict[str, float | None]) -> list[SparkPoint]:
    current = h.quarter_key(ctx.today)
    return [SparkPoint(label=h.quarter_label(q), value=v, partial=q == current) for q, v in values.items()]


def _trend_quarters(ctx: QueryContext) -> list[str]:
    return h.last_n_quarters(ctx.today, 4)


# --- EXE-01 Bookings vs target ----------------------------------------------------------------
def exe_01(ctx: QueryContext) -> MetricResult:
    p = ctx.period
    bookings = float(
        ctx.value(ctx.where(WON, "o.close_date BETWEEN ? AND ?", args=[p.start, _actuals_end(ctx)]), SUM_TCV)
    )
    ts = target_slice(ctx, p.quarters)
    target = h.period_target(ts.by_quarter, p.start, p.target_through) if ts.available else None
    pace = h.plan_pace(ts.by_quarter, p.start, p.target_through, ctx.today) if ts.available else None
    attainment = h.ratio(bookings, pace)
    trend = _per_quarter(ctx, WON, SUM_TCV, "close_date", _trend_quarters(ctx))
    return _result(
        ctx,
        "EXE-01",
        "usd",
        bookings,
        target=target,
        target_prorated=ts.prorated,
        target_basis=ts.basis,
        goal=pace,
        attainment=attainment,
        status=_status(ctx, "EXE-01", attainment),
        status_basis=(
            f"{h.fmt_pct(attainment)} of plan pace ({h.fmt_musd(pace)})"
            if attainment is not None
            else _no_target_basis(ts)
        ),
        sparkline=_spark(ctx, trend),
        meta={"pct_of_target": h.ratio(bookings, target), "plan_pace": pace},
    )


# --- EXE-02 Pipeline coverage -----------------------------------------------------------------
def coverage_at(ctx: QueryContext, as_of: date) -> dict:
    cq = h.quarter_key(as_of)
    nq = h.next_quarter(cq)
    w0, w1 = h.quarter_bounds(cq)[0], h.quarter_bounds(nq)[1]
    ts = target_slice(ctx, [cq, nq])
    if as_of >= ctx.today:
        qualified = ctx.value(
            ctx.where(OPEN, QUALIFIED, "o.close_date BETWEEN ? AND ?", args=[w0, w1]), SUM_TCV
        )
    else:
        snap = ctx.platform.scalar(
            "SELECT max(snapshot_date) FROM fact_opportunity_snapshot WHERE snapshot_date <= ?", [as_of]
        )
        qualified = (
            None
            if snap is None
            else ctx.value(
                ctx.where(
                    "o.snapshot_date = ?", QUALIFIED, "o.close_date BETWEEN ? AND ?", args=[snap, w0, w1]
                ),
                SUM_TCV,
                table="mart_opportunity_snapshot",
            )
        )
    booked = float(
        ctx.value(ctx.where(WON, "o.close_date BETWEEN ? AND ?", args=[w0, min(as_of, w1)]), SUM_TCV)
    )
    remaining = ts.total() - booked if ts.available else None
    return {
        "window": [cq, nq],
        "qualified": None if qualified is None else float(qualified),
        "booked": booked,
        "target": ts.total() if ts.available else None,
        "remaining": remaining,
        "coverage": h.ratio(qualified, remaining),
        "slice": ts,
    }


def exe_02(ctx: QueryContext) -> MetricResult:
    cur = coverage_at(ctx, ctx.today)
    trend: dict[str, float | None] = {}
    for q in _trend_quarters(ctx):
        trend[q] = (
            cur["coverage"]
            if q == h.quarter_key(ctx.today)
            else coverage_at(ctx, h.quarter_bounds(q)[1])["coverage"]
        )
    ts: TargetSlice = cur["slice"]
    window = "–".join(h.quarter_label(q) for q in cur["window"])
    met = cur["remaining"] is not None and cur["remaining"] <= 0
    return _result(
        ctx,
        "EXE-02",
        "x",
        cur["coverage"],
        target=cur["remaining"],
        target_prorated=ts.prorated,
        target_basis=ts.basis,
        goal=threshold(ctx.platform, "EXE-02")["on_track"],
        status="on_track" if met else _status(ctx, "EXE-02", cur["coverage"]),
        status_basis=(
            "Target for the window already achieved"
            if met
            else (
                f"{h.fmt_musd(cur['qualified'])} qualified pipeline vs "
                f"{h.fmt_musd(cur['remaining'])} remaining target, {window}"
                if ts.available
                else ts.basis
            )
        ),
        sparkline=_spark(ctx, trend),
        meta={
            "window": cur["window"],
            "qualified_pipeline": cur["qualified"],
            "remaining_target": cur["remaining"],
            "window_target": cur["target"],
            "window_bookings": cur["booked"],
            "trend_basis": "Quarter-end weekly snapshots",
        },
    )


# --- EXE-03 Win rate --------------------------------------------------------------------------
def exe_03(ctx: QueryContext) -> MetricResult:
    p = ctx.period
    r = ctx.rows(
        ctx.where(
            "o.stage_group IN ('won', 'lost')",
            "o.close_date BETWEEN ? AND ?",
            args=[p.start, _actuals_end(ctx)],
        ),
        select="""count(*) FILTER (WHERE o.stage_group = 'won') AS won,
                           count(*) FILTER (WHERE o.stage_group = 'lost') AS lost,
                           coalesce(sum(o.tcv_usd) FILTER (WHERE o.stage_group = 'won'), 0) AS won_tcv,
                           coalesce(sum(o.tcv_usd), 0) AS closed_tcv""",
    )[0]
    rate = h.ratio(r["won"], r["won"] + r["lost"])
    trend = _per_quarter(
        ctx,
        "o.stage_group IN ('won', 'lost')",
        "count(*) FILTER (WHERE o.stage_group = 'won') / nullif(count(*), 0)",
        "close_date",
        _trend_quarters(ctx),
    )
    return _result(
        ctx,
        "EXE-03",
        "pct",
        rate,
        goal=threshold(ctx.platform, "EXE-03")["on_track"],
        status=_status(ctx, "EXE-03", rate),
        status_basis=f"{r['won']} won of {r['won'] + r['lost']} decided (no-bid and cancelled excluded)",
        breakdown=[{"segment": "won", "count": r["won"]}, {"segment": "lost", "count": r["lost"]}],
        sparkline=_spark(ctx, trend),
        meta={"won": r["won"], "lost": r["lost"], "value_win_rate": h.ratio(r["won_tcv"], r["closed_tcv"])},
    )


# --- EXE-04 New pipeline created --------------------------------------------------------------
def exe_04(ctx: QueryContext) -> MetricResult:
    p = ctx.period
    created = float(
        ctx.value(ctx.where("o.created_date BETWEEN ? AND ?", args=[p.start, _actuals_end(ctx)]), SUM_TCV)
    )
    ts = target_slice(ctx, p.quarters)
    multiple = setting(ctx.platform, "EXE-04.goal_multiple", 3.0)
    goal = (
        multiple * h.plan_pace(ts.by_quarter, p.start, p.target_through, ctx.today) if ts.available else None
    )
    attainment = h.ratio(created, goal)
    trend = _per_quarter(ctx, "TRUE", SUM_TCV, "created_date", _trend_quarters(ctx))
    return _result(
        ctx,
        "EXE-04",
        "usd",
        created,
        target=goal,
        target_prorated=ts.prorated,
        target_basis=ts.basis,
        goal=goal,
        attainment=attainment,
        goal_label=f"{multiple:g}× bookings target, pro-rated to today",
        status=_status(ctx, "EXE-04", attainment),
        status_basis=(
            f"{h.fmt_pct(attainment)} of goal ({h.fmt_musd(goal)})"
            if attainment is not None
            else _no_target_basis(ts)
        ),
        sparkline=_spark(ctx, trend),
        meta={"goal_multiple": multiple},
    )


# --- EXE-05 Offering-led pipeline share -------------------------------------------------------
BUCKETS = ("Offering-led", "Capability-led", "Untagged")


def _offering_share(ctx: QueryContext, snapshot: date | None) -> tuple[float | None, list[dict]]:
    if snapshot is None:
        where, table = ctx.where(OPEN), "mart_opportunity"
    else:
        where, table = ctx.where("o.snapshot_date = ?", args=[snapshot]), "mart_opportunity_snapshot"
    rows = ctx.rows(
        where,
        select="o.offering_class AS bucket, sum(o.tcv_usd) AS tcv",
        table=table,
        tail="GROUP BY o.offering_class",
    )
    by = {r["bucket"]: float(r["tcv"]) for r in rows}
    total = sum(by.values())
    buckets = [{"bucket": b, "tcv": by.get(b, 0.0), "share": h.ratio(by.get(b, 0.0), total)} for b in BUCKETS]
    return h.ratio(by.get("Offering-led", 0.0), total), buckets


def exe_05(ctx: QueryContext) -> MetricResult:
    share, buckets = _offering_share(ctx, None)
    trend: dict[str, float | None] = {}
    for q in _trend_quarters(ctx):
        if q == h.quarter_key(ctx.today):
            trend[q] = share
            continue
        snap = ctx.platform.scalar(
            "SELECT max(snapshot_date) FROM fact_opportunity_snapshot WHERE snapshot_date <= ?",
            [h.quarter_bounds(q)[1]],
        )
        trend[q] = None if snap is None else _offering_share(ctx, snap)[0]
    untagged = next(b for b in buckets if b["bucket"] == "Untagged")
    return _result(
        ctx,
        "EXE-05",
        "pct",
        share,
        goal=threshold(ctx.platform, "EXE-05")["on_track"],
        status=_status(ctx, "EXE-05", share),
        status_basis=f"Untagged {h.fmt_musd(untagged['tcv'])} counts against the share (DQ-01)",
        breakdown=buckets,
        sparkline=_spark(ctx, trend),
        meta={"trend_basis": "Quarter-end weekly snapshots"},
    )


# --- EXE-06 Average deal cycle ----------------------------------------------------------------
CYCLE = "avg(date_diff('day', o.created_date, o.close_date))"


def exe_06(ctx: QueryContext) -> MetricResult:
    p = ctx.period
    r = ctx.rows(
        ctx.where(WON, "o.close_date BETWEEN ? AND ?", args=[p.start, _actuals_end(ctx)]),
        select=f"{CYCLE} AS days, count(*) AS n",
    )[0]
    days = None if r["days"] is None else float(r["days"])
    trend = _per_quarter(ctx, WON, CYCLE, "close_date", _trend_quarters(ctx))
    return _result(
        ctx,
        "EXE-06",
        "days",
        days,
        goal=threshold(ctx.platform, "EXE-06")["on_track"],
        status=_status(ctx, "EXE-06", days),
        status_basis=f"Mean over {r['n']} Closed Won deals",
        sparkline=_spark(ctx, trend),
        meta={"deals": r["n"]},
    )


# --- EXE-07 Bookings runway -------------------------------------------------------------------
def runway_components(ctx: QueryContext) -> dict:
    fy = ctx.today.year
    cq = h.quarter_key(ctx.today)
    booked = float(
        ctx.value(
            ctx.where(WON, "year(o.close_date) = ?", "o.close_date <= ?", args=[fy, ctx.today]), SUM_TCV
        )
    )
    weighted = "coalesce(sum(o.weighted_tcv), 0)"
    commit = float(ctx.value(ctx.where(OPEN, COMMIT, "o.close_quarter = ?", args=[cq]), weighted))
    best = float(ctx.value(ctx.where(OPEN, BEST_CASE, "o.close_quarter = ?", args=[cq]), weighted))
    return {"fy": fy, "cq": cq, "booked": booked, "commit": commit, "best_case": best}


def runway_narrative(booked: float, pace: float | None, commit: float, fy_target: float | None) -> str:
    if pace is None or fy_target is None:
        return (
            f"Bookings stand at {h.fmt_musd(booked)}; plan pace and the full-year target are "
            "unavailable until the planning source loads."
        )
    gap = booked - pace
    after_commit = fy_target - booked - commit
    position = "ahead of" if gap >= 0 else "behind"
    tail = (
        f"after weighted commit of {h.fmt_musd(commit)}, {h.fmt_musd(after_commit)} remains to "
        f"the full-year target of {h.fmt_musd(fy_target)}."
        if after_commit > 0
        else f"weighted commit of {h.fmt_musd(commit)} would cover the full-year target of "
        f"{h.fmt_musd(fy_target)}."
    )
    return (
        f"Bookings of {h.fmt_musd(booked)} are {h.fmt_musd(abs(gap))} {position} plan pace of "
        f"{h.fmt_musd(pace)}; {tail}"
    )


def exe_07(ctx: QueryContext) -> MetricResult:
    c = runway_components(ctx)
    quarters = h.fiscal_quarters(c["fy"])
    ts = target_slice(ctx, quarters)
    fy_start, fy_end = date(c["fy"], 1, 1), date(c["fy"], 12, 31)
    fy_target = ts.total() if ts.available else None
    pace = h.plan_pace(ts.by_quarter, fy_start, fy_end, ctx.today) if ts.available else None
    attainment = h.ratio(c["booked"], pace)
    return _result(
        ctx,
        "EXE-07",
        "usd",
        c["booked"],
        target=fy_target,
        target_prorated=ts.prorated,
        target_basis=ts.basis,
        goal=pace,
        attainment=attainment,
        status=_status(ctx, "EXE-01", attainment),
        status_basis=(
            f"{h.fmt_pct(attainment)} of plan pace" if attainment is not None else _no_target_basis(ts)
        ),
        breakdown=[
            {"component": "booked", "label": f"Booked FY{c['fy'] % 100:02d}", "value": c["booked"]},
            {
                "component": "commit",
                "label": f"Weighted commit ({h.quarter_label(c['cq'])})",
                "value": c["commit"],
            },
            {
                "component": "best_case",
                "label": f"Weighted best case ({h.quarter_label(c['cq'])})",
                "value": c["best_case"],
            },
        ],
        narrative=runway_narrative(c["booked"], pace, c["commit"], fy_target),
        meta={
            "fy_target": fy_target,
            "plan_pace": pace,
            "booked": c["booked"],
            "commit": c["commit"],
            "best_case": c["best_case"],
            "gap_to_pace": None if pace is None else c["booked"] - pace,
            "gap_after_commit": None if fy_target is None else fy_target - c["booked"] - c["commit"],
            "current_quarter": c["cq"],
            "current_quarter_label": h.quarter_label(c["cq"]),
            "fiscal_year": c["fy"],
        },
    )


# --- EXE-08 Bookings by quarter ---------------------------------------------------------------
def exe_08(ctx: QueryContext) -> MetricResult:
    fy = ctx.today.year
    quarters = h.fiscal_quarters(fy)
    cq = h.quarter_key(ctx.today)
    bookings = _per_quarter(ctx, WON, SUM_TCV, "close_date", quarters)
    ts = target_slice(ctx, quarters)
    rows = []
    for q in quarters:
        target = ts.by_quarter.get(q) if ts.available else None
        is_future = q > cq
        value = 0.0 if is_future else (bookings[q] or 0.0)
        met = None if is_future or target is None else value >= target
        if q == cq and not met:
            met = None  # quarter still in progress: not yet missed
        rows.append(
            {
                "quarter": q,
                "label": h.quarter_label(q) + (" QTD" if q == cq else ""),
                "bookings": value,
                "target": target,
                "met": met,
                "is_current": q == cq,
                "is_future": is_future,
            }
        )
    total = sum(r["bookings"] for r in rows)
    return _result(
        ctx,
        "EXE-08",
        "usd",
        total,
        target=ts.total() if ts.available else None,
        target_prorated=ts.prorated,
        target_basis=ts.basis,
        breakdown=rows,
        meta={"fiscal_year": fy, "current_quarter": cq, "quarters_met": sum(1 for r in rows if r["met"])},
    )


# --- EXE-09 Open pipeline by vertical ---------------------------------------------------------
def exe_09(ctx: QueryContext) -> MetricResult:
    rows = ctx.rows(
        ctx.where(OPEN),
        select=f"""o.vertical,
        coalesce(sum(o.tcv_usd) FILTER (WHERE {QUALIFIED}), 0) AS qualified,
        coalesce(sum(o.tcv_usd) FILTER (WHERE o.stage = 'Identify'), 0) AS identify""",
        tail="GROUP BY o.vertical",
    )
    by = {r["vertical"]: r for r in rows}
    order = [r["name"] for r in ctx.platform.query("SELECT name FROM dim_vertical ORDER BY sort_order")]
    order += sorted(v for v in by if v not in order)  # e.g. 'Unmapped' industries
    breakdown = []
    for v in order:
        q = float(by[v]["qualified"]) if v in by else 0.0
        i = float(by[v]["identify"]) if v in by else 0.0
        breakdown.append({"vertical": v, "qualified": q, "identify": i, "total": q + i})
    total = sum(b["total"] for b in breakdown)
    qualified = sum(b["qualified"] for b in breakdown)
    return _result(
        ctx,
        "EXE-09",
        "usd",
        total,
        breakdown=breakdown,
        meta={"qualified": qualified, "identify": total - qualified},
    )


# --- EXE-10 Deals needing attention -----------------------------------------------------------
def attention_rules(ctx: QueryContext) -> dict:
    t = threshold(ctx.platform, "EXE-10")
    return {
        "value_threshold": setting(ctx.platform, "EXE-10.value_threshold_usd", 2_000_000.0),
        "review_days": int(t["on_track"]),
        "stalled_days": int(t["watch"]),
    }


def attention_condition(ctx: QueryContext) -> tuple[str, list]:
    r = attention_rules(ctx)
    return (
        f"{OPEN} AND o.tcv_usd >= ? AND (o.days_in_stage > ? OR o.past_dated)",
        [r["value_threshold"], r["review_days"]],
    )


def flag_sql(ctx: QueryContext) -> tuple[str, list]:
    r = attention_rules(ctx)
    return (
        """CASE WHEN o.stage_group <> 'open' THEN NULL
                    WHEN o.days_in_stage > ? THEN 'Stalled'
                    WHEN o.days_in_stage > ? THEN 'Ageing'
                    WHEN o.past_dated THEN 'Past close date' END""",
        [r["stalled_days"], r["review_days"]],
    )


ROW_SELECT = """o.opportunity_id, o.name, o.account_id, o.account_name, o.vertical, o.geography,
    o.lead_practice, o.primary_platform, o.stage, o.tcv_usd, o.weighted_tcv, o.std_probability,
    o.rep_probability, o.created_date, o.close_date, o.days_in_stage, o.offering,
    o.offering_class, o.lead_source, o.partner, o.owner_name"""


def to_row(r: dict) -> OpportunityRow:
    return OpportunityRow(
        opportunity_id=r["opportunity_id"],
        name=r["name"],
        account_id=r["account_id"],
        account_name=r["account_name"],
        vertical=r["vertical"],
        geography=r["geography"],
        lead_practice=r["lead_practice"],
        primary_platform=r["primary_platform"],
        stage=r["stage"],
        tcv=float(r["tcv_usd"]),
        weighted_tcv=float(r["weighted_tcv"]),
        std_probability=float(r["std_probability"]),
        rep_probability=None if r["rep_probability"] is None else float(r["rep_probability"]),
        created_date=r["created_date"].isoformat(),
        close_date=r["close_date"].isoformat(),
        days_in_stage=r["days_in_stage"],
        offering=r["offering"],
        offering_class=r["offering_class"],
        lead_source=r["lead_source"],
        partner=r["partner"],
        owner_name=r["owner_name"],
        flag=r.get("flag"),
        crm_url=settings.crm_record_url.format(id=r["opportunity_id"]),
    )


def select_rows(
    ctx: QueryContext,
    condition: str,
    cond_args: list,
    order_by: str = "o.tcv_usd DESC",
    limit: int | None = None,
    offset: int = 0,
) -> list[OpportunityRow]:
    """Rows inside the caller's *detail* scope (RLS on outputs)."""
    flag, flag_args = flag_sql(ctx)
    where, args = ctx.where(condition, args=cond_args, detail=True)
    page = "" if limit is None else f"LIMIT {int(limit)} OFFSET {int(offset)}"
    rows = ctx.platform.query(
        f"SELECT {ROW_SELECT}, {flag} AS flag FROM mart_opportunity o WHERE {where} "
        f"ORDER BY {order_by}, o.opportunity_id {page}",
        [*flag_args, *args],
    )
    return [to_row(r) for r in rows]


def aggregated_other(ctx: QueryContext, condition: str, cond_args: list) -> AggregatedOther | None:
    """Rows that feed the aggregate but are outside the detail scope (practice-lead RLS)."""
    if not ctx.scope.has_detail_limit:
        return None
    where, args = ctx.where(condition, args=cond_args)
    detail_sql = ctx.scope.detail_sql
    r = ctx.platform.query(
        f"""SELECT count(*) AS n, coalesce(sum(o.tcv_usd), 0) AS tcv FROM mart_opportunity o
            WHERE {where} AND NOT ({detail_sql})""",
        [*args, *ctx.scope.detail_args],
    )[0]
    if not r["n"]:
        return None
    return AggregatedOther(
        count=r["n"],
        tcv=float(r["tcv"]),
        note=f"{r['n']} opportunities in other practices are included in totals "
        "but shown only in aggregate for your role.",
    )


ATTENTION_FLAGS = ("Ageing", "Stalled", "Past close date")


def flag_condition(rules: dict, flag: str) -> tuple[str, list]:
    """Predicate for one EXE-10 flag; mirrors the precedence in flag_sql (Stalled > Ageing > Past)."""
    if flag == "Stalled":
        return "o.days_in_stage > ?", [rules["stalled_days"]]
    if flag == "Ageing":
        return "o.days_in_stage > ? AND o.days_in_stage <= ?", [rules["review_days"], rules["stalled_days"]]
    if flag == "Past close date":
        return "coalesce(o.days_in_stage, 0) <= ?", [rules["review_days"]]
    raise InvalidSegment(f"EXE-10 flag must be one of {', '.join(ATTENTION_FLAGS)}")


def attention_by_vertical(ctx: QueryContext, cond: str, args: list) -> list[dict]:
    """Vertical x flag counts/TCV over the full aggregate scope (same population as the headline)."""
    where, w_args = ctx.where(cond, args=args)
    flag, flag_args = flag_sql(ctx)
    rows = ctx.platform.query(
        f"""SELECT o.vertical, {flag} AS flag, count(*) AS n, coalesce(sum(o.tcv_usd), 0) AS tcv
            FROM mart_opportunity o WHERE {where} GROUP BY 1, 2""",
        [*flag_args, *w_args],
    )
    by: dict[str, dict] = {}
    for r in rows:
        v = by.setdefault(r["vertical"], {"vertical": r["vertical"], "count": 0, "tcv": 0.0})
        v["count"] += r["n"]
        v["tcv"] += float(r["tcv"])
        v[r["flag"]] = {"count": r["n"], "tcv": float(r["tcv"])}
    for v in by.values():
        for f in ATTENTION_FLAGS:
            v.setdefault(f, {"count": 0, "tcv": 0.0})
    order = [r["name"] for r in ctx.platform.query("SELECT name FROM dim_vertical ORDER BY sort_order")]
    return sorted(
        by.values(),
        key=lambda v: (order.index(v["vertical"]) if v["vertical"] in order else len(order), v["vertical"]),
    )


def exe_10(ctx: QueryContext) -> tuple[MetricResult, list[OpportunityRow], AggregatedOther | None]:
    cond, args = attention_condition(ctx)
    rows = select_rows(ctx, cond, args, order_by="o.days_in_stage DESC NULLS LAST, o.tcv_usd DESC")
    other = aggregated_other(ctx, cond, args)
    counts = {f: sum(1 for r in rows if r.flag == f) for f in ("Ageing", "Stalled", "Past close date")}
    total_n = len(rows) + (other.count if other else 0)
    total_tcv = sum(r.tcv for r in rows) + (other.tcv if other else 0.0)
    rules = attention_rules(ctx)
    metric = _result(
        ctx,
        "EXE-10",
        "count",
        float(total_n),
        breakdown=[{"flag": k, "count": v} for k, v in counts.items()],
        status_basis=f"{total_n} open deals ≥ {h.fmt_musd(rules['value_threshold'])} over "
        f"{rules['review_days']} days in stage or past their close date, worth "
        f"{h.fmt_musd(total_tcv)}",
        meta={
            **rules,
            "total_tcv": total_tcv,
            **{k.lower().replace(" ", "_"): v for k, v in counts.items()},
            "by_vertical": attention_by_vertical(ctx, cond, args),
        },
    )
    return metric, rows, other


KPI_FUNCTIONS = (exe_01, exe_02, exe_03, exe_04, exe_05, exe_06)


# --- Drill-down conditions (FR-GEN-06) --------------------------------------------------------
class InvalidSegment(ValueError):
    pass


def drill_condition(ctx: QueryContext, metric_id: str | None, segment: str | None) -> tuple[str, list, str]:
    """(condition, args, title) behind an aggregate — the same predicate as the metric."""
    p, end = ctx.period, _actuals_end(ctx)
    cq = h.quarter_key(ctx.today)
    if metric_id is None:
        return "TRUE", [], "All opportunities"
    if metric_id in ("EXE-01", "EXE-06"):
        return f"{WON} AND o.close_date BETWEEN ? AND ?", [p.start, end], f"Closed Won, {p.label}"
    if metric_id == "EXE-02":
        nq = h.next_quarter(cq)
        return (
            f"{OPEN} AND {QUALIFIED} AND o.close_date BETWEEN ? AND ?",
            [h.quarter_bounds(cq)[0], h.quarter_bounds(nq)[1]],
            f"Qualified pipeline closing {h.quarter_label(cq)}–{h.quarter_label(nq)}",
        )
    if metric_id == "EXE-03":
        groups = {"won": "('won')", "lost": "('lost')", None: "('won', 'lost')"}
        if segment not in groups:
            raise InvalidSegment("EXE-03 segment must be won or lost")
        label = {"won": "Closed Won", "lost": "Closed Lost", None: "Won and lost"}[segment]
        return (
            f"o.stage_group IN {groups[segment]} AND o.close_date BETWEEN ? AND ?",
            [p.start, end],
            f"{label}, {p.label}",
        )
    if metric_id == "EXE-04":
        return "o.created_date BETWEEN ? AND ?", [p.start, end], f"Created in {p.label}"
    if metric_id == "EXE-05":
        if segment is None:
            return OPEN, [], "Open pipeline"
        if segment not in BUCKETS:
            raise InvalidSegment(f"EXE-05 segment must be one of {', '.join(BUCKETS)}")
        return f"{OPEN} AND o.offering_class = ?", [segment], f"Open pipeline — {segment}"
    if metric_id == "EXE-07":
        fy = ctx.today.year
        if segment == "booked":
            return (
                f"{WON} AND year(o.close_date) = ? AND o.close_date <= ?",
                [fy, ctx.today],
                f"Booked FY{fy % 100:02d}",
            )
        if segment in ("commit", "best_case"):
            stages = COMMIT if segment == "commit" else BEST_CASE
            label = "Commit" if segment == "commit" else "Best case"
            return (
                f"{OPEN} AND {stages} AND o.close_quarter = ?",
                [cq],
                f"{label} closing {h.quarter_label(cq)} (weighted)",
            )
        raise InvalidSegment("EXE-07 segment must be booked, commit or best_case")
    if metric_id == "EXE-08":
        if segment is None:
            return f"{WON} AND year(o.close_date) = ?", [ctx.today.year], "Bookings this FY"
        if segment not in h.fiscal_quarters(ctx.today.year):
            raise InvalidSegment("EXE-08 segment must be a quarter of the current FY, e.g. 2026-Q2")
        return (
            f"{WON} AND o.close_quarter = ? AND o.close_date <= ?",
            [segment, ctx.today],
            f"Bookings {h.quarter_label(segment)}",
        )
    if metric_id == "EXE-09":
        if not segment:
            return OPEN, [], "Open pipeline"
        vertical, _, part = segment.partition("|")
        part_sql = {"qualified": QUALIFIED, "identify": "o.stage = 'Identify'", "": "TRUE"}
        if part not in part_sql:
            raise InvalidSegment("EXE-09 segment must be '<vertical>|qualified' or '<vertical>|identify'")
        label = {"qualified": "qualified", "identify": "Identify", "": "all stages"}[part]
        return (
            f"{OPEN} AND o.vertical = ? AND {part_sql[part]}",
            [vertical],
            f"Open pipeline — {vertical} ({label})",
        )
    if metric_id == "EXE-10":
        cond, args = attention_condition(ctx)
        if not segment:
            return cond, args, "Deals needing attention"
        vertical, sep, flag = segment.partition("|")
        if not sep:
            vertical, flag = "", segment
        extra, extra_args = flag_condition(attention_rules(ctx), flag)
        cond, args = f"{cond} AND {extra}", [*args, *extra_args]
        title = f"Deals needing attention — {flag}"
        if vertical:
            cond, args, title = f"{cond} AND o.vertical = ?", [*args, vertical], f"{title} ({vertical})"
        return cond, args, title
    raise InvalidSegment(f"No drill-down defined for {metric_id}")
