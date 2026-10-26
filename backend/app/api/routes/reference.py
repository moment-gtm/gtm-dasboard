"""/api/reference/* and /api/me — filter options, metric metadata, thresholds, personas."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, platform_dep
from app.config import settings
from app.data import reference_data as ref
from app.domain.models import User
from app.platform import reference_sets as rs
from app.platform.db import Platform
from app.schemas.common import FilterOptions, MetricMeta, Option, Persona
from app.semantic import definitions
from app.semantic import helpers as h
from app.semantic.freshness import iso, last_success
from app.semantic.rls import describe, resolve_user

router = APIRouter(tags=["reference"])
SOURCE_KEYS = {s["source_id"]: s["key"] for s in ref.SOURCES}


def _persona(platform: Platform, user: User) -> Persona:
    rd = next(r for r in ref.ROLES if r["role"] == user.role)
    return Persona(
        role=user.role.value,
        label=user.role_label,
        name=user.name,
        upn=user.upn,
        scope=user.scope.value,
        scope_detail=describe(user),
        modules=list(user.modules),
        restricted=user.restricted,
        default_view=rd["default_view"],
    )


@router.get("/api/me", response_model=Persona)
def me(user: CurrentUser, platform: Annotated[Platform, Depends(platform_dep)]) -> Persona:
    return _persona(platform, user)


@router.get("/api/reference/roles", response_model=list[Persona])
def roles(user: CurrentUser, platform: Annotated[Platform, Depends(platform_dep)]) -> list[Persona]:
    """A user holds one persona. Only the caller's own is listed unless the demo persona switcher
    is explicitly enabled (GTM_ENABLE_PERSONA_SWITCHER=1)."""
    if not settings.enable_persona_switcher:
        return [_persona(platform, user)]
    return [_persona(platform, resolve_user(platform, r["role"].value)) for r in ref.ROLES]


def _opts(values: list[str]) -> list[Option]:
    return [Option(value=v, label=v) for v in values]


@router.get("/api/reference/filters", response_model=FilterOptions)
def filters(user: CurrentUser, platform: Annotated[Platform, Depends(platform_dep)]) -> FilterOptions:
    from app.semantic.rls import scope_for

    today = platform.as_of_date
    fy = today.year
    scope = scope_for(user)
    # Account / client-partner options only within the caller's row scope (RLS on outputs).
    accounts = platform.query(
        f"""SELECT DISTINCT o.account_id, o.account_name, o.client_partner_upn
            FROM mart_opportunity o WHERE {scope.row_sql} AND {scope.detail_sql}
            ORDER BY o.account_name""",
        [*scope.row_args, *scope.detail_args],
    )
    cp_upns = {a["client_partner_upn"] for a in accounts}
    people = {p["upn"]: p["name"] for p in platform.query("SELECT upn, name FROM dim_person")}
    quarters = [q for y in (fy - 1, fy) for q in h.fiscal_quarters(y)]
    return FilterOptions(
        fiscal_year=fy,
        today=today.isoformat(),
        current_quarter=h.quarter_key(today),
        periods=[
            Option(value="fytd", label=f"FY{fy % 100:02d} year to date"),
            Option(value="quarter", label="Individual quarter"),
            Option(value="qtd", label=f"Current quarter to date ({h.quarter_label(h.quarter_key(today))})"),
            Option(value="custom", label="Custom date range"),
        ],
        quarters=[
            Option(value=q, label=h.quarter_label(q)) for q in quarters if h.quarter_bounds(q)[0] <= today
        ],
        verticals=_opts(rs.read(platform.query, "verticals")),
        practices=_opts(rs.read(platform.query, "practices")),
        platforms=_opts(rs.read(platform.query, "platforms")),
        accounts=[Option(value=a["account_id"], label=a["account_name"]) for a in accounts],
        client_partners=[Option(value=u, label=people.get(u, u)) for u in sorted(cp_upns)],
        deal_sources=_opts(ref.LEAD_SOURCES),
        geographies=_opts(ref.GEOGRAPHIES),
    )


def _meta(platform: Platform, metric_id: str) -> MetricMeta:
    m = definitions.get(metric_id)
    refreshes = [last_success(platform, SOURCE_KEYS[s]) for s in m["sources"] if s in SOURCE_KEYS]
    known = [r for r in refreshes if r is not None]
    return MetricMeta(
        metric_id=metric_id,
        name=m["name"],
        definition=m["definition"],
        calculation=m["calculation"],
        sources=definitions.sources_for(metric_id),
        owner=m["owner"],
        refresh=m["refresh"],
        dimensions=m["dimensions"],
        period_sensitive=m["period_sensitive"],
        goal_label=m["goal_label"],
        # Last refresh of a multi-source metric = its oldest source.
        last_refresh=iso(min(known)) if known and len(known) == len(refreshes) else None,
    )


@router.get("/api/reference/metrics", response_model=list[MetricMeta])
def metrics(platform: Annotated[Platform, Depends(platform_dep)]) -> list[MetricMeta]:
    return [_meta(platform, mid) for mid in definitions.METRICS]


@router.get("/api/reference/metrics/{metric_id}", response_model=MetricMeta)
def metric(metric_id: str, platform: Annotated[Platform, Depends(platform_dep)]) -> MetricMeta:
    try:
        return _meta(platform, metric_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/reference/thresholds")
def thresholds(platform: Annotated[Platform, Depends(platform_dep)]) -> list[dict]:
    return platform.query(
        "SELECT metric_id, direction, on_track, watch, unit, label FROM ref_threshold ORDER BY 1"
    )
