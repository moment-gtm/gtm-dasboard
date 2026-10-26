"""/api/pipeline/* — FR-PIP-01..06. Thin: all logic lives in semantic/metrics/pip.py.

The opportunity register (PIP-06) is served by /api/opportunities?metric_id=PIP-06.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import PipelineContext
from app.schemas.common import MetricResult
from app.semantic.metrics import pip

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/funnel", response_model=MetricResult, summary="FR-PIP-01 Stage funnel + conversion (PIP-01)")
def funnel(ctx: PipelineContext) -> MetricResult:
    return pip.pip_01(ctx)


@router.get("/ageing", response_model=MetricResult, summary="FR-PIP-02 Ageing heatmap (PIP-02)")
def ageing(ctx: PipelineContext) -> MetricResult:
    return pip.pip_02(ctx)


@router.get("/by-practice", response_model=MetricResult, summary="FR-PIP-03 Pipeline by practice (PIP-03)")
def by_practice(ctx: PipelineContext) -> MetricResult:
    return pip.pip_03(ctx)


@router.get("/by-platform", response_model=MetricResult, summary="FR-PIP-03 Pipeline by platform (PIP-04)")
def by_platform(ctx: PipelineContext) -> MetricResult:
    return pip.pip_04(ctx)


@router.get(
    "/size-distribution", response_model=MetricResult, summary="FR-PIP-04 Deal-size distribution (PIP-05)"
)
def size_distribution(ctx: PipelineContext) -> MetricResult:
    return pip.pip_05(ctx)


@router.get("/register", response_model=MetricResult, summary="FR-PIP-05 Register summary (PIP-06)")
def register(ctx: PipelineContext) -> MetricResult:
    return pip.pip_06(ctx)


@router.get(
    "/stage-movement", response_model=MetricResult, summary="FR-PIP-06 Week-over-week movement (PIP-07)"
)
def stage_movement(ctx: PipelineContext) -> MetricResult:
    return pip.pip_07(ctx)
