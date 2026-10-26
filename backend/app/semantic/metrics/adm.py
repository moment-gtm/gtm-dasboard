"""Administration metrics and DQ console queries (ADM-01, FR-ADM-04). Admin-only; no RLS scoping."""

from __future__ import annotations

from app.platform.db import Platform
from app.schemas.common import MetricResult, SparkPoint
from app.semantic import dq
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import _result, _status
from app.semantic.status import threshold

STEWARD = "Sales Operations (data steward)"


def completeness_series(p: Platform) -> list[dict]:
    rows = p.query("""SELECT CAST(week_start AS VARCHAR) AS week_start, CAST(week_end AS VARCHAR) AS week_end,
                  qualified, complete,
                  CASE WHEN qualified = 0 THEN NULL ELSE complete * 1.0 / qualified END AS completeness
           FROM completeness_metric ORDER BY week_start""")
    return rows


def gate(p: Platform) -> dict:
    """AC-05: met when each of the latest two weeks is at or above the ADM-01 on-track threshold."""
    series = completeness_series(p)
    t = threshold(p, "ADM-01")
    need = t["on_track"] if t else 0.95
    last = series[-dq.GATE_WEEKS :]
    met = len(last) == dq.GATE_WEEKS and all((r["completeness"] or 0) >= need for r in last)
    return {"met": met, "required": need, "weeks": dq.GATE_WEEKS, "latest": last}


def adm_01(ctx: QueryContext) -> MetricResult:
    series = completeness_series(ctx.platform)
    latest = series[-1] if series else None
    value = latest["completeness"] if latest else None
    g = gate(ctx.platform)
    return _result(
        ctx,
        "ADM-01",
        "pct",
        value,
        goal=g["required"],
        status=_status(ctx, "ADM-01", value),
        status_basis="Latest ISO week, qualified opportunities only",
        breakdown=[
            {
                "field": label,
                "complete": ctx.platform.scalar(f"""SELECT count(*) FROM fact_opportunity f
                        WHERE f.opportunity_id IN (SELECT opportunity_id FROM fact_stage_history
                              WHERE stage IN ({", ".join(repr(s) for s in dq.QUALIFIED_STAGES)}))
                          AND {pred}"""),
            }
            for _, label, pred in dq.MANDATORY_FIELDS
        ],
        sparkline=[SparkPoint(label=r["week_start"], value=r["completeness"] or 0) for r in series],
        meta={"gate": g, "series": series},
    )


def dq_summary(p: Platform) -> dict:
    counts = {
        r["rule_id"]: r
        for r in p.query(
            "SELECT rule_id, count(*) AS records, "
            "count(DISTINCT coalesce(owner_upn, '')) AS owners FROM dq_finding GROUP BY 1"
        )
    }
    rules = [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "handling": r.handling,
            "severity": r.severity,
            "active": r.active,
            "inactive_reason": r.inactive_reason,
            "records": counts.get(r.rule_id, {}).get("records", 0),
        }
        for r in dq.RULES
    ]
    by_owner = p.query(f"""SELECT coalesce(owner_upn, '{STEWARD}') AS owner, count(*) AS records
            FROM dq_finding GROUP BY 1 ORDER BY records DESC, owner LIMIT 25""")
    return {"rules": rules, "by_owner": by_owner, "completeness": completeness_series(p), "gate": gate(p)}


def _finding_where(rule_id: str | None, owner: str | None, q: str | None) -> tuple[str, list]:
    clauses, args = [], []
    if rule_id:
        clauses.append("rule_id = ?")
        args.append(rule_id)
    if owner:
        clauses.append(f"coalesce(owner_upn, '{STEWARD}') = ?")
        args.append(owner)
    if q:
        clauses.append("(lower(record_id) LIKE ? OR lower(coalesce(detail, '')) LIKE ?)")
        args += [f"%{q.lower()}%"] * 2
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", args


def findings(
    p: Platform, rule_id: str | None, owner: str | None, q: str | None, page: int, page_size: int
) -> dict:
    where, args = _finding_where(rule_id, owner, q)
    total = p.scalar(f"SELECT count(*) FROM dq_finding{where}", args)
    rows = p.query(
        f"""SELECT rule_id, severity, record_type, record_id, detail,
                   coalesce(owner_upn, '{STEWARD}') AS owner, handling,
                   CAST(detected_at AS VARCHAR) AS detected_at
            FROM dq_finding{where} ORDER BY rule_id, record_id LIMIT ? OFFSET ?""",
        [*args, page_size, (page - 1) * page_size],
    )
    return {"total": total, "page": page, "page_size": page_size, "rows": rows}


def findings_all(p: Platform, rule_id: str | None, owner: str | None, q: str | None) -> list[dict]:
    where, args = _finding_where(rule_id, owner, q)
    return p.query(
        f"""SELECT rule_id, severity, record_type, record_id, detail,
                   coalesce(owner_upn, '{STEWARD}') AS owner, handling,
                   CAST(detected_at AS VARCHAR) AS detected_at
            FROM dq_finding{where} ORDER BY rule_id, record_id""",
        args,
    )
