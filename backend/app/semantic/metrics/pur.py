"""Pursuits & Wins metrics PUR-01 … PUR-05 (Pursuits plan §2).

Same contract as `exe.py` / `pip.py`: one function per metric ID returning a MetricResult, every
query built through QueryContext.where (global filters + RLS), and drill-down predicates that
reuse the metric's own conditions so a drill-down always adds up to the number it came from.

Win rate counts Closed Won against Closed Lost only — No Bid and Client Cancelled never count.
PUR-06 (margin at bid vs delivery) is restricted: it lives in RESTRICTED_FUNCTIONS, behind the
role gate in api/deps.py, and is kept out of the shared widget export map.
"""

from __future__ import annotations

from app.data import reference_data as ref
from app.schemas.common import MetricResult
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import SUM_TCV, InvalidSegment, _result, _status
from app.semantic.status import band, threshold

DECIDED = "o.stage_group IN ('won', 'lost')"
TREND_QUARTERS = 8
NOT_RECORDED = "Not recorded"
OUTCOME_SQL = {"won": "o.stage_group = 'won'", "lost": "o.stage_group = 'lost'"}
PURSUIT_JOIN = "fact_pursuit p JOIN mart_opportunity o ON o.opportunity_id = p.opportunity_id"
# segment -> (condition on the opportunity, condition on the bid record)
PURSUIT_SEGMENTS = {
    "": ("TRUE", "TRUE"),
    "no_bid": ("TRUE", "p.decision = 'no_bid'"),
    "pursued": ("TRUE", "p.decision = 'bid'"),
    "won": ("o.stage_group = 'won'", "p.decision = 'bid'"),
    "lost": ("o.stage_group = 'lost'", "p.decision = 'bid'"),
    "late": ("TRUE", "p.submitted_on_time = FALSE"),
}


def _quarters(ctx: QueryContext, n: int) -> tuple[list[str], str, list]:
    quarters = h.last_n_quarters(ctx.today, n)
    return quarters, ", ".join("?" * len(quarters)), [*quarters, ctx.today]


def _closed_in(ctx: QueryContext, n: int = 4) -> tuple[str, list]:
    _, marks, args = _quarters(ctx, n)
    return f"o.close_quarter IN ({marks}) AND o.close_date <= ?", args


def _bid_window(ctx: QueryContext) -> str:
    return h.quarter_bounds(h.last_n_quarters(ctx.today, 4)[0])[0].isoformat()


def _pct_status(ctx: QueryContext, metric_id: str, value: float | None) -> str | None:
    s = band(ctx.platform, metric_id, value)
    return None if s is None else s.value


# --- PUR-01 Win rate by quarter ---------------------------------------------------------------
def pur_01(ctx: QueryContext) -> MetricResult:
    quarters, marks, args = _quarters(ctx, TREND_QUARTERS)
    rows = ctx.rows(
        ctx.where(DECIDED, f"o.close_quarter IN ({marks})", "o.close_date <= ?", args=args),
        select=f"""o.close_quarter AS q,
                   count(*) FILTER (WHERE o.stage_group = 'won') AS won,
                   count(*) FILTER (WHERE o.stage_group = 'lost') AS lost,
                   coalesce(sum(o.tcv_usd) FILTER (WHERE o.stage_group = 'won'), 0) AS won_tcv,
                   {SUM_TCV} AS decided_tcv""",
        tail="GROUP BY o.close_quarter",
    )
    by = {r["q"]: r for r in rows}
    current = h.quarter_key(ctx.today)
    breakdown = []
    for q in quarters:
        r = by.get(q)
        won, lost = (int(r["won"]), int(r["lost"])) if r else (0, 0)
        won_tcv, decided_tcv = (float(r["won_tcv"]), float(r["decided_tcv"])) if r else (0.0, 0.0)
        breakdown.append(
            {
                "quarter": q,
                "label": h.quarter_label(q),
                "won": won,
                "lost": lost,
                "decided": won + lost,
                "won_tcv": won_tcv,
                "decided_tcv": decided_tcv,
                "win_rate": h.ratio(won, won + lost),
                "value_win_rate": h.ratio(won_tcv, decided_tcv),
                "partial": q == current,
            }
        )
    last4 = breakdown[-4:]
    won = sum(r["won"] for r in last4)
    decided = sum(r["decided"] for r in last4)
    rate = h.ratio(won, decided)
    goal = threshold(ctx.platform, "PUR-01")["on_track"]
    return _result(
        ctx,
        "PUR-01",
        "pct",
        rate,
        goal=goal,
        status=_status(ctx, "PUR-01", rate),
        status_basis=f"{won} won of {decided} decided over the last four quarters "
        "(no-bid and client-cancelled excluded)",
        breakdown=breakdown,
        meta={"won": won, "decided": decided, "goal": goal},
    )


# --- PUR-02 Loss reasons ----------------------------------------------------------------------
def pur_02(ctx: QueryContext) -> MetricResult:
    cond, args = _closed_in(ctx)
    rows = ctx.rows(
        ctx.where("o.stage_group = 'lost'", cond, args=args),
        select=f"coalesce(o.loss_reason, '{NOT_RECORDED}') AS reason, count(*) AS n, {SUM_TCV} AS tcv",
        tail="GROUP BY 1 ORDER BY n DESC, tcv DESC",
    )
    total = sum(int(r["n"]) for r in rows)
    top = next((r["reason"] for r in rows if r["reason"] != NOT_RECORDED), None)
    breakdown = [
        {
            "reason": r["reason"],
            "count": int(r["n"]),
            "tcv": float(r["tcv"]),
            "share": h.ratio(int(r["n"]), total),
            "most_frequent": r["reason"] == top,
        }
        for r in rows
    ]
    top_row = next((r for r in breakdown if r["most_frequent"]), None)
    return _result(
        ctx,
        "PUR-02",
        "pct",
        top_row["share"] if top_row else None,
        status_basis=(
            f"{top_row['reason']} is the most frequent reason ({top_row['count']} of {total} losses)"
            if top_row
            else "No losses recorded in the last four quarters"
        ),
        breakdown=breakdown,
        meta={"lost": total, "top_reason": top},
    )


# --- PUR-03 Deal source mix and win rate ------------------------------------------------------
def pur_03(ctx: QueryContext) -> MetricResult:
    cond, args = _closed_in(ctx)
    rows = ctx.rows(
        ctx.where(DECIDED, cond, args=args),
        select=f"""o.lead_source AS source,
                   count(*) FILTER (WHERE o.stage_group = 'won') AS won,
                   count(*) FILTER (WHERE o.stage_group = 'lost') AS lost,
                   {SUM_TCV} AS tcv""",
        tail="GROUP BY o.lead_source",
    )
    by = {r["source"]: r for r in rows}
    decided_total = sum(int(r["won"]) + int(r["lost"]) for r in rows)
    won_total = sum(int(r["won"]) for r in rows)
    breakdown = []
    for source in ref.LEAD_SOURCES:
        r = by.get(source)
        won, lost = (int(r["won"]), int(r["lost"])) if r else (0, 0)
        breakdown.append(
            {
                "source": source,
                "won": won,
                "lost": lost,
                "decided": won + lost,
                "tcv": float(r["tcv"]) if r else 0.0,
                "share": h.ratio(won + lost, decided_total),
                "win_rate": h.ratio(won, won + lost),
            }
        )
    rate = h.ratio(won_total, decided_total)
    return _result(
        ctx,
        "PUR-03",
        "pct",
        rate,
        goal=threshold(ctx.platform, "PUR-01")["on_track"],
        status=_status(ctx, "PUR-01", rate),
        status_basis=f"{won_total} won of {decided_total} decided over the last four quarters",
        breakdown=breakdown,
        meta={"decided": decided_total},
    )


# --- PUR-04 Bid discipline --------------------------------------------------------------------
def bid_callout(no_bid_rate: float | None, win_rate: float | None, no_bid_floor: float, win_floor: float):
    """Rule-based callout: fires only when a low no-bid rate coincides with a low pursued-RFP win rate."""
    if no_bid_rate is None or win_rate is None:
        return None
    if no_bid_rate < no_bid_floor and win_rate < win_floor:
        return (
            f"Only {h.fmt_pct(no_bid_rate)} of RFPs are declined (target {h.fmt_pct(no_bid_floor)}+) while "
            f"pursued RFPs win {h.fmt_pct(win_rate)} (target {h.fmt_pct(win_floor)}+). Moment is bidding on "
            "too many weak-fit RFPs — tighten the bid/no-bid gate."
        )
    return None


def _pursuit_counts(ctx: QueryContext) -> dict:
    where, args = ctx.where("o.created_date >= ?", args=[_bid_window(ctx)])
    return ctx.platform.query(
        f"""SELECT count(*) AS total,
                   count(*) FILTER (WHERE p.decision = 'no_bid') AS no_bid,
                   count(*) FILTER (WHERE p.decision = 'bid' AND o.stage_group = 'won') AS won,
                   count(*) FILTER (WHERE p.decision = 'bid' AND o.stage_group = 'lost') AS lost,
                   count(*) FILTER (WHERE p.submitted_on_time) AS on_time,
                   count(*) FILTER (WHERE p.submitted_on_time IS NOT NULL) AS submitted
            FROM {PURSUIT_JOIN} WHERE {where}""",
        args,
    )[0]


def pur_04(ctx: QueryContext) -> MetricResult:
    c = _pursuit_counts(ctx)
    total, no_bid = int(c["total"]), int(c["no_bid"])
    won, lost, submitted, on_time = int(c["won"]), int(c["lost"]), int(c["submitted"]), int(c["on_time"])
    no_bid_rate = h.ratio(no_bid, total)
    win_rate = h.ratio(won, won + lost)
    on_time_rate = h.ratio(on_time, submitted)
    nb_t, win_t = threshold(ctx.platform, "PUR-04"), threshold(ctx.platform, "PUR-04-WIN")
    measures = [
        {
            "key": "no_bid_rate",
            "label": "No-bid rate",
            "value": no_bid_rate,
            "detail": f"{no_bid} of {total} RFPs declined",
            "target": nb_t["on_track"],
            "target_label": nb_t["label"],
            "status": _pct_status(ctx, "PUR-04", no_bid_rate),
            "segment": "no_bid",
        },
        {
            "key": "pursued_win_rate",
            "label": "Pursued-RFP win rate",
            "value": win_rate,
            "detail": f"{won} won of {won + lost} decided",
            "target": win_t["on_track"],
            "target_label": win_t["label"],
            "status": _pct_status(ctx, "PUR-04-WIN", win_rate),
            "segment": "pursued",
        },
        {
            "key": "on_time_rate",
            "label": "Submitted within SLA",
            "value": on_time_rate,
            "detail": f"{on_time} of {submitted} submissions on time",
            "target": None,
            "target_label": None,
            "status": None,
            "segment": "late",
        },
    ]
    callout = bid_callout(no_bid_rate, win_rate, nb_t["on_track"], win_t["on_track"])
    return _result(
        ctx,
        "PUR-04",
        "pct",
        no_bid_rate,
        goal=nb_t["on_track"],
        status=_status(ctx, "PUR-04", no_bid_rate),
        status_basis=f"{total} RFPs reached the bid/no-bid gate since {_bid_window(ctx)}",
        breakdown=measures,
        narrative=callout,
        meta={"total": total, "no_bid": no_bid, "won": won, "lost": lost, "callout": callout},
    )


# --- PUR-05 Orals conversion ------------------------------------------------------------------
def pur_05(ctx: QueryContext) -> MetricResult:
    where, args = ctx.where("o.created_date >= ?", "p.orals_reached", args=[_bid_window(ctx)])
    c = ctx.platform.query(
        f"""SELECT count(*) FILTER (WHERE o.stage_group = 'won') AS won,
                   count(*) FILTER (WHERE o.stage_group = 'lost') AS lost,
                   count(*) FILTER (WHERE o.stage_group = 'open') AS open
            FROM {PURSUIT_JOIN} WHERE {where}""",
        args,
    )[0]
    won, lost, open_n = int(c["won"]), int(c["lost"]), int(c["open"])
    rate = h.ratio(won, won + lost)
    return _result(
        ctx,
        "PUR-05",
        "pct",
        rate,
        goal=threshold(ctx.platform, "PUR-05")["on_track"],
        status=_status(ctx, "PUR-05", rate),
        status_basis=f"{won} won of {won + lost} decided after reaching orals ({open_n} still open)",
        breakdown=[
            {"outcome": "won", "label": "Won", "count": won},
            {"outcome": "lost", "label": "Lost", "count": lost},
            {"outcome": "open", "label": "Still open", "count": open_n},
        ],
        meta={"won": won, "lost": lost, "open": open_n},
    )


FUNCTIONS = {"PUR-01": pur_01, "PUR-02": pur_02, "PUR-03": pur_03, "PUR-04": pur_04, "PUR-05": pur_05}


# --- PUR-06 Margin at bid vs delivery (restricted) --------------------------------------------
def pur_06(ctx: QueryContext) -> MetricResult:
    quarters, marks, args = _quarters(ctx, TREND_QUARTERS)
    where, wargs = ctx.where(
        "o.stage_group = 'won'",
        "m.delivery_margin IS NOT NULL",
        f"o.close_quarter IN ({marks})",
        "o.close_date <= ?",
        args=args,
    )
    rows = ctx.platform.query(
        f"""SELECT o.close_quarter AS q, count(*) AS deals, sum(o.tcv_usd) AS tcv,
                   sum(o.tcv_usd * m.bid_margin) AS bid_w, sum(o.tcv_usd * m.delivery_margin) AS delivery_w
            FROM fact_margin m JOIN mart_opportunity o ON o.opportunity_id = m.opportunity_id
            WHERE {where} GROUP BY o.close_quarter""",
        wargs,
    )
    by = {r["q"]: r for r in rows}
    breakdown = []
    for q in quarters:
        r = by.get(q)
        tcv = float(r["tcv"]) if r else 0.0
        bid, delivery = (
            (h.ratio(float(r["bid_w"]), tcv), h.ratio(float(r["delivery_w"]), tcv)) if r else (None, None)
        )
        breakdown.append(
            {
                "quarter": q,
                "label": h.quarter_label(q),
                "deals": int(r["deals"]) if r else 0,
                "tcv": tcv,
                "bid_margin": bid,
                "delivery_margin": delivery,
                "erosion": None if bid is None or delivery is None else bid - delivery,
            }
        )
    tcv = sum(r["tcv"] for r in breakdown)
    bid_w = sum((r["bid_margin"] or 0) * r["tcv"] for r in breakdown)
    delivery_w = sum((r["delivery_margin"] or 0) * r["tcv"] for r in breakdown)
    bid, delivery = h.ratio(bid_w, tcv), h.ratio(delivery_w, tcv)
    erosion = None if bid is None or delivery is None else bid - delivery
    return _result(
        ctx,
        "PUR-06",
        "pct",
        erosion,
        goal=threshold(ctx.platform, "PUR-06")["on_track"],
        status=_status(ctx, "PUR-06", erosion),
        status_basis=(
            f"Priced at {h.fmt_pct(bid)} at bid, {h.fmt_pct(delivery)} in delivery "
            f"({sum(r['deals'] for r in breakdown)} won deals with project financials)"
            if erosion is not None
            else "No won deals with project financials in the last eight quarters"
        ),
        breakdown=breakdown,
        meta={"bid_margin": bid, "delivery_margin": delivery, "restricted": True},
    )


RESTRICTED_FUNCTIONS = {"PUR-06": pur_06}


# --- Drill-down conditions (FR-GEN-06) --------------------------------------------------------
def _outcome(part: str) -> str:
    if part not in ("", *OUTCOME_SQL):
        raise InvalidSegment("Outcome must be 'won' or 'lost'")
    return OUTCOME_SQL.get(part, "TRUE")


def drill_condition(ctx: QueryContext, metric_id: str, segment: str | None) -> tuple[str, list, str]:
    """(condition, args, title) behind a Pursuits aggregate — the same predicate as the metric."""
    head, _, part = (segment or "").partition("|")
    if metric_id == "PUR-01":
        quarters = h.last_n_quarters(ctx.today, TREND_QUARTERS)
        if head not in quarters:
            raise InvalidSegment(f"PUR-01 segment must be '<quarter>[|won|lost]', e.g. {quarters[-1]}")
        label = {"": "decided", "won": "won", "lost": "lost"}[part if part in ("", *OUTCOME_SQL) else ""]
        return (
            f"{DECIDED} AND o.close_quarter = ? AND o.close_date <= ? AND {_outcome(part)}",
            [head, ctx.today],
            f"{h.quarter_label(head)} — {label} deals",
        )
    if metric_id == "PUR-02":
        cond, args = _closed_in(ctx)
        if head == NOT_RECORDED:
            reason_sql, reason_args = "o.loss_reason IS NULL", []
        elif head in ref.LOSS_REASONS:
            reason_sql, reason_args = "o.loss_reason = ?", [head]
        else:
            raise InvalidSegment(
                f"PUR-02 segment must be one of {', '.join([*ref.LOSS_REASONS, NOT_RECORDED])}"
            )
        return (
            f"o.stage_group = 'lost' AND {cond} AND {reason_sql}",
            [*args, *reason_args],
            f"Lost — {head}",
        )
    if metric_id == "PUR-03":
        if head not in ref.LEAD_SOURCES:
            raise InvalidSegment(
                f"PUR-03 segment must be '<source>[|won|lost]', source one of {', '.join(ref.LEAD_SOURCES)}"
            )
        cond, args = _closed_in(ctx)
        return (
            f"{DECIDED} AND {cond} AND o.lead_source = ? AND {_outcome(part)}",
            [*args, head],
            f"{head} — {part or 'decided'} deals",
        )
    if metric_id in ("PUR-04", "PUR-05"):
        start = _bid_window(ctx)
        if metric_id == "PUR-05":
            if head not in ("", "won", "lost", "open"):
                raise InvalidSegment("PUR-05 segment must be won, lost or open")
            outcome = "TRUE" if head == "" else f"o.stage_group = '{head}'"
            return (
                f"o.created_date >= ? AND {outcome} AND o.opportunity_id IN "
                "(SELECT p.opportunity_id FROM fact_pursuit p WHERE p.orals_reached)",
                [start],
                f"Pursued RFPs that reached orals{'' if not head else ' — ' + head}",
            )
        if head not in PURSUIT_SEGMENTS:
            raise InvalidSegment(
                f"PUR-04 segment must be one of {', '.join(k for k in PURSUIT_SEGMENTS if k)}"
            )
        o_cond, p_cond = PURSUIT_SEGMENTS[head]
        return (
            f"o.created_date >= ? AND {o_cond} AND o.opportunity_id IN "
            f"(SELECT p.opportunity_id FROM fact_pursuit p WHERE {p_cond})",
            [start],
            f"RFP pursuits — {head.replace('_', ' ') or 'all'}",
        )
    if metric_id == "PUR-06":
        if head not in h.last_n_quarters(ctx.today, TREND_QUARTERS):
            raise InvalidSegment("PUR-06 segment must be one of the last eight quarters, e.g. 2026-Q2")
        return (
            "o.stage_group = 'won' AND o.close_quarter = ? AND o.close_date <= ? AND o.opportunity_id IN "
            "(SELECT m.opportunity_id FROM fact_margin m WHERE m.delivery_margin IS NOT NULL)",
            [head, ctx.today],
            f"{h.quarter_label(head)} — won deals with delivery margin",
        )
    raise InvalidSegment(f"No drill-down defined for {metric_id}")
