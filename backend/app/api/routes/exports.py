"""/api/exports/* — widget data to CSV/Excel, view-to-PDF audit (FR-GEN-08).

Exports are computed through the same semantic layer as the widgets, so RLS applies to them
(AC-03). Every export is written to audit_log by the audit middleware (NFR-07).
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from openpyxl import Workbook

from app.api.deps import CurrentUser, Filters, guard_restricted, platform_dep
from app.api.routes.opportunities import MAX_EXPORT_ROWS, METRIC_MODULE, drill_context
from app.domain.models import User
from app.platform.audit import get_audit
from app.platform.db import Platform
from app.schemas.common import ExportAudit, MetricResult
from app.semantic.context import QueryContext
from app.semantic.metrics import acc, cap, exe, mkt, off, par, pip, pur

router = APIRouter(prefix="/api/exports", tags=["exports"])

WIDGETS = {
    "EXE-07": exe.exe_07,
    "EXE-08": exe.exe_08,
    "EXE-09": exe.exe_09,
    **{fn.__name__.upper().replace("_", "-"): fn for fn in exe.KPI_FUNCTIONS},
    **{k: v for k, v in pip.FUNCTIONS.items() if k != "PIP-06"},
    **pur.FUNCTIONS,
    **off.FUNCTIONS,
    **acc.FUNCTIONS,
    **par.FUNCTIONS,
    **cap.FUNCTIONS,
    **mkt.FUNCTIONS,
}


def _header(metric: MetricResult | None, title: str, user: User) -> list[list]:
    rows = [
        ["Moment GTM Dashboard export"],
        ["Title", title],
        ["Generated (UTC)", datetime.now(UTC).strftime("%Y-%m-%d %H:%M")],
        ["Role / scope", f"{user.role_label} — {user.name}"],
    ]
    if metric:
        rows += [
            ["Metric", f"{metric.metric_id} {metric.name}"],
            ["Period", metric.period.label],
            ["Sources", ", ".join(metric.sources)],
        ]
        if metric.target_prorated:
            rows.append(["Target", "PRO-RATED — " + (metric.target_basis or "")])
    return rows + [[]]


def _flatten(row: dict) -> dict:
    out: dict = {}
    for k, v in row.items():
        if isinstance(v, dict):
            out.update({f"{k}_{sk}": sv for sk, sv in v.items()})
        else:
            out[k] = v
    return out


def _metric_table(metric: MetricResult) -> tuple[list[str], list[list]]:
    if metric.breakdown:
        flat = [_flatten(r) for r in metric.breakdown]
        cols = list(flat[0].keys())
        return cols, [[r.get(c) for c in cols] for r in flat]
    cols = ["metric_id", "name", "value", "unit", "target", "goal", "attainment", "status", "status_basis"]
    return cols, [[getattr(metric, c) for c in cols]]


def _file(fmt: str, name: str, header: list[list], cols: list[str], rows: list[list]) -> Response:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerows(header)
        w.writerow(cols)
        w.writerows(rows)
        return Response(
            buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{name}_{stamp}.csv"'},
        )
    wb = Workbook()
    ws = wb.active
    ws.title = name[:31]
    for r in header:
        ws.append(r)
    ws.append(cols)
    for r in rows:
        ws.append(r)
    out = io.BytesIO()
    wb.save(out)
    return Response(
        out.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{name}_{stamp}.xlsx"'},
    )


ROW_COLS = [
    "opportunity_id",
    "name",
    "account_name",
    "vertical",
    "lead_practice",
    "primary_platform",
    "stage",
    "tcv",
    "weighted_tcv",
    "std_probability",
    "rep_probability",
    "close_date",
    "days_in_stage",
    "offering_class",
    "offering",
    "lead_source",
    "owner_name",
    "flag",
    "crm_url",
]


@router.get("/widget")
def export_widget(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: CurrentUser,
    metric_id: str,
    format: Literal["csv", "xlsx"] = "csv",
) -> Response:
    module = METRIC_MODULE.get(metric_id.split("-")[0])
    if module is None:
        raise HTTPException(status_code=404, detail=f"No exportable widget {metric_id}")
    if not user.can_access(module):
        raise HTTPException(status_code=403, detail=f"{user.role_label} cannot export {metric_id}")
    ctx = QueryContext(platform=platform, params=params, user=user)
    restricted = {**pur.RESTRICTED_FUNCTIONS, **cap.RESTRICTED_FUNCTIONS}
    if metric_id in restricted:
        guard_restricted(user, metric_id, "export")
        metric = restricted[metric_id](ctx)
        cols, data = _metric_table(metric)
        return _file(format, metric_id, _header(metric, metric.name, user), cols, data)
    if metric_id == "EXE-10":
        metric, rows, _ = exe.exe_10(ctx)
        data = [[getattr(r, c) for c in ROW_COLS] for r in rows]
        return _file(format, metric_id, _header(metric, metric.name, user), ROW_COLS, data)
    if metric_id == "PIP-06":
        metric = pip.pip_06(ctx)
        rows = exe.select_rows(ctx, pip.OPEN, [], limit=MAX_EXPORT_ROWS)
        data = [[getattr(r, c) for c in ROW_COLS] for r in rows]
        return _file(format, metric_id, _header(metric, metric.name, user), ROW_COLS, data)
    fn = WIDGETS.get(metric_id)
    if fn is None:
        raise HTTPException(status_code=404, detail=f"No exportable widget {metric_id}")
    metric = fn(ctx)
    cols, data = _metric_table(metric)
    return _file(format, metric_id, _header(metric, metric.name, user), cols, data)


@router.get("/opportunities")
def export_opportunities(
    params: Filters,
    user: CurrentUser,
    platform: Annotated[Platform, Depends(platform_dep)],
    metric_id: str | None = None,
    segment: str | None = None,
    format: Literal["csv", "xlsx"] = "csv",
) -> Response:
    ctx, cond, args, title = drill_context(platform, params, user, metric_id, segment)
    rows = exe.select_rows(ctx, cond, args, limit=MAX_EXPORT_ROWS)
    data = [[getattr(r, c) for c in ROW_COLS] for r in rows]
    return _file(
        format, f"{metric_id or 'opportunities'}_drilldown", _header(None, title, user), ROW_COLS, data
    )


@router.post("/view", status_code=204)
def export_view(body: ExportAudit, request: Request, user: CurrentUser) -> Response:
    """The browser renders the PDF (print); this records the export in audit_log."""
    if not user.can_access(body.view):
        raise HTTPException(status_code=403, detail=f"No access to {body.view}")
    get_audit().record(
        upn=user.upn,
        role=user.role.value,
        action=f"export_view_{body.format}",
        resource=body.view,
        status=204,
        detail={"query": str(request.url.query)},
    )
    return Response(status_code=204)
