"""Pipeline metrics PIP-01 … PIP-07 (Pipeline plan §2).

Same contract as `exe.py`: one function per metric ID returning a MetricResult, every query built
through QueryContext.where (global filters + RLS), and drill-down predicates that reuse the
metric's own conditions so a drill-down always adds up to the number it came from.
"""

from __future__ import annotations

from datetime import date

from app.schemas.common import MetricResult
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import (
    OPEN,
    QUALIFIED,
    SUM_TCV,
    InvalidSegment,
    _result,
    attention_rules,
)

FUNNEL_STAGES = ("Identify", "Qualify", "Propose", "Orals", "Negotiate", "Closed Won")
OPEN_STAGES = FUNNEL_STAGES[:-1]
MOVEMENTS = (
    ("created", "Created"),
    ("advanced", "Advanced"),
    ("regressed", "Regressed"),
    ("slipped", "Slipped"),
    ("closed", "Closed"),
)


def _buckets(ctx: QueryContext) -> list[dict]:
    return ctx.platform.query("SELECT * FROM ref_bucket ORDER BY sort_order")


def _bands(ctx: QueryContext) -> list[dict]:
    return ctx.platform.query("SELECT * FROM ref_size_band ORDER BY sort_order")


def _bucket_sql(b: dict) -> tuple[str, list]:
    if b["max_days"] is None:
        return "o.days_in_stage >= ?", [b["min_days"]]
    return "o.days_in_stage BETWEEN ? AND ?", [b["min_days"], b["max_days"]]


def _band_sql(b: dict) -> tuple[str, list]:
    if b["max_usd"] is None:
        return "o.tcv_usd >= ?", [b["min_usd"]]
    return "o.tcv_usd >= ? AND o.tcv_usd < ?", [b["min_usd"], b["max_usd"]]


# --- PIP-01 Stage funnel + trailing-4Q conversion ---------------------------------------------
def pip_01(ctx: QueryContext) -> MetricResult:
    window_start = h.quarter_bounds(h.last_n_quarters(ctx.today, 4)[0])[0]
    open_rows = ctx.rows(
        ctx.where(OPEN),
        select=f"o.stage, count(*) AS n, {SUM_TCV} AS tcv",
        tail="GROUP BY o.stage",
    )
    open_by = {r["stage"]: r for r in open_rows}
    where, args = ctx.where("o.created_date >= ?", args=[window_start])
    reached_rows = ctx.platform.query(
        f"""SELECT hst.stage, count(DISTINCT hst.opportunity_id) AS n
            FROM fact_stage_history hst JOIN mart_opportunity o ON o.opportunity_id = hst.opportunity_id
            WHERE {where} GROUP BY hst.stage""",
        args,
    )
    reached = {r["stage"]: r["n"] for r in reached_rows}
    breakdown = []
    for i, stage in enumerate(FUNNEL_STAGES):
        nxt = FUNNEL_STAGES[i + 1] if i + 1 < len(FUNNEL_STAGES) else None
        o = open_by.get(stage)
        breakdown.append(
            {
                "stage": stage,
                "open_count": int(o["n"]) if o else 0,
                "open_tcv": float(o["tcv"]) if o else 0.0,
                "reached": reached.get(stage, 0),
                "next_stage": nxt,
                "conversion": h.ratio(reached.get(nxt, 0), reached.get(stage, 0)) if nxt else None,
            }
        )
    overall = h.ratio(reached.get("Closed Won", 0), reached.get("Identify", 0))
    return _result(
        ctx,
        "PIP-01",
        "pct",
        overall,
        breakdown=breakdown,
        status_basis=f"Conversion over opportunities created since {window_start.isoformat()} "
        "(trailing 4 quarters)",
        meta={
            "window_start": window_start.isoformat(),
            "open_count": sum(r["open_count"] for r in breakdown),
        },
    )


# --- PIP-02 Ageing heatmap --------------------------------------------------------------------
def pip_02(ctx: QueryContext) -> MetricResult:
    buckets = _buckets(ctx)
    where, args = ctx.where(OPEN)
    rows = ctx.platform.query(
        f"""SELECT o.stage, b.bucket_key, count(*) AS n, {SUM_TCV} AS tcv
            FROM mart_opportunity o
            JOIN ref_bucket b ON o.days_in_stage >= b.min_days
             AND (b.max_days IS NULL OR o.days_in_stage <= b.max_days)
            WHERE {where} GROUP BY o.stage, b.bucket_key""",
        args,
    )
    cells = {(r["stage"], r["bucket_key"]): r for r in rows}
    breakdown = []
    for stage in OPEN_STAGES:
        row: dict = {"stage": stage, "count": 0, "tcv": 0.0}
        for b in buckets:
            c = cells.get((stage, b["bucket_key"]))
            n, v = (int(c["n"]), float(c["tcv"])) if c else (0, 0.0)
            row[b["bucket_key"]] = {"count": n, "tcv": v}
            row["count"] += n
            row["tcv"] += v
        breakdown.append(row)
    review_keys = [b["bucket_key"] for b in buckets if b["review"]]
    total = sum(r["count"] for r in breakdown)
    past = sum(r[k]["count"] for r in breakdown for k in review_keys)
    return _result(
        ctx,
        "PIP-02",
        "count",
        float(total),
        breakdown=breakdown,
        status_basis=f"{past} of {total} open deals are past the {attention_rules(ctx)['review_days']}-day "
        "review line",
        meta={
            "buckets": [
                {"key": b["bucket_key"], "label": b["label"], "review": b["review"]} for b in buckets
            ],
            "past_review": past,
        },
    )


# --- PIP-03 / PIP-04 Mix by practice and platform ---------------------------------------------
def pip_03(ctx: QueryContext) -> MetricResult:
    where, args = ctx.where(OPEN)
    rows = ctx.platform.query(
        f"""SELECT b.practice,
                   coalesce(sum(b.amount_usd) FILTER (WHERE b.is_lead), 0) AS lead,
                   coalesce(sum(b.amount_usd) FILTER (WHERE NOT b.is_lead), 0) AS contributing
            FROM bridge_opportunity_practice b JOIN mart_opportunity o ON o.opportunity_id = b.opportunity_id
            WHERE {where} GROUP BY b.practice""",
        args,
    )
    by = {r["practice"]: r for r in rows}
    order = [r["name"] for r in ctx.platform.query("SELECT name FROM dim_practice ORDER BY sort_order")]
    order += sorted(p for p in by if p not in order)
    breakdown = []
    for p in order:
        lead = float(by[p]["lead"]) if p in by else 0.0
        contrib = float(by[p]["contributing"]) if p in by else 0.0
        breakdown.append({"practice": p, "lead": lead, "contributing": contrib, "total": lead + contrib})
    return _result(
        ctx,
        "PIP-03",
        "usd",
        sum(b["total"] for b in breakdown),
        breakdown=breakdown,
        meta={
            "lead": sum(b["lead"] for b in breakdown),
            "contributing": sum(b["contributing"] for b in breakdown),
        },
    )


def pip_04(ctx: QueryContext) -> MetricResult:
    rows = ctx.rows(
        ctx.where(OPEN),
        select=f"""o.primary_platform AS platform,
        coalesce(sum(o.tcv_usd) FILTER (WHERE {QUALIFIED}), 0) AS qualified,
        coalesce(sum(o.tcv_usd) FILTER (WHERE o.stage = 'Identify'), 0) AS identify""",
        tail="GROUP BY o.primary_platform",
    )
    by = {r["platform"]: r for r in rows}
    order = [r["name"] for r in ctx.platform.query("SELECT name FROM dim_platform ORDER BY sort_order")]
    order += sorted(p for p in by if p not in order)
    breakdown = []
    for p in order:
        q = float(by[p]["qualified"]) if p in by else 0.0
        i = float(by[p]["identify"]) if p in by else 0.0
        breakdown.append({"platform": p, "qualified": q, "identify": i, "total": q + i})
    return _result(ctx, "PIP-04", "usd", sum(b["total"] for b in breakdown), breakdown=breakdown)


# --- PIP-05 Deal-size distribution ------------------------------------------------------------
def pip_05(ctx: QueryContext) -> MetricResult:
    bands = _bands(ctx)
    where, args = ctx.where(OPEN)
    rows = ctx.platform.query(
        f"""SELECT b.band_key, count(*) AS n, {SUM_TCV} AS tcv
            FROM mart_opportunity o
            JOIN ref_size_band b ON o.tcv_usd >= b.min_usd AND (b.max_usd IS NULL OR o.tcv_usd < b.max_usd)
            WHERE {where} GROUP BY b.band_key""",
        args,
    )
    by = {r["band_key"]: r for r in rows}
    breakdown = [
        {
            "band": b["band_key"],
            "label": b["label"],
            "count": int(by[b["band_key"]]["n"]) if b["band_key"] in by else 0,
            "tcv": float(by[b["band_key"]]["tcv"]) if b["band_key"] in by else 0.0,
        }
        for b in bands
    ]
    return _result(
        ctx,
        "PIP-05",
        "count",
        float(sum(b["count"] for b in breakdown)),
        breakdown=breakdown,
        meta={"total_tcv": sum(b["tcv"] for b in breakdown)},
    )


# --- PIP-06 Opportunity register (rows come from /api/opportunities) --------------------------
def pip_06(ctx: QueryContext) -> MetricResult:
    r = ctx.rows(ctx.where(OPEN), select=f"count(*) AS n, {SUM_TCV} AS tcv")[0]
    rules = attention_rules(ctx)
    flagged = ctx.value(
        ctx.where(OPEN, "(o.days_in_stage > ? OR o.past_dated)", args=[rules["review_days"]]),
        "count(*)",
    )
    return _result(
        ctx,
        "PIP-06",
        "count",
        float(r["n"]),
        breakdown=[],
        status_basis=f"{flagged} of {r['n']} open deals are ageing, stalled or past close date",
        meta={"total_tcv": float(r["tcv"]), "flagged": int(flagged or 0), **rules},
    )


# --- PIP-07 Week-over-week stage movement -----------------------------------------------------
def snapshot_dates(ctx: QueryContext) -> tuple[date | None, date | None]:
    latest = ctx.platform.scalar(
        "SELECT max(snapshot_date) FROM fact_opportunity_snapshot WHERE snapshot_date <= ?", [ctx.today]
    )
    if latest is None:
        return None, None
    prev = ctx.platform.scalar(
        "SELECT max(snapshot_date) FROM fact_opportunity_snapshot WHERE snapshot_date < ?", [latest]
    )
    return prev, latest


# Movement per opportunity between two snapshots; NULL = open in both with no change.
MOVEMENT_SQL = """
    FROM mart_opportunity o
    LEFT JOIN fact_opportunity_snapshot p ON p.opportunity_id = o.opportunity_id AND p.snapshot_date = ?
    LEFT JOIN fact_opportunity_snapshot c ON c.opportunity_id = o.opportunity_id AND c.snapshot_date = ?
    LEFT JOIN ref_stage_probability ps ON ps.stage = p.stage
    LEFT JOIN ref_stage_probability cs ON cs.stage = c.stage
"""
MOVEMENT_CASE = """CASE WHEN p.opportunity_id IS NULL THEN 'created'
    WHEN c.opportunity_id IS NULL THEN 'closed'
    WHEN cs.stage_order > ps.stage_order THEN 'advanced'
    WHEN cs.stage_order < ps.stage_order THEN 'regressed'
    WHEN c.close_date > p.close_date OR (p.close_date >= ? AND c.close_date < ?) THEN 'slipped'
    END"""
IN_EITHER = "(p.opportunity_id IS NOT NULL OR c.opportunity_id IS NOT NULL)"


def pip_07(ctx: QueryContext) -> MetricResult:
    prev, cur = snapshot_dates(ctx)
    if prev is None or cur is None:
        return _result(
            ctx,
            "PIP-07",
            "usd",
            None,
            status_basis="Fewer than two weekly snapshots are available yet",
            meta={"previous_snapshot": None, "latest_snapshot": None},
        )
    where, args = ctx.where(IN_EITHER)
    rows = ctx.platform.query(
        f"""SELECT m AS movement, count(*) AS n, coalesce(sum(tcv), 0) AS tcv FROM (
                SELECT {MOVEMENT_CASE} AS m, coalesce(c.tcv_usd, p.tcv_usd) AS tcv {MOVEMENT_SQL}
                WHERE {where}) GROUP BY m""",
        [prev, cur, prev, cur, *args],
    )
    by = {r["movement"]: r for r in rows}
    totals = ctx.platform.query(
        f"""SELECT coalesce(sum(p.tcv_usd), 0) AS prev_tcv, coalesce(sum(c.tcv_usd), 0) AS cur_tcv,
                   count(p.opportunity_id) AS prev_n, count(c.opportunity_id) AS cur_n
            {MOVEMENT_SQL} WHERE {where}""",
        [prev, cur, *args],
    )[0]
    breakdown = [
        {
            "movement": key,
            "label": label,
            "count": int(by[key]["n"]) if key in by else 0,
            "tcv": float(by[key]["tcv"]) if key in by else 0.0,
        }
        for key, label in MOVEMENTS
    ]
    net = float(totals["cur_tcv"]) - float(totals["prev_tcv"])
    return _result(
        ctx,
        "PIP-07",
        "usd",
        net,
        breakdown=breakdown,
        status_basis=f"Open pipeline {h.fmt_musd(totals['prev_tcv'])} → {h.fmt_musd(totals['cur_tcv'])} "
        f"between the {prev.isoformat()} and {cur.isoformat()} snapshots",
        meta={
            "previous_snapshot": prev.isoformat(),
            "latest_snapshot": cur.isoformat(),
            "previous_tcv": float(totals["prev_tcv"]),
            "latest_tcv": float(totals["cur_tcv"]),
            "previous_count": int(totals["prev_n"]),
            "latest_count": int(totals["cur_n"]),
        },
    )


FUNCTIONS = {
    "PIP-01": pip_01,
    "PIP-02": pip_02,
    "PIP-03": pip_03,
    "PIP-04": pip_04,
    "PIP-05": pip_05,
    "PIP-06": pip_06,
    "PIP-07": pip_07,
}


# --- Drill-down conditions (FR-GEN-06) --------------------------------------------------------
def _stage(segment: str, allowed: tuple[str, ...]) -> str:
    if segment not in allowed:
        raise InvalidSegment(f"Stage must be one of {', '.join(allowed)}")
    return segment


def drill_condition(ctx: QueryContext, metric_id: str, segment: str | None) -> tuple[str, list, str]:
    """(condition, args, title) behind a Pipeline aggregate — the same predicate as the metric."""
    if metric_id in ("PIP-01", "PIP-06"):
        if not segment:
            return OPEN, [], "Open pipeline"
        stage = _stage(segment, FUNNEL_STAGES)
        if stage == "Closed Won":
            return "o.stage_group = 'won'", [], "Closed Won"
        return f"{OPEN} AND o.stage = ?", [stage], f"Open pipeline — {stage}"
    if metric_id == "PIP-02":
        stage, _, bucket_key = (segment or "").partition("|")
        _stage(stage, OPEN_STAGES)
        bucket = next((b for b in _buckets(ctx) if b["bucket_key"] == bucket_key), None)
        if bucket is None:
            raise InvalidSegment("PIP-02 segment must be '<stage>|<bucket>', e.g. Propose|61-90")
        cond, args = _bucket_sql(bucket)
        return f"{OPEN} AND o.stage = ? AND {cond}", [stage, *args], f"{stage} — {bucket['label']} in stage"
    if metric_id == "PIP-03":
        practice, _, part = (segment or "").partition("|")
        if not practice or part not in ("", "lead", "contributing"):
            raise InvalidSegment("PIP-03 segment must be '<practice>' or '<practice>|lead|contributing'")
        lead = {"": "TRUE", "lead": "is_lead", "contributing": "NOT is_lead"}[part]
        label = {"": "all", "lead": "lead", "contributing": "contributing"}[part]
        return (
            f"{OPEN} AND o.opportunity_id IN (SELECT opportunity_id FROM bridge_opportunity_practice "
            f"WHERE practice = ? AND {lead})",
            [practice],
            f"Open pipeline — {practice} ({label})",
        )
    if metric_id == "PIP-04":
        platform, _, part = (segment or "").partition("|")
        part_sql = {"qualified": QUALIFIED, "identify": "o.stage = 'Identify'", "": "TRUE"}
        if not platform or part not in part_sql:
            raise InvalidSegment("PIP-04 segment must be '<platform>' or '<platform>|qualified|identify'")
        return (
            f"{OPEN} AND o.primary_platform = ? AND {part_sql[part]}",
            [platform],
            f"Open pipeline — {platform}" + (f" ({part})" if part else ""),
        )
    if metric_id == "PIP-05":
        band = next((b for b in _bands(ctx) if b["band_key"] == segment), None)
        if band is None:
            raise InvalidSegment(
                f"PIP-05 segment must be one of {', '.join(b['band_key'] for b in _bands(ctx))}"
            )
        cond, args = _band_sql(band)
        return f"{OPEN} AND {cond}", args, f"Open pipeline — {band['label']}"
    if metric_id == "PIP-07":
        labels = dict(MOVEMENTS)
        if segment not in labels:
            raise InvalidSegment(f"PIP-07 segment must be one of {', '.join(labels)}")
        prev, cur = snapshot_dates(ctx)
        if prev is None or cur is None:
            return "FALSE", [], f"{labels[segment]} deals"
        return (
            f"o.opportunity_id IN (SELECT opportunity_id FROM (SELECT o.opportunity_id, "
            f"{MOVEMENT_CASE} AS m {MOVEMENT_SQL} WHERE {IN_EITHER}) WHERE m = ?)",
            [prev, cur, prev, cur, segment],
            f"{labels[segment]} since {prev.isoformat()}",
        )
    raise InvalidSegment(f"No drill-down defined for {metric_id}")
