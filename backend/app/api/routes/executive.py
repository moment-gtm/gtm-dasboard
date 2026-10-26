"""/api/executive/* — FR-EXE-01..05. Thin: all logic lives in semantic/metrics/exe.py."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ExecutiveContext
from app.schemas.common import DealsAttention, MetricResult
from app.semantic.metrics import exe

router = APIRouter(prefix="/api/executive", tags=["executive"])


@router.get("/runway", response_model=MetricResult, summary="FR-EXE-01 Bookings runway (EXE-07)")
def runway(ctx: ExecutiveContext) -> MetricResult:
    return exe.exe_07(ctx)


@router.get("/kpis", response_model=list[MetricResult], summary="FR-EXE-02 North-star KPIs (EXE-01..06)")
def kpis(ctx: ExecutiveContext) -> list[MetricResult]:
    return [fn(ctx) for fn in exe.KPI_FUNCTIONS]


@router.get(
    "/bookings-by-quarter", response_model=MetricResult, summary="FR-EXE-03 Bookings by quarter (EXE-08)"
)
def bookings_by_quarter(ctx: ExecutiveContext) -> MetricResult:
    return exe.exe_08(ctx)


@router.get(
    "/pipeline-by-vertical",
    response_model=MetricResult,
    summary="FR-EXE-04 Open pipeline by vertical (EXE-09)",
)
def pipeline_by_vertical(ctx: ExecutiveContext) -> MetricResult:
    return exe.exe_09(ctx)


@router.get(
    "/deals-attention", response_model=DealsAttention, summary="FR-EXE-05 Deals needing attention (EXE-10)"
)
def deals_attention(ctx: ExecutiveContext) -> DealsAttention:
    metric, rows, other = exe.exe_10(ctx)
    return DealsAttention(metric=metric, rows=rows, aggregated_other=other)
