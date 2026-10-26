"""/api/accounts/* — FR-ACC-01..05. Thin: all logic lives in semantic/metrics/acc.py."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import AccountsContext, platform_dep
from app.platform.db import Platform
from app.schemas.common import MetricResult, OpportunityPage
from app.semantic.context import QueryContext
from app.semantic.filters import FilterParams
from app.semantic.metrics import acc, exe
from app.semantic.rls import scope_for

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/penetration", response_model=MetricResult, summary="FR-ACC-01 Penetration matrix (ACC-01)")
def penetration(ctx: AccountsContext) -> MetricResult:
    return acc.acc_01(ctx)


@router.get("/whitespace", response_model=MetricResult, summary="FR-ACC-02 Whitespace summary (ACC-02)")
def whitespace(ctx: AccountsContext) -> MetricResult:
    return acc.acc_02(ctx)


@router.get("/expansion", response_model=MetricResult, summary="FR-ACC-03 Expansion vs new logo (ACC-03)")
def expansion(ctx: AccountsContext) -> MetricResult:
    return acc.acc_03(ctx)


@router.get("/plan-health", response_model=MetricResult, summary="FR-ACC-04 Account-plan health (ACC-04)")
def plan_health(ctx: AccountsContext) -> MetricResult:
    return acc.acc_04(ctx)


@router.get(
    "/{account_id}/opportunities",
    response_model=OpportunityPage,
    summary="FR-ACC-05 All opportunities for one account (detail panel)",
)
def account_opportunities(
    account_id: str,
    ctx: AccountsContext,
    platform: Annotated[Platform, Depends(platform_dep)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 100,
) -> OpportunityPage:
    scope = scope_for(ctx.user, "a")
    account = platform.query(
        f"SELECT a.name FROM dim_account a WHERE a.account_id = ? AND {scope.row_sql}",
        [account_id, *scope.row_args],
    )
    if not account:  # unknown or outside the caller's assigned accounts: do not reveal which
        raise HTTPException(status_code=404, detail="Account not found")
    # The panel shows the whole account, so the global dashboard filters are not applied here.
    detail_ctx = QueryContext(platform=platform, params=FilterParams(), user=ctx.user)
    cond, args = "o.account_id = ?", [account_id]
    where, wargs = detail_ctx.where(cond, args=args, detail=True)
    totals = platform.query(
        f"SELECT count(*) AS n, coalesce(sum(o.tcv_usd), 0) AS tcv FROM mart_opportunity o WHERE {where}",
        wargs,
    )[0]
    rows = exe.select_rows(
        detail_ctx, cond, args, order_by="o.close_date DESC", limit=page_size, offset=(page - 1) * page_size
    )
    return OpportunityPage(
        metric_id="ACC-01",
        segment=account_id,
        title=account[0]["name"],
        total_count=totals["n"],
        total_tcv=float(totals["tcv"]),
        page=page,
        page_size=page_size,
        rows=rows,
        aggregated_other=exe.aggregated_other(detail_ctx, cond, args),
    )
