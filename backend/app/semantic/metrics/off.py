"""Offerings metrics OFF-01 … OFF-05 (Offerings plan §2).

OFF-01..03 are opportunity metrics and go through QueryContext.where (global filters + RLS).
OFF-04 and OFF-05 are asset-library metrics: the asset facts carry no deal data, so row-level
security does not narrow them (the module itself is closed to Client partners and Marketing).
Practice, platform and vertical filters apply to the asset library; cross-industry assets appear
under every vertical.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.schemas.common import MetricResult
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import SUM_TCV, _result, _status
from app.semantic.status import setting, threshold

BUCKET = "CASE WHEN o.offering_class = 'Untagged' THEN 'Untagged' ELSE o.offering END"
CROSS_INDUSTRY = "Cross-industry"
TOP_UNVALIDATED = 5
REUSE_WINDOW_DAYS = 365


def _end(ctx: QueryContext) -> date:
    return min(ctx.period.end, ctx.today)


# --- OFF-01 Pipeline and wins by offering -----------------------------------------------------
def off_01(ctx: QueryContext) -> MetricResult:
    open_rows = ctx.rows(
        ctx.where("o.stage_group = 'open'"),
        select=f"{BUCKET} AS bucket, count(*) AS n, {SUM_TCV} AS tcv",
        tail="GROUP BY 1",
    )
    won_rows = ctx.rows(
        ctx.where(
            "o.stage_group = 'won'", "o.close_date BETWEEN ? AND ?", args=[ctx.period.start, _end(ctx)]
        ),
        select=f"{BUCKET} AS bucket, count(*) AS n, {SUM_TCV} AS tcv",
        tail="GROUP BY 1",
    )
    merged: dict[str, dict] = {}
    for kind, rows in (("open", open_rows), ("won", won_rows)):
        for r in rows:
            b = merged.setdefault(
                r["bucket"],
                {"offering": r["bucket"], "open_tcv": 0.0, "open_count": 0, "won_tcv": 0.0, "won_count": 0},
            )
            b[f"{kind}_tcv"], b[f"{kind}_count"] = float(r["tcv"]), int(r["n"])
    for b in merged.values():
        b["kind"] = {"Untagged": "untagged", "Capability-led": "capability"}.get(b["offering"], "offering")
        b["total_tcv"] = b["open_tcv"] + b["won_tcv"]
    order = {"offering": 0, "capability": 1, "untagged": 2}
    breakdown = sorted(merged.values(), key=lambda b: (order[b["kind"]], -b["total_tcv"]))
    total = sum(b["total_tcv"] for b in breakdown)
    led = sum(b["total_tcv"] for b in breakdown if b["kind"] == "offering")
    untagged = sum(b["total_tcv"] for b in breakdown if b["kind"] == "untagged")
    share = h.ratio(led, total)
    return _result(
        ctx,
        "OFF-01",
        "pct",
        share,
        status_basis=f"{h.fmt_pct(share)} of open and won TCV is offering-led; "
        f"{h.fmt_musd(untagged)} is untagged ({ctx.period.label})",
        breakdown=breakdown,
        meta={"total_tcv": total, "offering_led_tcv": led, "untagged_tcv": untagged},
    )


# --- OFF-02 Attach rate and practices per deal ------------------------------------------------
def off_02(ctx: QueryContext) -> MetricResult:
    where, args = ctx.where(
        "o.stage_group = 'won'", "o.close_date BETWEEN ? AND ?", args=[ctx.period.start, _end(ctx)]
    )
    rows = ctx.platform.query(
        f"""SELECT n, count(*) AS deals, coalesce(sum(tcv), 0) AS tcv FROM (
                SELECT o.opportunity_id, count(b.practice) AS n, any_value(o.tcv_usd) AS tcv
                FROM mart_opportunity o
                LEFT JOIN bridge_opportunity_practice b ON b.opportunity_id = o.opportunity_id
                WHERE {where} GROUP BY o.opportunity_id) GROUP BY n ORDER BY n""",
        args,
    )
    deals = sum(int(r["deals"]) for r in rows)
    multi = sum(int(r["deals"]) for r in rows if int(r["n"]) >= 2)
    rate = h.ratio(multi, deals)
    mean = h.ratio(sum(int(r["n"]) * int(r["deals"]) for r in rows), deals)
    breakdown = [
        {
            "practices": int(r["n"]),
            "label": f"{int(r['n'])} practice{'s' if int(r['n']) != 1 else ''}",
            "deals": int(r["deals"]),
            "tcv": float(r["tcv"]),
            "share": h.ratio(int(r["deals"]), deals),
        }
        for r in rows
    ]
    goal = threshold(ctx.platform, "OFF-02")["on_track"]
    return _result(
        ctx,
        "OFF-02",
        "pct",
        rate,
        goal=goal,
        status=_status(ctx, "OFF-02", rate),
        status_basis=f"{multi} of {deals} won deals include more than one practice ({ctx.period.label})",
        breakdown=breakdown,
        meta={"deals": deals, "multi_practice": multi, "mean_practices": mean},
    )


# --- OFF-03 AI-led validation split -----------------------------------------------------------
VALIDATION_JOIN = (
    "mart_opportunity o LEFT JOIN fact_validation v "
    "ON v.validation_id = o.validation_id AND v.opportunity_id = o.opportunity_id"
)
STATE_SQL = (
    "CASE WHEN NOT o.ai_led THEN 'not_ai_led' WHEN v.status = 'Validated' THEN 'validated' "
    "ELSE 'unvalidated' END"
)
STATE_LABELS = {
    "validated": "AI-led, validated",
    "unvalidated": "AI-led, not validated",
    "not_ai_led": "Not AI-led",
}


def off_03(ctx: QueryContext) -> MetricResult:
    where, args = ctx.where("o.stage_group = 'open'")
    rows = ctx.platform.query(
        f"SELECT {STATE_SQL} AS state, count(*) AS n, {SUM_TCV} AS tcv FROM {VALIDATION_JOIN} "
        f"WHERE {where} GROUP BY 1",
        args,
    )
    by = {r["state"]: r for r in rows}
    total = sum(float(r["tcv"]) for r in rows)
    breakdown = []
    for state, label in STATE_LABELS.items():
        r = by.get(state)
        tcv = float(r["tcv"]) if r else 0.0
        breakdown.append(
            {
                "state": state,
                "label": label,
                "count": int(r["n"]) if r else 0,
                "tcv": tcv,
                "share": h.ratio(tcv, total),
            }
        )
    unv = next(b for b in breakdown if b["state"] == "unvalidated")
    d_where, d_args = ctx.where("o.stage_group = 'open'", f"{STATE_SQL} = 'unvalidated'", detail=True)
    largest = ctx.platform.query(
        f"""SELECT o.opportunity_id, o.name, o.account_name, o.stage, o.tcv_usd,
                   coalesce(v.status, CASE WHEN coalesce(o.validation_id, '') = '' THEN 'No validation ID'
                                           ELSE 'Not in register' END) AS validation
            FROM {VALIDATION_JOIN} WHERE {d_where} ORDER BY o.tcv_usd DESC LIMIT {TOP_UNVALIDATED}""",
        d_args,
    )
    callout = (
        f"{h.fmt_musd(unv['tcv'])} of open pipeline across {unv['count']} AI-led deals has no "
        "completed validation."
        if unv["count"]
        else None
    )
    return _result(
        ctx,
        "OFF-03",
        "usd",
        unv["tcv"],
        status_basis=f"Open pipeline of {h.fmt_musd(total)} split by AI validation state",
        breakdown=breakdown,
        narrative=callout,
        meta={
            "total_tcv": total,
            "largest_unvalidated": [{**r, "tcv_usd": float(r["tcv_usd"])} for r in largest],
            "detail_limited": ctx.scope.has_detail_limit,
        },
    )


# --- Asset library helpers --------------------------------------------------------------------
def _asset_filter(ctx: QueryContext, alias: str) -> tuple[str, list]:
    conds, args = [], []
    for name in ("practice", "platform"):
        values = getattr(ctx.params, name)
        if values:
            conds.append(f"{alias}.{name} IN ({', '.join('?' * len(values))})")
            args.extend(values)
    if ctx.params.vertical:
        marks = ", ".join("?" * len(ctx.params.vertical))
        conds.append(f"({alias}.vertical IN ({marks}) OR {alias}.vertical = '{CROSS_INDUSTRY}')")
        args.extend(ctx.params.vertical)
    return (" AND ".join(conds) or "TRUE"), args


def _filtered(ctx: QueryContext) -> bool:
    p = ctx.params
    return bool(p.practice or p.platform or p.vertical)


# --- OFF-04 Asset reuse -----------------------------------------------------------------------
def off_04(ctx: QueryContext) -> MetricResult:
    low = int(setting(ctx.platform, "OFF-04.low_reuse_uses", 8))
    stale = int(setting(ctx.platform, "OFF-04.refresh_due_days", 180))
    cond, fargs = _asset_filter(ctx, "a")
    since = ctx.today - timedelta(days=REUSE_WINDOW_DAYS)
    rows = ctx.platform.query(
        f"""SELECT a.asset_id, a.title, a.asset_type, a.offering, a.practice, a.last_refreshed,
                   count(u.asset_id) FILTER (WHERE u.used_on > ?) AS uses
            FROM fact_asset a LEFT JOIN fact_asset_usage u ON u.asset_id = a.asset_id
            WHERE {cond} GROUP BY ALL ORDER BY uses DESC, a.asset_id""",
        [since, *fargs],
    )
    breakdown = []
    for r in rows:
        age = (ctx.today - r["last_refreshed"]).days
        uses = int(r["uses"])
        breakdown.append(
            {
                "asset_id": r["asset_id"],
                "title": r["title"],
                "asset_type": r["asset_type"],
                "offering": r["offering"],
                "practice": r["practice"],
                "uses": uses,
                "days_since_refresh": age,
                "low_reuse": uses < low,
                "refresh_due": age > stale,
            }
        )
    flagged = sum(1 for b in breakdown if b["low_reuse"] or b["refresh_due"])
    return _result(
        ctx,
        "OFF-04",
        "count",
        float(flagged),
        status_basis=f"{flagged} of {len(breakdown)} assets are low reuse (<{low} uses in 12 months) "
        f"or refresh due (>{stale} days)",
        breakdown=breakdown,
        meta={
            "assets": len(breakdown),
            "low_reuse": sum(1 for b in breakdown if b["low_reuse"]),
            "refresh_due": sum(1 for b in breakdown if b["refresh_due"]),
            "low_reuse_uses": low,
            "refresh_due_days": stale,
            "total_uses": sum(b["uses"] for b in breakdown),
        },
    )


# --- OFF-05 Demos, accelerators and solutions developed ---------------------------------------
def off_05(ctx: QueryContext) -> MetricResult:
    fy = ctx.today.year
    cond, fargs = _asset_filter(ctx, "b")
    builds = ctx.platform.query(
        f"""SELECT b.build_id, b.asset_id, b.asset_type, b.status, b.target_quarter, b.complete,
                   b.build_weeks, b.released_date
            FROM fact_asset_build b WHERE {cond}""",
        fargs,
    )
    total_builds = ctx.platform.scalar("SELECT count(*) FROM fact_asset_build")
    plan = {
        r["quarter_key"]: float(r["planned_releases"])
        for r in ctx.platform.query(
            "SELECT quarter_key, planned_releases FROM dim_build_plan WHERE fiscal_year = ?", [fy]
        )
    }
    prorated = _filtered(ctx)
    scale = h.ratio(len(builds), total_builds) if prorated else 1.0
    scale = scale or 0.0
    plan = {q: v * scale for q, v in plan.items()}
    pace = h.plan_pace(plan, date(fy, 1, 1), date(fy, 12, 31), ctx.today)
    released_all = [b for b in builds if b["status"] == "Released"]
    released = [b for b in released_all if b["complete"]]
    excluded = len(released_all) - len(released)
    used = {
        r["asset_id"]
        for r in ctx.platform.query(
            "SELECT DISTINCT asset_id FROM fact_asset_usage WHERE used_on >= ?", [date(fy, 1, 1)]
        )
    }
    reused = sum(1 for b in released if b["asset_id"] in used)
    reuse = h.ratio(reused, len(released))
    weeks = [float(b["build_weeks"]) for b in released if b["build_weeks"] is not None]
    mean_weeks = sum(weeks) / len(weeks) if weeks else None
    attainment = h.ratio(len(released), pace)
    current = h.quarter_key(ctx.today)
    breakdown = []
    for q in h.fiscal_quarters(fy):
        in_q = [b for b in builds if b["target_quarter"] == q]
        breakdown.append(
            {
                "quarter": q,
                "label": h.quarter_label(q),
                "planned": plan.get(q, 0.0),
                "released": sum(1 for b in released if b["target_quarter"] == q),
                "in_development": sum(1 for b in in_q if b["status"] == "In development"),
                "planned_items": sum(1 for b in in_q if b["status"] == "Planned"),
                "partial": q == current,
            }
        )
    by_type = {}
    for b in released:
        by_type[b["asset_type"]] = by_type.get(b["asset_type"], 0) + 1
    reuse_t = threshold(ctx.platform, "OFF-05-REUSE")
    return _result(
        ctx,
        "OFF-05",
        "count",
        float(len(released)),
        goal=pace,
        attainment=attainment,
        status=_status(ctx, "OFF-05", attainment),
        status_basis=f"{len(released)} released against a plan pace of {pace:.1f}"
        + (" (plan pro-rated to the filtered asset share)" if prorated else ""),
        target_prorated=prorated,
        target_basis="Build plan pro-rated by the filtered share of build items" if prorated else None,
        breakdown=breakdown,
        meta={
            "released": len(released),
            "in_development": sum(1 for b in builds if b["status"] == "In development"),
            "plan_pace": pace,
            "annual_plan": sum(plan.values()),
            "reuse_share": reuse,
            "reuse_status": _status(ctx, "OFF-05-REUSE", reuse),
            "reuse_goal": reuse_t["on_track"],
            "reused": reused,
            "mean_build_weeks": mean_weeks,
            "excluded_incomplete": excluded,
            "released_by_type": by_type,
        },
    )


FUNCTIONS = {"OFF-01": off_01, "OFF-02": off_02, "OFF-03": off_03, "OFF-04": off_04, "OFF-05": off_05}
