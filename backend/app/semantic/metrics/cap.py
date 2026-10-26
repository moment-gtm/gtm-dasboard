"""Solutions Capacity metrics CAP-01 … CAP-04 (Solutions Capacity plan §2).

Same contract as the other metric modules: one function per metric ID returning a MetricResult,
every query built through QueryContext.where (global filters + RLS), drill-down predicates that
reuse the metric's own conditions.

CAP-03 (cost of sale) is restricted to GTM Lead, Leadership and Finance. The route gates and audits
it, and it is deliberately absent from `FUNCTIONS` so the generic widget export cannot reach it —
the export route calls it through the same restricted gate.
"""

from __future__ import annotations

from app.data.capacity_data import ARCHITECT_ROLE
from app.domain.enums import Stage
from app.schemas.common import MetricResult
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import InvalidSegment, _result, _status
from app.semantic.metrics.pur import DECIDED, _quarters
from app.semantic.status import band, threshold

ARCHITECT_STAGES = (Stage.QUALIFY.value, Stage.PROPOSE.value, Stage.ORALS.value)
STAGE_MARKS = ", ".join("?" * len(ARCHITECT_STAGES))
TEAM_JOIN = (
    "fact_opportunity_team t JOIN mart_opportunity o ON o.opportunity_id = t.opportunity_id "
    "JOIN dim_resource r ON r.resource_id = t.resource_id"
)
PURSUIT_JOIN = "fact_pursuit p JOIN mart_opportunity o ON o.opportunity_id = p.opportunity_id"
EFFORT_JOIN = "fact_pursuit_effort e JOIN mart_opportunity o ON o.opportunity_id = e.opportunity_id"
QUALITY_JOIN = "fact_bid_quality b JOIN mart_opportunity o ON o.opportunity_id = b.opportunity_id"
SUBMITTED_QUARTER = "printf('%d-Q%d', year(p.rfp_submitted), quarter(p.rfp_submitted))"
TREND_QUARTERS = 4
OUTCOMES = ("won", "lost")
SCORES = (1, 2, 3, 4, 5)


def _load_band(ctx: QueryContext, load: int) -> str:
    s = band(ctx.platform, "CAP-01", load)
    return s.value if s else "on_track"


# --- CAP-01 Architect load --------------------------------------------------------------------
def cap_01(ctx: QueryContext) -> MetricResult:
    where, args = ctx.where(
        "t.role = ?", f"o.stage IN ({STAGE_MARKS})", args=[ARCHITECT_ROLE, *ARCHITECT_STAGES]
    )
    rows = ctx.platform.query(
        f"""SELECT r.resource_id, r.name, count(*) AS open_pursuits, coalesce(sum(o.tcv_usd), 0) AS tcv
            FROM {TEAM_JOIN} WHERE {where}
            GROUP BY r.resource_id, r.name ORDER BY open_pursuits DESC, r.name""",
        args,
    )
    t = threshold(ctx.platform, "CAP-01")
    breakdown = [
        {
            "resource_id": r["resource_id"],
            "architect": r["name"],
            "open_pursuits": int(r["open_pursuits"]),
            "tcv": float(r["tcv"]),
            "band": _load_band(ctx, int(r["open_pursuits"])),
        }
        for r in rows
    ]
    over = [r for r in breakdown if r["band"] == "off_track"]
    stretched = [r for r in breakdown if r["band"] == "watch"]
    healthy = len(breakdown) - len(over) - len(stretched)
    if over:
        callout = (
            f"{len(over)} architect{'s are' if len(over) > 1 else ' is'} over capacity: "
            + ", ".join(f"{r['architect']} ({r['open_pursuits']})" for r in over)
            + f". Healthy load is up to {int(t['on_track'])} open pursuits."
        )
    else:
        callout = "No architect is over capacity."
    peak = breakdown[0]["open_pursuits"] if breakdown else None
    return _result(
        ctx,
        "CAP-01",
        "count",
        len(over),
        goal=0,
        status=_status(ctx, "CAP-01", peak),
        status_basis=f"{len(breakdown)} architects hold open Qualify, Propose or Orals pursuits; "
        f"the busiest holds {peak if peak is not None else 0}",
        breakdown=breakdown,
        narrative=callout,
        meta={
            "healthy": healthy,
            "stretched": len(stretched),
            "over_capacity": len(over),
            "architects": len(breakdown),
            "healthy_max": int(t["on_track"]),
            "stretched_at": int(t["watch"]),
            "callout": callout,
        },
    )


# --- CAP-02 RFP turnaround and SLA ------------------------------------------------------------
def cap_02(ctx: QueryContext) -> MetricResult:
    quarters, marks, qargs = _quarters(ctx, TREND_QUARTERS)
    where, args = ctx.where(
        "p.rfp_submitted IS NOT NULL",
        "p.rfp_submitted <= ?",
        f"{SUBMITTED_QUARTER} IN ({marks})",
        args=[ctx.today, *qargs[:-1]],
    )
    rows = ctx.platform.query(
        f"""SELECT {SUBMITTED_QUARTER} AS q, count(*) AS submitted,
                   count(*) FILTER (WHERE p.submitted_on_time) AS on_time,
                   avg(date_diff('day', p.rfp_received, p.rfp_submitted)) AS avg_days,
                   avg(p.sla_target_days) AS avg_sla
            FROM {PURSUIT_JOIN} WHERE {where} GROUP BY 1""",
        args,
    )
    by = {r["q"]: r for r in rows}
    current = h.quarter_key(ctx.today)
    breakdown = []
    for q in quarters:
        r = by.get(q)
        submitted, on_time = (int(r["submitted"]), int(r["on_time"])) if r else (0, 0)
        breakdown.append(
            {
                "quarter": q,
                "label": h.quarter_label(q),
                "submitted": submitted,
                "on_time": on_time,
                "sla_share": h.ratio(on_time, submitted),
                "avg_days": float(r["avg_days"]) if r else None,
                "avg_sla_days": float(r["avg_sla"]) if r else None,
                "partial": q == current,
            }
        )
    submitted = sum(r["submitted"] for r in breakdown)
    on_time = sum(r["on_time"] for r in breakdown)
    share = h.ratio(on_time, submitted)
    days = sum((r["avg_days"] or 0) * r["submitted"] for r in breakdown)
    goal = threshold(ctx.platform, "CAP-02")["on_track"]
    return _result(
        ctx,
        "CAP-02",
        "pct",
        share,
        goal=goal,
        status=_status(ctx, "CAP-02", share),
        status_basis=f"{on_time} of {submitted} proposals submitted inside the RFP's SLA "
        f"over the last {TREND_QUARTERS} quarters",
        breakdown=breakdown,
        meta={
            "submitted": submitted,
            "on_time": on_time,
            "avg_days": days / submitted if submitted else None,
        },
    )


# --- CAP-03 Cost of sale (restricted) ---------------------------------------------------------
def cap_03(ctx: QueryContext) -> MetricResult:
    quarters, marks, qargs = _quarters(ctx, TREND_QUARTERS)
    where, args = ctx.where(DECIDED, f"o.close_quarter IN ({marks})", "o.close_date <= ?", args=qargs)
    rows = ctx.platform.query(
        f"""SELECT o.close_quarter AS q, count(*) AS pursuits, sum(e.hours) AS hours,
                   sum(e.cost_usd) AS cost, sum(o.tcv_usd) AS tcv
            FROM {EFFORT_JOIN} WHERE {where} GROUP BY o.close_quarter""",
        args,
    )
    by = {r["q"]: r for r in rows}
    current = h.quarter_key(ctx.today)
    breakdown = []
    for q in quarters:
        r = by.get(q)
        cost, tcv = (float(r["cost"]), float(r["tcv"])) if r else (0.0, 0.0)
        breakdown.append(
            {
                "quarter": q,
                "label": h.quarter_label(q),
                "pursuits": int(r["pursuits"]) if r else 0,
                "hours": float(r["hours"]) if r else 0.0,
                "cost": cost,
                "tcv": tcv,
                "cost_of_sale": h.ratio(cost, tcv),
                "partial": q == current,
            }
        )
    cost, tcv = sum(r["cost"] for r in breakdown), sum(r["tcv"] for r in breakdown)
    value = h.ratio(cost, tcv)
    goal = threshold(ctx.platform, "CAP-03")["on_track"]
    return _result(
        ctx,
        "CAP-03",
        "pct",
        value,
        goal=goal,
        status=_status(ctx, "CAP-03", value),
        status_basis=f"${cost / 1e6:.1f}M of pursuit effort on ${tcv / 1e6:.1f}M of TCV "
        f"over the last {TREND_QUARTERS} quarters",
        breakdown=breakdown,
        meta={"cost": cost, "tcv": tcv, "restricted": True},
    )


# --- CAP-04 Proposal quality score ------------------------------------------------------------
def cap_04(ctx: QueryContext) -> MetricResult:
    _, marks, qargs = _quarters(ctx, TREND_QUARTERS)
    where, args = ctx.where(DECIDED, f"o.close_quarter IN ({marks})", "o.close_date <= ?", args=qargs)
    score_cols = ", ".join(f"count(*) FILTER (WHERE round(b.quality_score) = {s}) AS s{s}" for s in SCORES)
    rows = ctx.platform.query(
        f"""SELECT o.stage_group AS outcome, count(*) AS n, avg(b.quality_score) AS avg_score,
                   {score_cols}
            FROM {QUALITY_JOIN} WHERE {where} GROUP BY o.stage_group""",
        args,
    )
    by = {r["outcome"]: r for r in rows}
    breakdown = [
        {
            "outcome": o,
            "label": "Won" if o == "won" else "Lost",
            "count": int(by[o]["n"]) if o in by else 0,
            "avg_score": float(by[o]["avg_score"]) if o in by else None,
            "distribution": [{"score": s, "count": int(by[o][f"s{s}"]) if o in by else 0} for s in SCORES],
        }
        for o in OUTCOMES
    ]
    won, lost = breakdown[0]["avg_score"], breakdown[1]["avg_score"]
    gap = None if won is None or lost is None else won - lost
    return _result(
        ctx,
        "CAP-04",
        "count",
        won,
        status_basis=(
            f"Won proposals average {won:.1f} against {lost:.1f} for lost ({gap:+.1f}) over the last "
            f"{TREND_QUARTERS} quarters"
            if gap is not None
            else "No reviewed pursuits in the last four quarters"
        ),
        breakdown=breakdown,
        meta={"won_avg": won, "lost_avg": lost, "gap": gap, "max_score": 5},
    )


FUNCTIONS = {"CAP-01": cap_01, "CAP-02": cap_02, "CAP-04": cap_04}
RESTRICTED_FUNCTIONS = {"CAP-03": cap_03}


# --- Drill-down conditions (FR-GEN-06) --------------------------------------------------------
def drill_condition(ctx: QueryContext, metric_id: str, segment: str | None) -> tuple[str, list, str]:
    head, _, part = (segment or "").partition("|")
    quarters = h.last_n_quarters(ctx.today, TREND_QUARTERS)
    if metric_id == "CAP-01":
        name = ctx.platform.scalar("SELECT name FROM dim_resource WHERE resource_id = ?", [head])
        if name is None:
            raise InvalidSegment("CAP-01 segment must be an architect resource id, e.g. RES-A001")
        return (
            f"o.stage IN ({STAGE_MARKS}) AND o.opportunity_id IN (SELECT t.opportunity_id FROM "
            "fact_opportunity_team t WHERE t.resource_id = ? AND t.role = ?)",
            [*ARCHITECT_STAGES, head, ARCHITECT_ROLE],
            f"Open pursuits — {name}",
        )
    if metric_id == "CAP-02":
        if head not in quarters:
            raise InvalidSegment(f"CAP-02 segment must be '<quarter>[|late]', e.g. {quarters[-1]}")
        late = "AND p.submitted_on_time = FALSE" if part == "late" else ""
        return (
            f"o.opportunity_id IN (SELECT p.opportunity_id FROM fact_pursuit p WHERE "
            f"p.rfp_submitted IS NOT NULL AND {SUBMITTED_QUARTER} = ? {late})",
            [head],
            f"{h.quarter_label(head)} — {'late ' if late else ''}submissions",
        )
    if metric_id == "CAP-03":
        if head not in quarters:
            raise InvalidSegment(f"CAP-03 segment must be a quarter, e.g. {quarters[-1]}")
        return (
            f"{DECIDED} AND o.close_quarter = ? AND o.close_date <= ? AND o.opportunity_id IN "
            "(SELECT e.opportunity_id FROM fact_pursuit_effort e)",
            [head, ctx.today],
            f"{h.quarter_label(head)} — pursuits with recorded effort",
        )
    if metric_id == "CAP-04":
        if head not in OUTCOMES:
            raise InvalidSegment("CAP-04 segment must be won or lost")
        _, marks, qargs = _quarters(ctx, TREND_QUARTERS)
        return (
            f"o.stage_group = '{head}' AND o.close_quarter IN ({marks}) AND o.close_date <= ? AND "
            "o.opportunity_id IN (SELECT b.opportunity_id FROM fact_bid_quality b)",
            qargs,
            f"Reviewed pursuits — {head}",
        )
    raise InvalidSegment(f"No drill-down defined for {metric_id}")
