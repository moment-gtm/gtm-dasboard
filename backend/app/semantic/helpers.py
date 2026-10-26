"""Shared calculation helpers: fiscal calendar, plan pace, coverage, formatting (Skill §semantic).

Fiscal year = calendar year (RSD 7.3). Elapsed share is measured in calendar days, counting
"today" as elapsed.
"""

from __future__ import annotations

from datetime import date, timedelta


def quarter_key(d: date) -> str:
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def quarter_label(key: str) -> str:
    year, q = key.split("-Q")
    return f"FY{int(year) % 100:02d} Q{q}"


def quarter_bounds(key: str) -> tuple[date, date]:
    year, q = int(key[:4]), int(key[-1])
    start = date(year, 3 * (q - 1) + 1, 1)
    end = date(year + 1, 1, 1) if q == 4 else date(year, 3 * q + 1, 1)
    return start, end - timedelta(days=1)


def next_quarter(key: str) -> str:
    year, q = int(key[:4]), int(key[-1])
    return f"{year + 1}-Q1" if q == 4 else f"{year}-Q{q + 1}"


def prev_quarter(key: str) -> str:
    year, q = int(key[:4]), int(key[-1])
    return f"{year - 1}-Q4" if q == 1 else f"{year}-Q{q - 1}"


def fiscal_quarters(fy: int) -> list[str]:
    return [f"{fy}-Q{q}" for q in range(1, 5)]


def quarters_between(start: date, end: date) -> list[str]:
    keys, k = [], quarter_key(start)
    while quarter_bounds(k)[0] <= end:
        keys.append(k)
        k = next_quarter(k)
    return keys


def last_n_quarters(today: date, n: int) -> list[str]:
    keys = [quarter_key(today)]
    while len(keys) < n:
        keys.insert(0, prev_quarter(keys[0]))
    return keys


def _overlap_days(a0: date, a1: date, b0: date, b1: date) -> int:
    lo, hi = max(a0, b0), min(a1, b1)
    return max(0, (hi - lo).days + 1)


def quarter_fraction(key: str, start: date, end: date) -> float:
    """Share of quarter `key` (calendar days) that falls inside [start, end]."""
    q0, q1 = quarter_bounds(key)
    return _overlap_days(q0, q1, start, end) / ((q1 - q0).days + 1)


def period_target(targets: dict[str, float], start: date, end: date) -> float:
    """Target for an arbitrary period: each quarter's target pro-rated by days covered."""
    return sum(t * quarter_fraction(k, start, end) for k, t in targets.items())


def plan_pace(targets: dict[str, float], start: date, end: date, today: date) -> float:
    """Plan pace (RSD 1.5): completed quarters in full plus the current quarter target × share of
    the quarter elapsed — generalised to any period by counting days up to today only."""
    return period_target(targets, start, min(end, today))


def elapsed_share(key: str, today: date) -> float:
    q0, q1 = quarter_bounds(key)
    return quarter_fraction(key, q0, min(q1, today))


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or not denominator or denominator <= 0:
        return None
    return numerator / denominator


def fmt_musd(value: float | None) -> str:
    """$M to one decimal (RSD §10.1)."""
    if value is None:
        return "n/a"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value) / 1e6:,.1f}M"


def fmt_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"
