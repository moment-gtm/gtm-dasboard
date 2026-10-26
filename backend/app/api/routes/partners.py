"""/api/partners/* — FR-PAR-01..03. Thin: all logic lives in semantic/metrics/par.py."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import PartnersContext
from app.schemas.common import MetricResult
from app.semantic.metrics import par

router = APIRouter(prefix="/api/partners", tags=["partners"])


@router.get("/pipeline", response_model=MetricResult, summary="FR-PAR-01 Pipeline by partner (PAR-01)")
def pipeline(ctx: PartnersContext) -> MetricResult:
    return par.par_01(ctx)


@router.get("/co-sell", response_model=MetricResult, summary="FR-PAR-02 Co-sell performance (PAR-02)")
def co_sell(ctx: PartnersContext) -> MetricResult:
    return par.par_02(ctx)


@router.get("/certifications", response_model=MetricResult, summary="FR-PAR-03 Certifications (PAR-03)")
def certifications(ctx: PartnersContext) -> MetricResult:
    return par.par_03(ctx)
