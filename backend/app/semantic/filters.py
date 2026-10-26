"""Global filters (FR-GEN-02/03). The only place filters are translated into predicates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from pydantic import BaseModel, model_validator

from app.semantic import helpers as h

# Filter name -> mart column. Practice filters the lead practice (target grain, SRC-02).
DIMENSION_COLUMNS: dict[str, str] = {
    "vertical": "vertical",
    "practice": "lead_practice",
    "platform": "primary_platform",
    "account": "account_id",
    "client_partner": "client_partner_upn",
    "deal_source": "lead_source",
    "geography": "geography",
}
# Dimensions at which planning targets exist (quarter × practice, RSD OQ-04 assumption).
TARGET_GRAIN_DIMENSIONS = {"practice"}


class FilterParams(BaseModel):
    period: Literal["fytd", "quarter", "qtd", "custom"] = "fytd"
    quarter: str | None = None  # "2026-Q2" when period = quarter
    start: date | None = None  # custom range
    end: date | None = None
    vertical: list[str] = []
    practice: list[str] = []
    platform: list[str] = []
    account: list[str] = []
    client_partner: list[str] = []
    deal_source: list[str] = []
    geography: list[str] = []

    @model_validator(mode="after")
    def _check_period(self) -> FilterParams:
        if self.period == "quarter":
            if (
                not self.quarter
                or len(self.quarter) != 7
                or self.quarter[4:6] != "-Q"
                or self.quarter[-1] not in "1234"
            ):
                raise ValueError("period=quarter needs quarter=YYYY-Qn")
        if self.period == "custom":
            if not self.start or not self.end:
                raise ValueError("period=custom needs start and end")
            if self.start > self.end:
                raise ValueError("start must be on or before end")
        return self

    def active_dimensions(self) -> dict[str, list[str]]:
        return {k: getattr(self, k) for k in DIMENSION_COLUMNS if getattr(self, k)}

    def has_sub_target_filters(self) -> bool:
        """True when a filter is finer than the planning grain -> target must be pro-rated."""
        return any(k not in TARGET_GRAIN_DIMENSIONS for k in self.active_dimensions())


@dataclass(frozen=True)
class Period:
    kind: str
    start: date
    end: date
    label: str
    fiscal_year: int
    # Span the target covers: the whole FY for FYTD, the whole quarter for QTD (RSD EXE-01:
    # target for the period; status uses plan pace = that target pro-rated to today).
    target_end: date | None = None

    @property
    def target_through(self) -> date:
        return self.target_end or self.end

    @property
    def quarters(self) -> list[str]:
        return h.quarters_between(self.start, self.target_through)

    def to_info(self) -> dict:
        return {
            "kind": self.kind,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "label": self.label,
            "fiscal_year": self.fiscal_year,
        }


def resolve_period(params: FilterParams, today: date) -> Period:
    fy = today.year
    if params.period == "quarter":
        start, end = h.quarter_bounds(params.quarter)  # type: ignore[arg-type]
        return Period("quarter", start, end, h.quarter_label(params.quarter), start.year)
    if params.period == "qtd":
        key = h.quarter_key(today)
        start, q_end = h.quarter_bounds(key)
        return Period("qtd", start, today, f"{h.quarter_label(key)} QTD", fy, target_end=q_end)
    if params.period == "custom":
        assert params.start and params.end
        return Period(
            "custom",
            params.start,
            params.end,
            f"{params.start:%d %b %Y} – {params.end:%d %b %Y}",
            params.start.year,
        )
    return Period("fytd", date(fy, 1, 1), today, f"FY{fy % 100:02d} YTD", fy, target_end=date(fy, 12, 31))


def dimension_clause(
    params: FilterParams, alias: str = "o", only: set[str] | None = None
) -> tuple[str, list]:
    parts, args = [], []
    for name, values in params.active_dimensions().items():
        if only is not None and name not in only:
            continue
        parts.append(f"{alias}.{DIMENSION_COLUMNS[name]} IN ({', '.join('?' * len(values))})")
        args.extend(values)
    return (" AND ".join(parts) or "TRUE"), args
