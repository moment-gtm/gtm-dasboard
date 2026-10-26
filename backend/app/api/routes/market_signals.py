"""/api/market/* — FR-MKT-01..04. Thin: all logic lives in semantic/metrics/mkt.py."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import MarketSignalsContext
from app.schemas.common import MetricResult
from app.semantic.metrics import mkt

router = APIRouter(prefix="/api/market", tags=["market signals"])


@router.get(
    "/thought-leadership",
    response_model=MetricResult,
    summary="FR-MKT-01 Thought leadership output & engagement (MKT-01)",
)
def thought_leadership(ctx: MarketSignalsContext) -> MetricResult:
    return mkt.mkt_01(ctx)


@router.get(
    "/workshop-funnel",
    response_model=MetricResult,
    summary="FR-MKT-02 Discovery workshop conversion (MKT-02)",
)
def workshop_funnel(ctx: MarketSignalsContext) -> MetricResult:
    return mkt.mkt_02(ctx)


@router.get(
    "/campaign-sourced",
    response_model=MetricResult,
    summary="FR-MKT-03 Campaign-sourced pipeline (MKT-03)",
)
@router.get(
    "/campaign-pipeline",
    response_model=MetricResult,
    summary="FR-MKT-03 Campaign-sourced pipeline alias (MKT-03)",
)
def campaign_sourced(ctx: MarketSignalsContext) -> MetricResult:
    return mkt.mkt_03(ctx)


@router.get(
    "/analyst-positioning",
    response_model=MetricResult,
    summary="FR-MKT-04 Analyst positioning (MKT-04)",
)
def analyst_positioning(ctx: MarketSignalsContext) -> MetricResult:
    return mkt.mkt_04(ctx)
