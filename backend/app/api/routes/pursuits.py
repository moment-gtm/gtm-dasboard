"""/api/pursuits/* — FR-PUR-01..05. Thin: all logic lives in semantic/metrics/pur.py.

FR-PUR-05 (margin at bid vs delivery, PUR-06) is restricted: the route is role-gated and audited.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import MarginContext, PursuitsContext
from app.schemas.common import MetricResult
from app.semantic.metrics import pur

router = APIRouter(prefix="/api/pursuits", tags=["pursuits"])


@router.get("/win-rate", response_model=MetricResult, summary="FR-PUR-01 Win rate by quarter (PUR-01)")
def win_rate(ctx: PursuitsContext) -> MetricResult:
    return pur.pur_01(ctx)


@router.get("/loss-reasons", response_model=MetricResult, summary="FR-PUR-02 Loss reasons (PUR-02)")
def loss_reasons(ctx: PursuitsContext) -> MetricResult:
    return pur.pur_02(ctx)


@router.get("/source-mix", response_model=MetricResult, summary="FR-PUR-03 Deal source mix (PUR-03)")
def source_mix(ctx: PursuitsContext) -> MetricResult:
    return pur.pur_03(ctx)


@router.get("/bid-discipline", response_model=MetricResult, summary="FR-PUR-04 Bid discipline (PUR-04)")
def bid_discipline(ctx: PursuitsContext) -> MetricResult:
    return pur.pur_04(ctx)


@router.get("/orals-conversion", response_model=MetricResult, summary="FR-PUR-04 Orals conversion (PUR-05)")
def orals_conversion(ctx: PursuitsContext) -> MetricResult:
    return pur.pur_05(ctx)


@router.get(
    "/margin",
    response_model=MetricResult,
    summary="FR-PUR-05 Margin at bid vs delivery (PUR-06) — restricted roles only",
)
def margin(ctx: MarginContext) -> MetricResult:
    return pur.pur_06(ctx)
