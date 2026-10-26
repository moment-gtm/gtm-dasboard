"""Accounts metrics ACC-01 … ACC-04 (Accounts plan §2).

The penetration matrix is account × practice. A cell is Sold when a Closed Won deal this fiscal
year includes the practice on a line item, Open when an open deal includes it, otherwise Not
addressed. ACC-02 reads the same matrix, so the whitespace share always reconciles to it.
Row-level security limits the matrix to the caller's accounts; deal-level filters (platform,
deal source) narrow the deals that mark a cell.
"""

from __future__ import annotations

from datetime import date

from app.data import reference_data as ref
from app.schemas.common import MetricResult
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.filters import dimension_clause
from app.semantic.metrics.exe import SUM_TCV, _result, _status
from app.semantic.rls import scope_for
from app.semantic.status import setting, threshold

ACCOUNT_DIMENSIONS = {"vertical", "geography", "account", "client_partner"}
DEAL_DIMENSIONS = {"platform", "deal_source"}
SOLD, OPEN, NOT_ADDRESSED = "sold", "open", "not_addressed"
HEALTH_LABELS = {"current": "Current", "needs_update": "Needs update", "overdue": "Overdue"}
EXPANSION_MONTHS = 24


def _account_where(ctx: QueryContext, alias: str = "a") -> tuple[str, list]:
    sql, args = dimension_clause(ctx.params, alias, only=ACCOUNT_DIMENSIONS)
    scope = scope_for(ctx.user, alias)
    return f"{sql} AND {scope.row_sql}", [*args, *scope.row_args]


def _practices(ctx: QueryContext) -> list[str]:
    selected = ctx.params.practice
    return [p for p in ref.PRACTICES if not selected or p in selected]


def _matrix(ctx: QueryContext) -> tuple[list[dict], list[str]]:
    practices = _practices(ctx)
    fy_start = date(ctx.today.year, 1, 1)
    a_where, a_args = _account_where(ctx)
    accounts = ctx.platform.query(
        f"""SELECT a.account_id, a.name, a.strategic, a.vertical, a.geography, a.client_partner_upn,
                   coalesce(p.name, a.client_partner_upn) AS client_partner
            FROM dim_account a LEFT JOIN dim_person p ON p.upn = a.client_partner_upn
            WHERE {a_where}""",
        a_args,
    )
    d_sql, d_args = dimension_clause(ctx.params, "o", only=DEAL_DIMENSIONS)
    a2_where, a2_args = _account_where(ctx, "o")
    cells = ctx.platform.query(
        f"""SELECT o.account_id, b.practice,
                   bool_or(o.stage_group = 'won' AND o.close_date BETWEEN ? AND ?) AS sold,
                   bool_or(o.stage_group = 'open') AS open_deal
            FROM mart_opportunity o
            JOIN bridge_opportunity_practice b ON b.opportunity_id = o.opportunity_id
            WHERE {d_sql} AND {a2_where}
            GROUP BY 1, 2""",
        [fy_start, ctx.today, *d_args, *a2_args],
    )
    state = {
        (c["account_id"], c["practice"]): (SOLD if c["sold"] else OPEN if c["open_deal"] else None)
        for c in cells
    }
    rows = []
    for a in accounts:
        by_practice = {p: state.get((a["account_id"], p)) or NOT_ADDRESSED for p in practices}
        rows.append(
            {
                "account_id": a["account_id"],
                "account_name": a["name"],
                "strategic": bool(a["strategic"]),
                "vertical": a["vertical"],
                "geography": a["geography"],
                "client_partner": a["client_partner"],
                "cells": by_practice,
                "sold": sum(1 for s in by_practice.values() if s == SOLD),
                "open": sum(1 for s in by_practice.values() if s == OPEN),
            }
        )
    rows.sort(key=lambda r: (not r["strategic"], -(r["sold"] + r["open"]), r["account_name"]))
    return rows, practices


# --- ACC-01 Penetration matrix ----------------------------------------------------------------
def acc_01(ctx: QueryContext) -> MetricResult:
    rows, practices = _matrix(ctx)
    cells = len(rows) * len(practices)
    sold = sum(r["sold"] for r in rows)
    open_n = sum(r["open"] for r in rows)
    share = h.ratio(sold, cells)
    return _result(
        ctx,
        "ACC-01",
        "pct",
        share,
        status_basis=f"{sold} of {cells} account-practice cells are Sold this fiscal year, {open_n} are Open",
        breakdown=rows,
        meta={
            "practices": practices,
            "accounts": len(rows),
            "cells": cells,
            "sold": sold,
            "open": open_n,
            "not_addressed": cells - sold - open_n,
            "scope": ctx.scope.description,
        },
    )


# --- ACC-02 Whitespace summary ----------------------------------------------------------------
def acc_02(ctx: QueryContext) -> MetricResult:
    rows, practices = _matrix(ctx)
    breakdown = []
    for p in practices:
        states = [r["cells"][p] for r in rows]
        sold, open_n = states.count(SOLD), states.count(OPEN)
        na = states.count(NOT_ADDRESSED)
        breakdown.append(
            {
                "practice": p,
                "sold": sold,
                "open": open_n,
                "not_addressed": na,
                "pursued_share": h.ratio(open_n, open_n + na),
            }
        )
    open_total = sum(b["open"] for b in breakdown)
    na_total = sum(b["not_addressed"] for b in breakdown)
    share = h.ratio(open_total, open_total + na_total)
    goal = threshold(ctx.platform, "ACC-02")["on_track"]
    return _result(
        ctx,
        "ACC-02",
        "pct",
        share,
        goal=goal,
        status=_status(ctx, "ACC-02", share),
        status_basis=f"{open_total} of {open_total + na_total} whitespace cells are being pursued "
        "through an open deal",
        breakdown=breakdown,
        meta={"whitespace": open_total + na_total, "pursued": open_total, "not_addressed": na_total},
    )


# --- ACC-03 Expansion vs new logo -------------------------------------------------------------
def acc_03(ctx: QueryContext) -> MetricResult:
    end = min(ctx.period.end, ctx.today)
    where, args = ctx.where(
        "o.stage_group = 'won'", "o.close_date BETWEEN ? AND ?", args=[ctx.period.start, end]
    )
    rows = ctx.rows(
        (where, args),
        select=f"""CASE WHEN EXISTS (
                        SELECT 1 FROM fact_account_booking_history bh
                        WHERE bh.account_id = o.account_id AND bh.booked_on < o.close_date
                          AND bh.booked_on >= o.close_date - INTERVAL {EXPANSION_MONTHS} MONTH)
                   THEN 'expansion' ELSE 'new_logo' END AS kind,
                   count(*) AS n, {SUM_TCV} AS tcv""",
        tail="GROUP BY 1",
    )
    by = {r["kind"]: r for r in rows}
    total = sum(float(r["tcv"]) for r in rows)
    breakdown = []
    for kind, label in (("expansion", "Expansion"), ("new_logo", "New logo")):
        r = by.get(kind)
        tcv = float(r["tcv"]) if r else 0.0
        breakdown.append(
            {
                "kind": kind,
                "label": label,
                "count": int(r["n"]) if r else 0,
                "tcv": tcv,
                "share": h.ratio(tcv, total),
            }
        )
    share = breakdown[0]["share"]
    return _result(
        ctx,
        "ACC-03",
        "pct",
        share,
        status_basis=f"{h.fmt_musd(breakdown[0]['tcv'])} of {h.fmt_musd(total)} won TCV came from existing "
        f"accounts ({ctx.period.label})",
        breakdown=breakdown,
        meta={"total_tcv": total, "deals": sum(b["count"] for b in breakdown)},
    )


# --- ACC-04 Account-plan health ---------------------------------------------------------------
def plan_health(days: int | None, current_days: float, overdue_days: float) -> str:
    if days is None or days > overdue_days:
        return "overdue"
    return "current" if days <= current_days else "needs_update"


def acc_04(ctx: QueryContext) -> MetricResult:
    current = setting(ctx.platform, "ACC-04.current_days", 90)
    overdue = setting(ctx.platform, "ACC-04.overdue_days", 120)
    a_where, a_args = _account_where(ctx)
    rows = ctx.platform.query(
        f"""SELECT a.account_id, a.name, a.client_partner_upn, p.plan_status, p.last_review_date,
                   coalesce(m.name, a.client_partner_upn) AS client_partner
            FROM dim_account a
            LEFT JOIN dim_account_plan p ON p.account_id = a.account_id
            LEFT JOIN dim_person m ON m.upn = a.client_partner_upn
            WHERE a.strategic AND {a_where} ORDER BY a.name""",
        a_args,
    )
    breakdown = []
    for r in rows:
        days = (ctx.today - r["last_review_date"]).days if r["last_review_date"] else None
        health = plan_health(days, current, overdue)
        breakdown.append(
            {
                "account_id": r["account_id"],
                "account_name": r["name"],
                "client_partner": r["client_partner"],
                "plan_status": r["plan_status"] or "No plan",
                "last_review_date": r["last_review_date"].isoformat() if r["last_review_date"] else None,
                "days_since_review": days,
                "health": health,
                "label": HEALTH_LABELS[health],
            }
        )
    counts = {k: sum(1 for b in breakdown if b["health"] == k) for k in HEALTH_LABELS}
    share = h.ratio(counts["current"], len(breakdown))
    return _result(
        ctx,
        "ACC-04",
        "pct",
        share,
        status_basis=f"{counts['current']} of {len(breakdown)} strategic account plans reviewed within "
        f"{int(current)} days",
        breakdown=breakdown,
        meta={
            **counts,
            "strategic_accounts": len(breakdown),
            "current_days": current,
            "overdue_days": overdue,
        },
    )


FUNCTIONS = {"ACC-01": acc_01, "ACC-02": acc_02, "ACC-03": acc_03, "ACC-04": acc_04}
