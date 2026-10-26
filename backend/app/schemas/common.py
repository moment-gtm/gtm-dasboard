"""Shared API contracts. Mirrored by `frontend/src/api/types.ts` — change both together."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

StatusValue = Literal["on_track", "watch", "off_track"]
Unit = Literal["usd", "x", "pct", "days", "count"]


class PeriodInfo(BaseModel):
    kind: Literal["fytd", "quarter", "qtd", "custom"]
    start: str
    end: str
    label: str  # e.g. "FY26 YTD", "FY26 Q2", "FY26 Q3 QTD"
    fiscal_year: int


class SparkPoint(BaseModel):
    label: str  # "FY26 Q2"
    value: float | None
    partial: bool = False  # current quarter (QTD)


class MetricResult(BaseModel):
    """Metric-module contract (skill): value, target, status, breakdown + traceability."""

    metric_id: str
    name: str
    unit: Unit
    value: float | None
    target: float | None = None
    target_prorated: bool = False  # FR-GEN-04
    target_basis: str | None = None  # plain-language basis of the target / pro-rating
    goal: float | None = None  # goal in the same unit as `value`
    goal_label: str | None = None
    attainment: float | None = None  # ratio banded when status is not banded on `value`
    status: StatusValue | None = None
    status_basis: str | None = None
    breakdown: list[dict[str, Any]] = Field(default_factory=list)
    sparkline: list[SparkPoint] = Field(default_factory=list)
    narrative: str | None = None
    period: PeriodInfo
    as_of: str | None = None  # last successful refresh of the primary source (ISO)
    sources: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class AggregatedOther(BaseModel):
    """Rows outside the caller's detail scope, shown only as an aggregate (practice-lead RLS)."""

    count: int
    tcv: float
    note: str


class OpportunityRow(BaseModel):
    opportunity_id: str
    name: str
    account_id: str
    account_name: str
    vertical: str
    geography: str
    lead_practice: str
    primary_platform: str
    stage: str
    tcv: float
    weighted_tcv: float
    std_probability: float
    rep_probability: float | None
    created_date: str
    close_date: str
    days_in_stage: int | None
    offering: str | None
    offering_class: str
    lead_source: str
    partner: str | None
    owner_name: str
    flag: str | None = None  # Ageing / Stalled / Past close date (EXE-10)
    crm_url: str


class OpportunityPage(BaseModel):
    metric_id: str | None
    segment: str | None
    title: str
    total_count: int
    total_tcv: float
    page: int
    page_size: int
    rows: list[OpportunityRow]
    aggregated_other: AggregatedOther | None = None


class DealsAttention(BaseModel):
    metric: MetricResult
    rows: list[OpportunityRow]
    aggregated_other: AggregatedOther | None = None


class Option(BaseModel):
    value: str
    label: str


class FilterOptions(BaseModel):
    fiscal_year: int
    today: str
    current_quarter: str
    periods: list[Option]
    quarters: list[Option]
    verticals: list[Option]
    practices: list[Option]
    platforms: list[Option]
    accounts: list[Option]
    client_partners: list[Option]
    deal_sources: list[Option]
    geographies: list[Option]


class SourceRef(BaseModel):
    source_id: str
    name: str


class MetricMeta(BaseModel):
    metric_id: str
    name: str
    definition: str
    calculation: str
    sources: list[SourceRef]
    owner: str
    refresh: str
    dimensions: list[str]
    period_sensitive: bool
    goal_label: str | None
    last_refresh: str | None


class SourceHealth(BaseModel):
    source_id: str
    key: str
    name: str
    cadence: str
    last_success: str | None
    last_attempt: str | None
    status: Literal["fresh", "stale", "failed"]
    rows: int
    message: str | None


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    as_of_date: str
    built_at: str
    stale: bool
    sources: list[SourceHealth]


class Persona(BaseModel):
    role: str
    label: str
    name: str
    upn: str
    scope: str
    scope_detail: str
    modules: list[str]
    restricted: bool
    default_view: str


class ExportAudit(BaseModel):
    view: str
    format: Literal["pdf", "pptx"]
