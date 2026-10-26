"""/api/capacity/* — FR-CAP-01..04. Thin: all logic lives in semantic/metrics/cap.py.

Cost of sale (CAP-03) is restricted: it 403s for other roles and every attempt is audited.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CapacityContext, CostOfSaleContext
from app.schemas.common import MetricResult
from app.semantic.metrics import cap

router = APIRouter(prefix="/api/capacity", tags=["solutions capacity"])


@router.get("/architect-load", response_model=MetricResult, summary="FR-CAP-01 Architect load (CAP-01)")
def architect_load(ctx: CapacityContext) -> MetricResult:
    return cap.cap_01(ctx)


@router.get("/rfp-turnaround", response_model=MetricResult, summary="FR-CAP-02 RFP turnaround (CAP-02)")
def rfp_turnaround(ctx: CapacityContext) -> MetricResult:
    return cap.cap_02(ctx)


@router.get(
    "/cost-of-sale",
    response_model=MetricResult,
    summary="FR-CAP-03 Cost of sale (CAP-03) — restricted roles only",
)
def cost_of_sale(ctx: CostOfSaleContext) -> MetricResult:
    return cap.cap_03(ctx)


@router.get("/quality-scores", response_model=MetricResult, summary="FR-CAP-04 Proposal quality (CAP-04)")
def quality_scores(ctx: CapacityContext) -> MetricResult:
    return cap.cap_04(ctx)
