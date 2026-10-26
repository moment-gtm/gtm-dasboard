"""Filtered target comparison & pro-rating (FR-GEN-04, Shared doc §6.1).

Planning (SRC-02) provides targets at quarter × practice grain.
- Exact slice: no filter finer than practice and no narrowing row scope -> stored targets.
- Otherwise pro-rate the practice-level (or total) parent target by the slice's pipeline share
  and label it pro-rated. Pipeline share = TCV of open + Closed Won opportunities closing in
  the fiscal year inside the slice ÷ the same for the parent population.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.semantic.context import QueryContext
from app.semantic.filters import dimension_clause
from app.semantic.helpers import fmt_pct


@dataclass
class TargetSlice:
    by_quarter: dict[str, float]
    available: bool
    prorated: bool
    basis: str
    shares: dict[int, float] = field(default_factory=dict)

    def total(self) -> float:
        return sum(self.by_quarter.values())


def _stored(ctx: QueryContext, quarters: list[str]) -> tuple[dict[str, float], str | None]:
    marks = ", ".join("?" * len(quarters))
    args: list = list(quarters)
    practice_sql = "TRUE"
    if ctx.params.practice:
        practice_sql = f"practice IN ({', '.join('?' * len(ctx.params.practice))})"
        args.extend(ctx.params.practice)
    rows = ctx.platform.query(
        f"""SELECT quarter_key, sum(amount_usd) AS amount, max(target_version) AS version
            FROM mart_target WHERE quarter_key IN ({marks}) AND {practice_sql}
            GROUP BY quarter_key""",
        args,
    )
    versions = sorted({r["version"] for r in rows})
    return {r["quarter_key"]: float(r["amount"]) for r in rows}, ", ".join(versions) or None


def pipeline_share(ctx: QueryContext, fiscal_year: int) -> float:
    cond = "o.stage_group IN ('open', 'won') AND year(o.close_date) = ?"
    slice_tcv = ctx.value(ctx.where(cond, args=[fiscal_year]), "coalesce(sum(o.tcv_usd), 0)")
    parent_sql, parent_args = dimension_clause(ctx.params, "o", only={"practice"})
    parent_tcv = ctx.platform.scalar(
        f"SELECT coalesce(sum(o.tcv_usd), 0) FROM mart_opportunity o WHERE {parent_sql} AND {cond}",
        [*parent_args, fiscal_year],
    )
    return float(slice_tcv) / float(parent_tcv) if parent_tcv else 0.0


def target_slice(ctx: QueryContext, quarters: list[str]) -> TargetSlice:
    stored, versions = _stored(ctx, quarters)
    if not stored:
        return TargetSlice(
            {},
            available=False,
            prorated=False,
            basis="No planning target loaded (SRC-02 Planning unavailable)",
        )
    grain = "practice" if ctx.params.practice else "total"
    needs_prorate = ctx.params.has_sub_target_filters() or ctx.scope.narrows_rows
    if not needs_prorate:
        return TargetSlice(
            stored,
            available=True,
            prorated=False,
            basis=f"Planned target ({versions}) at quarter × {grain} grain",
        )
    shares = {fy: pipeline_share(ctx, fy) for fy in sorted({int(q[:4]) for q in quarters})}
    by_q = {q: amount * shares[int(q[:4])] for q, amount in stored.items()}
    share_txt = ", ".join(f"FY{fy % 100:02d} {fmt_pct(s)}" for fy, s in shares.items())
    reason = (
        "your data scope"
        if ctx.scope.narrows_rows and not ctx.params.has_sub_target_filters()
        else "the filtered slice"
    )
    return TargetSlice(
        by_q,
        available=True,
        prorated=True,
        shares=shares,
        basis=(
            f"Pro-rated: {grain}-level planned target ({versions}) × pipeline share of {reason} "
            f"({share_txt}). No target is stored below quarter × practice grain."
        ),
    )
