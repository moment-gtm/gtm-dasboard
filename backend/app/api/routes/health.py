"""/api/health — per-source freshness (FR-GEN-09, NFR-02) and data-quality counts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import platform_dep
from app.platform.db import Platform
from app.schemas.common import Health, SourceHealth
from app.semantic.freshness import iso, source_health

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=Health)
def health(platform: Annotated[Platform, Depends(platform_dep)]) -> Health:
    sources = [SourceHealth(**s) for s in source_health(platform)]
    stale = any(s.status != "fresh" for s in sources)
    return Health(
        status="degraded" if stale else "ok",
        as_of_date=platform.as_of_date.isoformat(),
        built_at=iso(platform.built_at) or "",
        stale=stale,
        sources=sources,
    )


@router.get("/api/dq/summary", summary="DQ findings by rule (full console arrives in Step 4)")
def dq_summary(platform: Annotated[Platform, Depends(platform_dep)]) -> list[dict]:
    return platform.query("""SELECT rule_id, description, handling, count(*) AS records FROM dq_finding
           GROUP BY ALL ORDER BY rule_id""")
