"""Partners metrics PAR-01 … PAR-03 (Partners plan §2).

PAR-01/02 are opportunity metrics (global filters + RLS; an Alliance manager sees only their
partner). PAR-03 reads the partner-portal certifications (SRC-08) and LMS records (SRC-09);
an Alliance manager sees only their own partner there too.
"""

from __future__ import annotations

from app.schemas.common import MetricResult
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import SUM_TCV, _result, _status
from app.semantic.status import threshold

HAS_PARTNER = "(o.partner IS NOT NULL AND o.partner <> '')"
ROLE = "coalesce(o.partner_role, 'Influenced')"


# --- PAR-01 Pipeline by partner ---------------------------------------------------------------
def par_01(ctx: QueryContext) -> MetricResult:
    rows = ctx.rows(
        ctx.where("o.stage_group = 'open'", HAS_PARTNER),
        select=f"o.partner, {ROLE} AS role, count(*) AS n, {SUM_TCV} AS tcv",
        tail="GROUP BY 1, 2",
    )
    open_total = ctx.value(ctx.where("o.stage_group = 'open'"), SUM_TCV) or 0.0
    by: dict[str, dict] = {}
    for r in rows:
        p = by.setdefault(
            r["partner"],
            {
                "partner": r["partner"],
                "sourced_tcv": 0.0,
                "sourced_count": 0,
                "influenced_tcv": 0.0,
                "influenced_count": 0,
            },
        )
        key = "sourced" if r["role"] == "Sourced" else "influenced"
        p[f"{key}_tcv"] += float(r["tcv"])
        p[f"{key}_count"] += int(r["n"])
    breakdown = sorted(by.values(), key=lambda p: -(p["sourced_tcv"] + p["influenced_tcv"]))
    for p in breakdown:
        p["total_tcv"] = p["sourced_tcv"] + p["influenced_tcv"]
        p["sourced_share"] = h.ratio(p["sourced_tcv"], p["total_tcv"])
    total = sum(p["total_tcv"] for p in breakdown)
    sourced = sum(p["sourced_tcv"] for p in breakdown)
    return _result(
        ctx,
        "PAR-01",
        "usd",
        total,
        status_basis=f"{h.fmt_musd(total)} of open pipeline is partner-tagged; {h.fmt_musd(sourced)} "
        "was partner-sourced",
        breakdown=breakdown,
        meta={
            "open_tcv": float(open_total),
            "partner_share_of_open": h.ratio(total, float(open_total)),
            "sourced_tcv": sourced,
            "influenced_tcv": total - sourced,
            "scope": ctx.scope.description,
        },
    )


# --- PAR-02 Co-sell performance ---------------------------------------------------------------
def par_02(ctx: QueryContext) -> MetricResult:
    end = min(ctx.period.end, ctx.today)
    where, args = ctx.where(
        "o.stage_group IN ('won', 'lost')", "o.close_date BETWEEN ? AND ?", args=[ctx.period.start, end]
    )
    rows = ctx.platform.query(
        f"""SELECT {HAS_PARTNER} AS with_partner,
                   count(*) FILTER (WHERE o.stage_group = 'won') AS won,
                   count(*) FILTER (WHERE o.stage_group = 'lost') AS lost,
                   coalesce(sum(o.tcv_usd) FILTER (WHERE o.stage_group = 'won'), 0) AS won_tcv,
                   count(*) FILTER (WHERE o.stage_group = 'won' AND e.co_sell) AS co_sell_won
            FROM mart_opportunity o
            LEFT JOIN fact_partner_engagement e ON e.opportunity_id = o.opportunity_id
            WHERE {where} GROUP BY 1""",
        args,
    )
    by = {bool(r["with_partner"]): r for r in rows}
    breakdown = []
    for key, label in ((True, "With partner"), (False, "Without partner")):
        r = by.get(key)
        won, lost = (int(r["won"]), int(r["lost"])) if r else (0, 0)
        breakdown.append(
            {
                "group": "with_partner" if key else "without_partner",
                "label": label,
                "won": won,
                "lost": lost,
                "decided": won + lost,
                "won_tcv": float(r["won_tcv"]) if r else 0.0,
                "win_rate": h.ratio(won, won + lost),
            }
        )
    with_p, without_p = breakdown
    total_won = with_p["won_tcv"] + without_p["won_tcv"]
    share = h.ratio(with_p["won_tcv"], total_won)
    wr_with, wr_without = with_p["win_rate"], without_p["win_rate"]
    basis = (
        f"Win rate {h.fmt_pct(wr_with)} with a partner vs {h.fmt_pct(wr_without)} without "
        f"({ctx.period.label})"
        if wr_without is not None
        else f"Win rate {h.fmt_pct(wr_with)} with a partner; no comparison group in your scope"
    )
    return _result(
        ctx,
        "PAR-02",
        "pct",
        wr_with,
        goal=wr_without,
        status_basis=basis,
        breakdown=breakdown,
        meta={
            "partner_share_of_bookings": share,
            "won_tcv_with_partner": with_p["won_tcv"],
            "won_tcv_total": total_won,
            "co_sell_wins": int(by[True]["co_sell_won"]) if True in by else 0,
        },
    )


# --- PAR-03 Certification status --------------------------------------------------------------
def par_03(ctx: QueryContext) -> MetricResult:
    only = "AND t.partner = ?" if ctx.user.partner else ""
    args = [ctx.user.partner] if ctx.user.partner else []
    rows = ctx.platform.query(
        f"""SELECT t.partner, t.tier, t.required_certifications AS required,
                   count(c.partner) FILTER (WHERE c.active) AS certified,
                   count(c.partner) FILTER (WHERE NOT c.active) AS expired,
                   (SELECT count(*) FROM raw_lms_learning_record l
                    WHERE l.partner = t.partner AND l.status = 'In progress') AS in_progress
            FROM raw_partner_tier t LEFT JOIN fact_certification c ON c.partner = t.partner
            WHERE TRUE {only} GROUP BY t.partner, t.tier, t.required_certifications ORDER BY t.partner""",
        args,
    )
    breakdown = []
    for r in rows:
        required, certified = int(r["required"]), int(r["certified"])
        progress = h.ratio(certified, required)
        breakdown.append(
            {
                "partner": r["partner"],
                "tier": r["tier"],
                "required": required,
                "certified": certified,
                "expired": int(r["expired"]),
                "in_progress": int(r["in_progress"]),
                "gap": max(0, required - certified),
                "progress": progress,
                "status": _status(ctx, "PAR-03", progress),
            }
        )
    required = sum(b["required"] for b in breakdown)
    counted = sum(min(b["certified"], b["required"]) for b in breakdown)
    overall = h.ratio(counted, required)
    return _result(
        ctx,
        "PAR-03",
        "pct",
        overall,
        goal=threshold(ctx.platform, "PAR-03")["on_track"],
        status=_status(ctx, "PAR-03", overall),
        status_basis=f"{counted} of {required} required certifications are held and unexpired",
        breakdown=breakdown,
        meta={
            "required": required,
            "certified": counted,
            "in_progress": sum(b["in_progress"] for b in breakdown),
        },
    )


FUNCTIONS = {"PAR-01": par_01, "PAR-02": par_02, "PAR-03": par_03}
