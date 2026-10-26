"""/api/offerings/* — FR-OFF-01..05. Thin: all logic lives in semantic/metrics/off.py."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import OfferingsContext
from app.schemas.common import MetricResult
from app.semantic.metrics import off

router = APIRouter(prefix="/api/offerings", tags=["offerings"])


@router.get("/by-offering", response_model=MetricResult, summary="FR-OFF-01 Pipeline and wins (OFF-01)")
def by_offering(ctx: OfferingsContext) -> MetricResult:
    return off.off_01(ctx)


@router.get("/attach-rate", response_model=MetricResult, summary="FR-OFF-02 Attach rate (OFF-02)")
def attach_rate(ctx: OfferingsContext) -> MetricResult:
    return off.off_02(ctx)


@router.get("/ai-validation", response_model=MetricResult, summary="FR-OFF-03 AI-led validation (OFF-03)")
def ai_validation(ctx: OfferingsContext) -> MetricResult:
    return off.off_03(ctx)


@router.get("/asset-reuse", response_model=MetricResult, summary="FR-OFF-04 Asset reuse (OFF-04)")
def asset_reuse(ctx: OfferingsContext) -> MetricResult:
    return off.off_04(ctx)


@router.get("/asset-build", response_model=MetricResult, summary="FR-OFF-05 Assets developed (OFF-05)")
def asset_build(ctx: OfferingsContext) -> MetricResult:
    return off.off_05(ctx)
