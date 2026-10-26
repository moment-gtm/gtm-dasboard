"""QueryContext bundles platform + filters + caller so every metric builds predicates the same way:
global filters (filters.py) AND row scope (rls.py) AND the metric's own condition."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.domain.models import User
from app.platform.db import Platform
from app.semantic.filters import FilterParams, Period, dimension_clause, resolve_period
from app.semantic.rls import RowScope, scope_for


@dataclass
class QueryContext:
    platform: Platform
    params: FilterParams
    user: User
    today: date = field(init=False)
    period: Period = field(init=False)
    scope: RowScope = field(init=False)

    def __post_init__(self) -> None:
        self.today = self.platform.as_of_date
        self.period = resolve_period(self.params, self.today)
        self.scope = scope_for(self.user)

    def where(
        self,
        *conditions: str,
        args: list | None = None,
        detail: bool = False,
        dims: bool = True,
        rls: bool = True,
        alias: str = "o",
    ) -> tuple[str, list]:
        """Combine filters + RLS + metric conditions. `conditions` use `?` placeholders bound
        by `args`, in order, after the filter and scope arguments."""
        parts, out = [], []
        if dims:
            sql, a = dimension_clause(self.params, alias)
            parts.append(sql)
            out.extend(a)
        if rls:
            scope = scope_for(self.user, alias)
            parts.append(scope.row_sql)
            out.extend(scope.row_args)
            if detail:
                parts.append(scope.detail_sql)
                out.extend(scope.detail_args)
        parts.extend(f"({c})" for c in conditions)
        out.extend(args or [])
        return " AND ".join(parts), out

    def rows(
        self, sql_where: tuple[str, list], select: str = "*", table: str = "mart_opportunity", tail: str = ""
    ) -> list[dict]:
        where, args = sql_where
        return self.platform.query(f"SELECT {select} FROM {table} o WHERE {where} {tail}", args)

    def value(
        self, sql_where: tuple[str, list], select: str, table: str = "mart_opportunity"
    ) -> float | None:
        where, args = sql_where
        return self.platform.scalar(f"SELECT {select} FROM {table} o WHERE {where}", args)
