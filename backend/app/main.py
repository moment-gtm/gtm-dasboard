"""FastAPI app: lifespan (build platform, start scheduler), CORS, audit middleware, routers."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    accounts,
    admin,
    alerts,
    auth,
    capacity,
    executive,
    exports,
    health,
    market_signals,
    mock_sources,
    offerings,
    opportunities,
    partners,
    pipeline,
    pursuits,
    reference,
)
from app.config import settings
from app.data import reference_data as ref
from app.platform.audit import get_audit
from app.platform.db import rebuild

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
PERSONA_UPN: dict[str, str] = {}
for p in ref.PERSONA_USERS:
    PERSONA_UPN.setdefault(p["role"].value, p["upn"])


@asynccontextmanager
async def lifespan(_: FastAPI):
    rebuild()  # bootstrap DuckDB: mock extracts -> raw -> conformed -> marts
    get_audit()
    scheduler = None
    if settings.enable_scheduler:
        from app.platform.scheduler import start_scheduler

        scheduler = start_scheduler()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Moment GTM Dashboard API (prototype)",
    version="0.1.0",
    description="Semantic layer + REST API for the Moment GTM Dashboard. Executive summary "
    "module (Step 1). Data is synthetic, served by mock source connectors.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def audit_exports(request: Request, call_next):
    """NFR-07: every data export is logged (view/PDF exports are logged by their route)."""
    response = await call_next(request)
    path = request.url.path
    denied_admin = path.startswith("/api/admin") and response.status_code in (401, 403)
    if denied_admin or (path.startswith("/api/exports/") and not path.endswith("/view")):
        role = request.headers.get("x-mock-role") or request.query_params.get("role") or "gtm_lead"
        get_audit().record(
            upn=PERSONA_UPN.get(role),
            role=role,
            action="admin.denied" if denied_admin else "export",
            resource=path,
            status=response.status_code,
            detail={"query": str(request.url.query)},
        )
    return response


for module in (
    auth,
    executive,
    pipeline,
    pursuits,
    offerings,
    accounts,
    partners,
    capacity,
    market_signals,
    alerts,
    opportunities,
    reference,
    health,
    exports,
    mock_sources,
    admin,
):
    app.include_router(module.router)
