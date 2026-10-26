"""/api/admin/* — FR-ADM-01..04 and metric change control (§10.2). Thin and admin-only.

Every write is audited with before/after detail and followed by a rebuild, so targets, thresholds
and reference data take effect everywhere (statuses, filters, bands) without a restart.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.api.deps import platform_dep, require_module
from app.domain.enums import Role
from app.domain.models import User
from app.platform import reference_sets as rs
from app.platform.admin_store import get_admin_store
from app.platform.audit import get_audit
from app.platform.db import Platform, rebuild
from app.schemas.admin import AssessIn, ChangeRequestIn, DecideIn, ReferenceIn, TargetVersionIn, ThresholdIn
from app.schemas.common import MetricResult
from app.semantic import definitions
from app.semantic.context import QueryContext
from app.semantic.filters import FilterParams
from app.semantic.metrics import adm

router = APIRouter(prefix="/api/admin", tags=["administration"])
AdminUser = Annotated[User, Depends(require_module("admin"))]
Plat = Annotated[Platform, Depends(platform_dep)]

IN_USE = {
    "verticals": "SELECT DISTINCT vertical FROM dim_account",
    "practices": "SELECT DISTINCT lead_practice FROM fact_opportunity",
    "platforms": "SELECT DISTINCT primary_platform FROM fact_opportunity",
}


def _audit(user: User, action: str, resource: str, detail: dict, status: int = 200) -> None:
    get_audit().record(
        upn=user.upn, role=user.role.value, action=action, resource=resource, status=status, detail=detail
    )


def _refresh() -> Platform:
    return rebuild()


# --- FR-ADM-01 targets ---------------------------------------------------------------------------
@router.get("/targets", summary="FR-ADM-01 Target versions and the active plan")
def targets(_: AdminUser, p: Plat) -> dict:
    active = p.query("""SELECT fiscal_year, max(target_version) AS version, sum(amount_usd) AS total_usd
           FROM mart_target GROUP BY 1 ORDER BY 1""")
    source = p.query(
        """SELECT target_version AS version, fiscal_year, CAST(max(loaded_at) AS VARCHAR) AS created_at,
                  sum(amount_usd) AS total_usd
           FROM raw_planning_target GROUP BY 1, 2 ORDER BY 2, 3"""
    )
    admin = {v["version"]: v for v in get_admin_store().target_versions()}
    versions = [
        {
            **s,
            "source": "admin" if s["version"] in admin else "planning",
            "note": admin.get(s["version"], {}).get("note"),
            "created_by": admin.get(s["version"], {}).get("created_by"),
            "active": any(a["version"] == s["version"] for a in active),
        }
        for s in source
    ]
    return {
        "active": active,
        "versions": versions,
        "practices": rs.read(p.query, "practices"),
        "grid": p.query(
            """SELECT fiscal_year, fiscal_quarter AS quarter, practice, amount_usd, target_version AS version
               FROM mart_target ORDER BY 1, 2, 3"""
        ),
    }


@router.get("/targets/{version}", summary="Rows of one target version")
def target_version(version: str, _: AdminUser, p: Plat) -> dict:
    rows = p.query(
        """SELECT quarter, practice, amount_usd FROM raw_planning_target
           WHERE target_version = ? ORDER BY 1, 2""",
        [version],
    )
    if not rows:
        raise HTTPException(404, f"Target version {version} not found.")
    return {"version": version, "rows": rows}


@router.post("/targets", status_code=201, summary="FR-ADM-01 Publish a new target version")
def create_target(body: TargetVersionIn, user: AdminUser, p: Plat) -> dict:
    practices = rs.read(p.query, "practices")
    got = {(r.quarter, r.practice) for r in body.rows}
    want = {(q, pr) for q in range(1, 5) for pr in practices}
    if len(got) != len(body.rows):
        raise HTTPException(422, "Each quarter and practice may appear only once.")
    if got != want:
        missing = sorted(want - got)[:3]
        extra = sorted(got - want)[:3]
        hint = f" Missing e.g. {missing}." if missing else ""
        hint += f" Unknown e.g. {extra}." if extra else ""
        raise HTTPException(422, f"Provide all 4 quarters for every practice ({len(want)} rows).{hint}")
    if body.fiscal_year not in {
        r["fiscal_year"] for r in p.query("SELECT DISTINCT fiscal_year FROM mart_target")
    }:
        raise HTTPException(422, f"No plan exists for FY{body.fiscal_year % 100}.")
    before = p.scalar("SELECT max(target_version) FROM mart_target WHERE fiscal_year = ?", [body.fiscal_year])
    rows = [r.model_dump() for r in body.rows]
    version = get_admin_store().add_target_version(body.fiscal_year, rows, body.note, user.upn)
    _refresh()
    _audit(
        user,
        "admin.target.create",
        f"/api/admin/targets/{version}",
        {
            "before": before,
            "after": version,
            "note": body.note,
            "total_usd": sum(r["amount_usd"] for r in rows),
        },
    )
    return {"version": version}


# --- FR-ADM-02 thresholds ------------------------------------------------------------------------
@router.get("/thresholds", summary="FR-ADM-02 RAG thresholds per metric")
def thresholds(_: AdminUser, p: Plat) -> list[dict]:
    history = get_admin_store().latest_thresholds()
    rows = p.query(
        "SELECT metric_id, direction, on_track, watch, unit, label, version FROM ref_threshold ORDER BY 1"
    )
    return [
        {
            **r,
            "name": definitions.METRICS.get(r["metric_id"], {}).get("name", r["metric_id"]),
            "reason": history.get(r["metric_id"], {}).get("reason"),
            "changed_by": history.get(r["metric_id"], {}).get("changed_by"),
        }
        for r in rows
    ]


@router.put("/thresholds/{metric_id}", summary="FR-ADM-02 Edit a threshold (versioned)")
def edit_threshold(metric_id: str, body: ThresholdIn, user: AdminUser, p: Plat) -> dict:
    cur = p.query("SELECT * FROM ref_threshold WHERE metric_id = ?", [metric_id])
    if not cur:
        raise HTTPException(404, f"No threshold is defined for {metric_id}.")
    c = cur[0]
    ok = body.on_track > body.watch if c["direction"] == "higher" else body.on_track < body.watch
    if not ok:
        want = "above" if c["direction"] == "higher" else "below"
        raise HTTPException(422, f"On-track must be {want} the watch value for {metric_id}.")
    version = get_admin_store().add_threshold(metric_id, body.on_track, body.watch, body.reason, user.upn)
    new = _refresh().query("SELECT * FROM ref_threshold WHERE metric_id = ?", [metric_id])[0]
    _audit(
        user,
        "admin.threshold.edit",
        f"/api/admin/thresholds/{metric_id}",
        {
            "before": {"on_track": c["on_track"], "watch": c["watch"], "version": c["version"]},
            "after": {"on_track": body.on_track, "watch": body.watch, "version": version},
            "reason": body.reason,
        },
    )
    return new


@router.get("/thresholds/{metric_id}/history", summary="Threshold version history")
def threshold_history(metric_id: str, _: AdminUser) -> list[dict]:
    return [
        {**h, "changed_at": h["changed_at"].isoformat()}
        for h in get_admin_store().threshold_history(metric_id)
    ]


# --- FR-ADM-03 reference data --------------------------------------------------------------------
@router.get("/reference", summary="FR-ADM-03 Reference sets")
def reference(_: AdminUser, p: Plat) -> list[dict]:
    latest = get_admin_store().latest_reference()
    out = []
    for key, meta in {**rs.EDITABLE, **rs.READ_ONLY}.items():
        out.append(
            {
                "key": key,
                **meta,
                "editable": key in rs.EDITABLE,
                "count": len(rs.read(p.query, key)),
                "version": latest.get(key, {}).get("version", 1),
            }
        )
    return out


@router.get("/reference/{key}", summary="FR-ADM-03 One reference set with history")
def reference_set(key: str, _: AdminUser, p: Plat) -> dict:
    meta = {**rs.EDITABLE, **rs.READ_ONLY}.get(key)
    if meta is None:
        raise HTTPException(404, f"Unknown reference set {key}.")
    return {
        "key": key,
        **meta,
        "editable": key in rs.EDITABLE,
        "values": rs.read(p.query, key),
        "history": [
            {**h, "changed_at": h["changed_at"].isoformat()} for h in get_admin_store().reference_history(key)
        ],
    }


@router.put("/reference/{key}", summary="FR-ADM-03 Replace an editable reference set (versioned)")
def edit_reference(key: str, body: ReferenceIn, user: AdminUser, p: Plat) -> dict:
    if key in rs.READ_ONLY:
        raise HTTPException(
            405, f"{rs.READ_ONLY[key]['label']} is read-only here. {rs.READ_ONLY[key]['description']}"
        )
    if key not in rs.EDITABLE:
        raise HTTPException(404, f"Unknown reference set {key}.")
    current = rs.read(p.query, key)
    try:
        values = rs.validate(key, body.values, current)
    except rs.InvalidReference as exc:
        raise HTTPException(422, str(exc)) from exc
    if key in IN_USE:
        used = {r[next(iter(r))] for r in p.query(IN_USE[key])}
        blocked = sorted(v for v in current if v not in values and v in used)
        if blocked:
            raise HTTPException(
                409,
                f"Cannot remove {', '.join(blocked)}: still in use. Re-tag those records in CRM first.",
            )
    version = get_admin_store().add_reference(key, values, body.reason, user.upn)
    _refresh()
    _audit(
        user,
        "admin.reference.edit",
        f"/api/admin/reference/{key}",
        {"before": current, "after": values, "version": version, "reason": body.reason},
    )
    return {"key": key, "version": version}


# --- FR-ADM-04 data quality ----------------------------------------------------------------------
@router.get("/dq", summary="FR-ADM-04 DQ console: rules, owners, completeness gate")
def dq(_: AdminUser, p: Plat) -> dict:
    return adm.dq_summary(p)


@router.get("/dq/completeness", response_model=MetricResult, summary="ADM-01 Mandatory-field completeness")
def completeness(user: AdminUser, p: Plat) -> MetricResult:
    return adm.adm_01(QueryContext(platform=p, params=FilterParams(), user=user))


@router.get("/dq/findings", summary="FR-ADM-04 Findings, filterable and paged")
def dq_findings(
    _: AdminUser,
    p: Plat,
    rule_id: str | None = None,
    owner: str | None = None,
    q: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 25,
) -> dict:
    return adm.findings(p, rule_id, owner, q, page, page_size)


@router.get("/dq/export", summary="FR-ADM-04 Export findings as CSV (audited)")
def dq_export(user: AdminUser, p: Plat, rule_id: str | None = None, owner: str | None = None) -> Response:
    rows = adm.findings_all(p, rule_id, owner, None)
    cols = ["rule_id", "severity", "record_type", "record_id", "detail", "owner", "handling", "detected_at"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cols)
    w.writerows([[r[c] for c in cols] for r in rows])
    _audit(
        user,
        "admin.dq.export",
        "/api/admin/dq/export",
        {"rule_id": rule_id, "owner": owner, "rows": len(rows)},
    )
    return Response(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="dq-findings.csv"'},
    )


# --- metric change control (§10.2) ---------------------------------------------------------------
def _next_window(today: date) -> str:
    first = date(today.year + (today.month == 12), today.month % 12 + 1, 1)
    return (first + timedelta(days=(7 - first.weekday()) % 7)).isoformat()


def _cr(request_id: int) -> dict:
    cr = get_admin_store().change_request(request_id)
    if cr is None:
        raise HTTPException(404, f"Change request {request_id} not found.")
    return cr


def _out(cr: dict) -> dict:
    return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in cr.items()}


@router.get("/change-requests", summary="Metric change requests")
def change_requests(_: AdminUser) -> list[dict]:
    return [_out(c) for c in get_admin_store().change_requests()]


@router.post("/change-requests", status_code=201, summary="Log a metric change request")
def create_change_request(body: ChangeRequestIn, user: AdminUser) -> dict:
    if body.metric_id and body.metric_id not in definitions.METRICS:
        raise HTTPException(422, f"{body.metric_id} is not a registered metric.")
    cr = get_admin_store().add_change_request(body.metric_id, body.title, body.description, user.upn)
    _audit(user, "admin.change.log", f"/api/admin/change-requests/{cr['id']}", {"title": body.title})
    return _out(cr)


@router.post("/change-requests/{request_id}/assess", summary="Add an impact assessment (GTM Lead, Sales Ops)")
def assess(request_id: int, body: AssessIn, user: AdminUser) -> dict:
    cr = _cr(request_id)
    if cr["status"] not in ("logged", "assessed"):
        raise HTTPException(409, f"A {cr['status']} request can no longer be assessed.")
    entries = [a for a in cr["assessments"] if a["role"] != user.role.value]
    entries.append(
        {"role": user.role.value, "by": user.upn, "note": body.note, "at": datetime.now(UTC).isoformat()}
    )
    both = {a["role"] for a in entries} >= {Role.GTM_LEAD.value, Role.SALES_OPS.value}
    out = get_admin_store().update_change_request(
        request_id, assessments=entries, status="assessed" if both else "logged"
    )
    _audit(user, "admin.change.assess", f"/api/admin/change-requests/{request_id}", {"note": body.note})
    return _out(out)


@router.post("/change-requests/{request_id}/decide", summary="Approve or reject (GTM Lead only)")
def decide(request_id: int, body: DecideIn, user: AdminUser) -> dict:
    if user.role != Role.GTM_LEAD:
        raise HTTPException(403, "Only the GTM Lead approves or rejects metric changes.")
    cr = _cr(request_id)
    if cr["status"] != "assessed":
        raise HTTPException(409, "Both the GTM Lead and Sales Ops must assess the change before a decision.")
    approved = body.decision == "approve"
    out = get_admin_store().update_change_request(
        request_id,
        status="approved" if approved else "rejected",
        decision_by=user.upn,
        decision_note=body.note,
        release_window=_next_window(datetime.now(UTC).date()) if approved else None,
    )
    _audit(
        user, f"admin.change.{body.decision}", f"/api/admin/change-requests/{request_id}", {"note": body.note}
    )
    return _out(out)


@router.post("/change-requests/{request_id}/release", summary="Mark an approved change as released")
def release(request_id: int, user: AdminUser) -> dict:
    cr = _cr(request_id)
    if cr["status"] != "approved":
        raise HTTPException(409, "Only an approved change can be released.")
    out = get_admin_store().update_change_request(request_id, status="released")
    _audit(user, "admin.change.release", f"/api/admin/change-requests/{request_id}", {})
    return _out(out)


# --- audit trail ---------------------------------------------------------------------------------
@router.get("/audit", summary="Audit trail of administration activity")
def audit_trail(_: AdminUser, limit: Annotated[int, Query(ge=1, le=500)] = 100) -> list[dict]:
    rows = [
        r
        for r in get_audit().recent(1000)
        if str(r["action"]).startswith("admin.") or str(r["resource"]).startswith("/api/admin")
    ][:limit]
    return [
        {**r, "ts": r["ts"].isoformat(), "detail": json.loads(r["detail"]) if r["detail"] else None}
        for r in rows
    ]
