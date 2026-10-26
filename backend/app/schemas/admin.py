"""Request bodies for the Administration API (FR-ADM-01..04, §10.2)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TargetRow(BaseModel):
    quarter: int = Field(ge=1, le=4)
    practice: str
    amount_usd: float = Field(ge=0)


class TargetVersionIn(BaseModel):
    fiscal_year: int
    note: str = Field(min_length=3, max_length=300, description="Why the plan changed")
    rows: list[TargetRow]


class ThresholdIn(BaseModel):
    on_track: float
    watch: float
    reason: str = Field(min_length=3, max_length=300)


class ReferenceIn(BaseModel):
    values: list[Any]
    reason: str = Field(min_length=3, max_length=300)


class ChangeRequestIn(BaseModel):
    metric_id: str | None = None
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=3, max_length=1000)


class AssessIn(BaseModel):
    note: str = Field(min_length=3, max_length=500, description="Impact assessment")


class DecideIn(BaseModel):
    decision: Literal["approve", "reject"]
    note: str = Field(min_length=3, max_length=500)
