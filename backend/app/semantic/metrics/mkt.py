"""Market Signals metrics MKT-01 … MKT-04 (RSD §5.7, FR-MKT-01..04).

- MKT-01: Thought leadership volume & reach (POVs published per quarter + downloads & engaged visits, SRC-11).
- MKT-02: Discovery workshop conversion funnel (Workshops held -> Opps created <=90d -> Qualified -> Won,
  conversion rate vs 50% target, and pipeline originated, SRC-01).
- MKT-03: Campaign-sourced pipeline (TCV created in period where campaign is primary source, by campaign
  and quarter, reconciled between SRC-01 CRM and SRC-10 Marketing Automation within 0.5%).
- MKT-04: Analyst positioning (Forrester Wave, Gartner MQ, IDC MarketScape, Everest PEAK Matrix
  with current placement, prior placement, and direction icon + text, SRC-15).
"""

from __future__ import annotations

from datetime import date

from app.domain.enums import Stage
from app.schemas.common import MetricResult
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import SUM_TCV, InvalidSegment, _result, _status
from app.semantic.status import threshold

TL_QUARTERS = 4
CAMPAIGN_TREND_QUARTERS = 4
UNQUALIFIED_STAGES = (Stage.IDENTIFY.value, Stage.NO_BID.value, Stage.CLIENT_CANCELLED.value)
UNQUAL_MARKS = ", ".join("?" * len(UNQUALIFIED_STAGES))

DIRECTION_MAP = {
    "Improved": ("up", "↑", "Improved"),
    "up": ("up", "↑", "Improved"),
    "Maintained": ("flat", "→", "Unchanged"),
    "Unchanged": ("flat", "→", "Unchanged"),
    "flat": ("flat", "→", "Unchanged"),
    "Declined": ("down", "↓", "Declined"),
    "down": ("down", "↓", "Declined"),
}


def _end(ctx: QueryContext) -> date:
    return min(ctx.period.end, ctx.today)


def _practice_platform_filter(ctx: QueryContext, alias: str) -> tuple[str, list]:
    conds, args = [], []
    if ctx.params.practice:
        marks = ", ".join("?" * len(ctx.params.practice))
        conds.append(f"{alias}.practice IN ({marks})")
        args.extend(ctx.params.practice)
    if ctx.params.platform:
        marks = ", ".join("?" * len(ctx.params.platform))
        conds.append(f"{alias}.platform IN ({marks})")
        args.extend(ctx.params.platform)
    return (" AND ".join(conds) or "TRUE"), args


# --- MKT-01 Thought leadership volume & reach -------------------------------------------------
def mkt_01(ctx: QueryContext) -> MetricResult:
    quarters = h.last_n_quarters(ctx.today, TL_QUARTERS)
    qmarks = ", ".join("?" * len(quarters))
    dim_cond, dim_args = _practice_platform_filter(ctx, "c")
    rows = ctx.platform.query(
        f"""SELECT c.published_quarter AS q,
                   count(*) AS povs,
                   coalesce(sum(c.downloads), 0) AS downloads,
                   coalesce(sum(c.engaged_visits), 0) AS engaged_visits,
                   avg(c.avg_dwell_seconds) AS avg_dwell,
                   coalesce(sum(c.social_shares), 0) AS social_shares
            FROM fact_content_engagement c
            WHERE c.published_quarter IN ({qmarks}) AND c.published_date <= ? AND ({dim_cond})
            GROUP BY c.published_quarter""",
        [*quarters, ctx.today, *dim_args],
    )
    by_q = {r["q"]: r for r in rows}
    current_q = h.quarter_key(ctx.today)
    breakdown = []
    for q in quarters:
        r = by_q.get(q)
        povs_count = int(r["povs"]) if r else 0
        breakdown.append(
            {
                "quarter": q,
                "label": h.quarter_label(q),
                "povs": povs_count,
                "povs_published": povs_count,
                "downloads": int(r["downloads"]) if r else 0,
                "engaged_visits": int(r["engaged_visits"]) if r else 0,
                "avg_dwell_seconds": (
                    round(float(r["avg_dwell"]), 1) if r and r["avg_dwell"] is not None else 0.0
                ),
                "social_shares": int(r["social_shares"]) if r else 0,
                "partial": q == current_q,
            }
        )

    asset_rows = ctx.platform.query(
        f"""SELECT c.asset_id, c.title, c.asset_type, c.practice, c.platform,
                   c.published_date, c.published_quarter, c.downloads, c.engaged_visits,
                   c.avg_dwell_seconds, c.social_shares
            FROM fact_content_engagement c
            WHERE c.published_quarter IN ({qmarks}) AND c.published_date <= ? AND ({dim_cond})
            ORDER BY c.published_date DESC, c.asset_id""",
        [*quarters, ctx.today, *dim_args],
    )
    recent_assets = [
        {
            "asset_id": r["asset_id"],
            "title": r["title"],
            "asset_type": r["asset_type"],
            "practice": r["practice"],
            "platform": r["platform"],
            "published_date": r["published_date"].isoformat(),
            "published_quarter": r["published_quarter"],
            "downloads": int(r["downloads"]),
            "engaged_visits": int(r["engaged_visits"]),
            "avg_dwell_seconds": int(r["avg_dwell_seconds"]),
            "social_shares": int(r["social_shares"]),
        }
        for r in asset_rows
    ]

    total_povs = sum(b["povs_published"] for b in breakdown)
    total_downloads = sum(b["downloads"] for b in breakdown)
    total_visits = sum(b["engaged_visits"] for b in breakdown)
    return _result(
        ctx,
        "MKT-01",
        "count",
        float(total_povs),
        status_basis=f"{total_povs} POVs & thought-leadership assets published over the last "
        f"{TL_QUARTERS} quarters ({total_downloads:,} downloads; {total_visits:,} engaged visits)",
        breakdown=breakdown,
        meta={
            "total_assets": total_povs,
            "total_downloads": total_downloads,
            "total_engaged_visits": total_visits,
            "quarters": TL_QUARTERS,
            "assets": recent_assets,
            "recent_assets": recent_assets,
        },
    )


# --- MKT-02 Discovery workshop conversion -----------------------------------------------------
def mkt_02(ctx: QueryContext) -> MetricResult:
    where, args = ctx.where(
        "w.workshop_date BETWEEN ? AND ?",
        args=[ctx.period.start, _end(ctx)],
        alias="w",
    )
    row = ctx.platform.query(
        f"""SELECT count(*) AS held,
                   count(*) FILTER (WHERE w.converted_within_90d) AS created_90d,
                   count(*) FILTER (WHERE w.converted_within_90d AND w.is_qualified) AS qualified,
                   count(*) FILTER (WHERE w.converted_within_90d AND w.is_won) AS won,
                   coalesce(
                       sum(w.opportunity_tcv_usd) FILTER (WHERE w.converted_within_90d), 0
                   ) AS created_tcv,
                   coalesce(
                       sum(w.opportunity_tcv_usd)
                       FILTER (WHERE w.converted_within_90d AND w.is_qualified),
                       0,
                   ) AS qualified_tcv,
                   coalesce(
                       sum(w.opportunity_tcv_usd)
                       FILTER (WHERE w.converted_within_90d AND w.is_won),
                       0,
                   ) AS won_tcv,
                   avg(w.days_to_opportunity) FILTER (WHERE w.converted_within_90d) AS avg_days_to_opp
            FROM fact_workshop w
            WHERE {where}""",
        args,
    )[0]

    held = int(row["held"])
    created_90d = int(row["created_90d"])
    qualified = int(row["qualified"])
    won = int(row["won"])
    created_tcv = float(row["created_tcv"])
    qualified_tcv = float(row["qualified_tcv"])
    won_tcv = float(row["won_tcv"])
    avg_days = round(float(row["avg_days_to_opp"]), 1) if row["avg_days_to_opp"] is not None else None

    conv_rate = h.ratio(created_90d, held)
    qual_rate = h.ratio(qualified, held)
    goal = threshold(ctx.platform, "MKT-02")["on_track"]

    breakdown = [
        {
            "key": "workshops",
            "stage": "workshops",
            "label": "Workshops held",
            "count": held,
            "tcv": created_tcv,
            "conversion_from_start": 1.0 if held else None,
            "step_conversion": 1.0 if held else None,
        },
        {
            "key": "created",
            "stage": "created",
            "label": "Opps created (≤90d)",
            "count": created_90d,
            "tcv": created_tcv,
            "conversion_from_start": conv_rate,
            "step_conversion": conv_rate,
        },
        {
            "key": "qualified",
            "stage": "qualified",
            "label": "Qualified opps",
            "count": qualified,
            "tcv": qualified_tcv,
            "conversion_from_start": qual_rate,
            "step_conversion": h.ratio(qualified, created_90d),
        },
        {
            "key": "won",
            "stage": "won",
            "label": "Closed Won",
            "count": won,
            "tcv": won_tcv,
            "conversion_from_start": h.ratio(won, held),
            "step_conversion": h.ratio(won, qualified),
        },
    ]

    by_practice_rows = ctx.platform.query(
        f"""SELECT w.practice,
                   count(*) AS held,
                   count(*) FILTER (WHERE w.converted_within_90d) AS created_90d,
                   count(*) FILTER (WHERE w.converted_within_90d AND w.is_qualified) AS qualified,
                   count(*) FILTER (WHERE w.converted_within_90d AND w.is_won) AS won,
                   coalesce(sum(w.opportunity_tcv_usd) FILTER (WHERE w.converted_within_90d), 0) AS tcv
            FROM fact_workshop w
            WHERE {where}
            GROUP BY w.practice
            ORDER BY tcv DESC, w.practice""",
        args,
    )
    by_practice = [
        {
            "practice": r["practice"],
            "held": int(r["held"]),
            "created_90d": int(r["created_90d"]),
            "qualified": int(r["qualified"]),
            "won": int(r["won"]),
            "conversion_rate": h.ratio(int(r["created_90d"]), int(r["held"])),
            "tcv": float(r["tcv"]),
        }
        for r in by_practice_rows
    ]

    return _result(
        ctx,
        "MKT-02",
        "pct",
        conv_rate,
        goal=goal,
        status=_status(ctx, "MKT-02", conv_rate),
        status_basis=f"{created_90d} of {held} discovery workshops converted to opportunities within 90d "
        f"({h.fmt_pct(conv_rate)} vs {h.fmt_pct(goal)} goal; {qualified} qualified, {won} won), "
        f"originating {h.fmt_musd(created_tcv)} of pipeline ({ctx.period.label})",
        breakdown=breakdown,
        meta={
            "workshops_held": held,
            "opps_created_90d": created_90d,
            "qualified_count": qualified,
            "won_count": won,
            "pipeline_originated_tcv": created_tcv,
            "qualified_tcv": qualified_tcv,
            "won_tcv": won_tcv,
            "created_rate": conv_rate,
            "qualified_rate": qual_rate,
            "win_rate": h.ratio(won, held),
            "avg_days_to_opportunity": avg_days,
            "by_practice": by_practice,
        },
    )


# --- MKT-03 Campaign-sourced pipeline ---------------------------------------------------------
def mkt_03(ctx: QueryContext) -> MetricResult:
    where, args = ctx.where(
        "o.campaign_id IS NOT NULL",
        "o.created_date BETWEEN ? AND ?",
        args=[ctx.period.start, _end(ctx)],
    )
    camp_rows = ctx.platform.query(
        f"""SELECT c.campaign_id, c.campaign_name, c.channel, c.practice, c.platform,
                   c.budget_usd, c.status,
                   count(o.opportunity_id) AS deals,
                   {SUM_TCV} AS tcv,
                   count(o.opportunity_id) FILTER (WHERE o.stage_group = 'won') AS won_deals,
                   coalesce(sum(o.tcv_usd) FILTER (WHERE o.stage_group = 'won'), 0) AS won_tcv,
                   coalesce(sum(m.attributed_tcv_usd), 0) AS mktg_attributed_tcv
            FROM dim_campaign c
            LEFT JOIN mart_opportunity o
                   ON o.campaign_id = c.campaign_id AND ({where})
            LEFT JOIN fact_campaign_member m
                   ON m.opportunity_id = o.opportunity_id
                  AND m.campaign_id = c.campaign_id
                  AND m.primary_source = TRUE
            GROUP BY c.campaign_id, c.campaign_name, c.channel, c.practice, c.platform, c.budget_usd, c.status
            HAVING count(o.opportunity_id) > 0
            ORDER BY tcv DESC, c.campaign_name""",
        args,
    )

    total_tcv = sum(float(r["tcv"]) for r in camp_rows)
    total_mktg_tcv = sum(float(r["mktg_attributed_tcv"]) for r in camp_rows)
    total_deals = sum(int(r["deals"]) for r in camp_rows)
    total_won_tcv = sum(float(r["won_tcv"]) for r in camp_rows)
    variance_pct = abs(total_tcv - total_mktg_tcv) / total_tcv if total_tcv else 0.0

    by_campaign = [
        {
            "campaign_id": r["campaign_id"],
            "campaign_name": r["campaign_name"],
            "channel": r["channel"],
            "practice": r["practice"],
            "platform": r["platform"],
            "status": r["status"],
            "budget_usd": float(r["budget_usd"]),
            "deals": int(r["deals"]),
            "tcv": float(r["tcv"]),
            "won_deals": int(r["won_deals"]),
            "won_tcv": float(r["won_tcv"]),
            "mktg_attributed_tcv": float(r["mktg_attributed_tcv"]),
            "roi_multiple": h.ratio(float(r["tcv"]), float(r["budget_usd"])),
            "share": h.ratio(float(r["tcv"]), total_tcv),
        }
        for r in camp_rows
    ]

    fy = ctx.period.start.year
    quarters = [f"{fy}-Q{q}" for q in range(1, 5)]
    qmarks = ", ".join("?" * len(quarters))
    q_where, q_args = ctx.where(
        "o.campaign_id IS NOT NULL",
        f"o.created_quarter IN ({qmarks})",
        "o.created_date BETWEEN ? AND ?",
        args=[*quarters, ctx.period.start, _end(ctx)],
    )
    q_rows = ctx.platform.query(
        f"""SELECT o.created_quarter AS q,
                   count(*) AS deals,
                   {SUM_TCV} AS tcv,
                   coalesce(sum(o.tcv_usd) FILTER (WHERE o.stage_group = 'won'), 0) AS won_tcv
            FROM mart_opportunity o
            WHERE {q_where}
            GROUP BY o.created_quarter""",
        q_args,
    )
    by_q = {r["q"]: r for r in q_rows}
    current_q = h.quarter_key(ctx.today)
    by_quarter = [
        {
            "quarter": q,
            "label": h.quarter_label(q),
            "deals": int(by_q[q]["deals"]) if q in by_q else 0,
            "tcv": float(by_q[q]["tcv"]) if q in by_q else 0.0,
            "won_tcv": float(by_q[q]["won_tcv"]) if q in by_q else 0.0,
            "partial": q == current_q,
        }
        for q in quarters
    ]

    return _result(
        ctx,
        "MKT-03",
        "usd",
        total_tcv,
        status_basis=f"{h.fmt_musd(total_tcv)} of campaign-sourced pipeline across {total_deals} deals "
        f"from {len(by_campaign)} active campaigns ({ctx.period.label})",
        breakdown=by_quarter,
        meta={
            "total_tcv": total_tcv,
            "mktg_attributed_tcv": total_mktg_tcv,
            "reconciliation_variance_pct": variance_pct,
            "reconciled": variance_pct <= 0.005,
            "total_deals": total_deals,
            "won_tcv": total_won_tcv,
            "active_campaigns": len(by_campaign),
            "by_campaign": by_campaign,
            "by_quarter": by_quarter,
        },
    )


# --- MKT-04 Analyst positioning ---------------------------------------------------------------
def mkt_04(ctx: QueryContext) -> MetricResult:
    dim_cond, dim_args = _practice_platform_filter(ctx, "e")
    rows = ctx.platform.query(
        f"""SELECT e.eval_id, e.firm, e.report_series, e.report_title, e.practice, e.platform,
                   e.published_date, e.current_placement, e.prior_placement,
                   e.direction, e.direction_icon, e.score_delta, e.lead_analyst, e.summary_note
            FROM fact_analyst_eval e
            WHERE {dim_cond}
            ORDER BY e.published_date DESC, e.eval_id""",
        dim_args,
    )
    breakdown = []
    for r in rows:
        dir_key, dir_icon, dir_label = DIRECTION_MAP.get(r["direction"], ("flat", "→", "Unchanged"))
        breakdown.append(
            {
                "eval_id": r["eval_id"],
                "firm": r["firm"],
                "report_series": r["report_series"],
                "report_title": r["report_title"],
                "practice": r["practice"],
                "platform": r["platform"],
                "published_date": r["published_date"].isoformat(),
                "current_placement": r["current_placement"],
                "prior_placement": r["prior_placement"],
                "direction": dir_key,
                "direction_icon": dir_icon,
                "direction_label": dir_label,
                "direction_display": f"{dir_icon} {dir_label}",
                "score_delta": float(r["score_delta"]),
                "lead_analyst": r["lead_analyst"],
                "summary_note": r["summary_note"],
            }
        )
    leaders = sum(1 for b in breakdown if b["current_placement"] == "Leader")
    improved = sum(1 for b in breakdown if b["direction"] == "up")
    maintained = sum(1 for b in breakdown if b["direction"] == "flat")
    declined = sum(1 for b in breakdown if b["direction"] == "down")

    return _result(
        ctx,
        "MKT-04",
        "count",
        float(leaders),
        status_basis=f"Named a Leader in {leaders} of {len(breakdown)} major analyst evaluations "
        f"({improved} ↑ Improved, {maintained} → Unchanged, {declined} ↓ Declined)",
        breakdown=breakdown,
        meta={
            "evaluations": len(breakdown),
            "leaders": leaders,
            "improved": improved,
            "maintained": maintained,
            "declined": declined,
        },
    )


FUNCTIONS = {
    "MKT-01": mkt_01,
    "MKT-02": mkt_02,
    "MKT-03": mkt_03,
    "MKT-04": mkt_04,
}


# --- Drill-down conditions (FR-GEN-06) --------------------------------------------------------
def drill_condition(ctx: QueryContext, metric_id: str | None, segment: str | None) -> tuple[str, list, str]:
    seg = (segment or "").strip()

    if metric_id == "MKT-02":
        base = "o.workshop_originated = TRUE AND o.created_date BETWEEN ? AND ?"
        args: list = [ctx.period.start, _end(ctx)]
        if seg in ("", "workshops", "created"):
            return (
                base,
                args,
                f"Workshop-originated opportunities (≤90d) — {ctx.period.label}",
            )
        if seg == "qualified":
            return (
                f"{base} AND o.stage NOT IN ({UNQUAL_MARKS})",
                [*args, *UNQUALIFIED_STAGES],
                f"Qualified workshop-originated opportunities — {ctx.period.label}",
            )
        if seg == "won":
            return (
                f"{base} AND o.stage_group = 'won'",
                args,
                f"Won workshop-originated opportunities — {ctx.period.label}",
            )
        raise InvalidSegment("MKT-02 segment must be one of: workshops, created, qualified, won")

    if metric_id == "MKT-03":
        if not seg:
            return (
                "o.campaign_id IS NOT NULL AND o.created_date BETWEEN ? AND ?",
                [ctx.period.start, _end(ctx)],
                f"Campaign-sourced opportunities — {ctx.period.label}",
            )
        if len(seg) == 7 and seg[4:6] == "-Q" and seg[-1] in "1234":
            return (
                "o.campaign_id IS NOT NULL AND o.created_quarter = ? AND o.created_date BETWEEN ? AND ?",
                [seg, ctx.period.start, _end(ctx)],
                f"Campaign-sourced opportunities — {h.quarter_label(seg)}",
            )
        cname = ctx.platform.scalar("SELECT campaign_name FROM dim_campaign WHERE campaign_id = ?", [seg])
        if cname is not None:
            return (
                "o.campaign_id = ? AND o.created_date BETWEEN ? AND ?",
                [seg, ctx.period.start, _end(ctx)],
                f"Campaign-sourced opportunities — {cname} ({ctx.period.label})",
            )
        raise InvalidSegment(f"Unknown MKT-03 segment '{seg}' (expected campaign_id or YYYY-Qn)")

    raise InvalidSegment(f"Drill-down is not supported for metric {metric_id}")
