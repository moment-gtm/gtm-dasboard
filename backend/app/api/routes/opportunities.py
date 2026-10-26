"""/api/opportunities — drill-down list behind any aggregate (FR-GEN-06), RLS on rows."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import CurrentUser, Filters, guard_restricted, platform_dep
from app.domain.models import User
from app.platform.db import Platform
from app.schemas.common import OpportunityPage
from app.semantic import definitions
from app.semantic.context import QueryContext
from app.semantic.metrics import cap, drill, exe, mkt, pip, pur

router = APIRouter(prefix="/api", tags=["opportunities"])

METRIC_MODULE = {
    "EXE": "executive",
    "PIP": "pipeline",
    "PUR": "pursuits",
    "OFF": "offerings",
    "ACC": "accounts",
    "PAR": "partners",
    "CAP": "solutions_capacity",
    "MKT": "market_signals",
}
SORT_COLUMNS = {
    "tcv": "o.tcv_usd",
    "close_date": "o.close_date",
    "days_in_stage": "o.days_in_stage",
    "name": "o.name",
    "account_name": "o.account_name",
    "stage": "o.stage",
}
MAX_EXPORT_ROWS = 5000


def check_metric_access(user: User, metric_id: str | None) -> None:
    if metric_id is None:
        if not user.modules:
            raise HTTPException(status_code=403, detail="No dashboard access")
        return
    module = METRIC_MODULE.get(metric_id.split("-")[0])
    if module is None:
        raise HTTPException(status_code=404, detail=f"Unknown metric {metric_id}")
    if not user.can_access(module):
        raise HTTPException(status_code=403, detail=f"{user.role_label} cannot drill into {metric_id}")
    if definitions.is_restricted(metric_id):
        guard_restricted(user, metric_id, "drilldown")


def drill_context(
    platform: Platform, params, user: User, metric_id: str | None, segment: str | None
) -> tuple[QueryContext, str, list, str]:
    check_metric_access(user, metric_id)
    ctx = QueryContext(platform=platform, params=params, user=user)
    try:
        module = {
            "PIP": pip,
            "PUR": pur,
            "OFF": drill,
            "ACC": drill,
            "PAR": drill,
            "CAP": cap,
            "MKT": mkt,
        }.get((metric_id or "")[:3], exe)
        cond, args, title = module.drill_condition(ctx, metric_id, segment)
    except exe.InvalidSegment as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ctx, cond, args, title


def search_condition(cond: str, args: list, search: str | None) -> tuple[str, list]:
    if not search:
        return cond, args
    like = f"%{search.lower()}%"
    return (
        f"({cond}) AND (lower(o.name) LIKE ? OR lower(o.account_name) LIKE ? "
        "OR lower(o.opportunity_id) LIKE ? OR lower(o.owner_name) LIKE ?)",
        [*args, like, like, like, like],
    )


@router.get("/opportunities", response_model=OpportunityPage)
def opportunities(
    params: Filters,
    user: CurrentUser,
    platform: Annotated[Platform, Depends(platform_dep)],
    metric_id: str | None = None,
    segment: str | None = None,
    sort: Literal["tcv", "close_date", "days_in_stage", "name", "account_name", "stage"] = "tcv",
    order: Literal["asc", "desc"] = "desc",
    search: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 25,
) -> OpportunityPage:
    ctx, cond, args, title = drill_context(platform, params, user, metric_id, segment)
    cond, args = search_condition(cond, args, search)
    where, wargs = ctx.where(cond, args=args, detail=True)
    totals = platform.query(
        f"SELECT count(*) AS n, coalesce(sum(o.tcv_usd), 0) AS tcv FROM mart_opportunity o WHERE {where}",
        wargs,
    )[0]
    rows = exe.select_rows(
        ctx,
        cond,
        args,
        order_by=f"{SORT_COLUMNS[sort]} {order.upper()} NULLS LAST",
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return OpportunityPage(
        metric_id=metric_id,
        segment=segment,
        title=title,
        total_count=totals["n"],
        total_tcv=float(totals["tcv"]),
        page=page,
        page_size=page_size,
        rows=rows,
        aggregated_other=exe.aggregated_other(ctx, cond, args),
    )
