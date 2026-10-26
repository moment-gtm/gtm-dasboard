"""Admin-editable reference sets (FR-ADM-03) — one definition shared by the ELT overlay (which
applies saved edits) and the admin API (which reads, validates and saves them).

Each editable set maps to the conformed ref_* / dim_* table it feeds, so a saved edit is picked up by
the semantic layer on the next rebuild without code changes. Sets owned by another system (offering
catalogue, strategic accounts, architect roster) are read-only here.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Query = Callable[[str], list[dict]]

NAME_SETS = {"verticals": "dim_vertical", "practices": "dim_practice", "platforms": "dim_platform"}

EDITABLE: dict[str, dict[str, str]] = {
    "verticals": {"label": "Verticals", "description": "Industry verticals used by the global filter."},
    "practices": {"label": "Practices", "description": "Practices that own targets and offerings."},
    "platforms": {"label": "Platforms", "description": "Technology platforms used by the global filter."},
    "stage_probability": {
        "label": "Stage probabilities",
        "description": "Standard probability per pipeline stage, used for weighted pipeline (DQ-07).",
    },
    "ageing_buckets": {
        "label": "Ageing buckets",
        "description": "Days-in-stage buckets for the pipeline ageing heatmap (PIP-02).",
    },
    "size_bands": {
        "label": "Deal-size bands",
        "description": "Deal-size bands for the size distribution (PIP-05).",
    },
    "settings": {
        "label": "Metric settings",
        "description": "Configurable defaults, e.g. the EXE-10 value threshold and EXE-04 goal multiple.",
    },
}
READ_ONLY: dict[str, dict[str, str]] = {
    "offerings": {
        "label": "Offering catalogue",
        "description": "Managed in the SharePoint offering list (REF-OFF); edit it at the source.",
    },
    "strategic_accounts": {
        "label": "Strategic accounts",
        "description": "Strategic flag comes from CRM (SRC-01); edit it in the CRM account record.",
    },
    "architect_roster": {
        "label": "Architect roster",
        "description": "People and titles come from Microsoft Entra ID (SRC-16).",
    },
    "campaigns": {
        "label": "Marketing campaigns",
        "description": "Campaign catalogue synced from marketing automation (SRC-10).",
    },
    "analyst_evaluations": {
        "label": "Analyst evaluations",
        "description": "Analyst placement register synced from SharePoint (SRC-15).",
    },
}

_SQL = {
    "stage_probability": "SELECT stage, probability FROM ref_stage_probability ORDER BY stage_order",
    "ageing_buckets": """SELECT bucket_key AS key, label, min_days, max_days, review
                         FROM ref_bucket ORDER BY sort_order""",
    "size_bands": "SELECT band_key AS key, label, min_usd, max_usd FROM ref_size_band ORDER BY sort_order",
    "settings": "SELECT key, value FROM ref_setting ORDER BY key",
    "offerings": "SELECT offering_id, name, family FROM ref_offering ORDER BY family, name",
    "strategic_accounts": """SELECT account_id, name, vertical, geography FROM dim_account
                             WHERE strategic ORDER BY name""",
    "architect_roster": "SELECT upn, name, title FROM dim_person ORDER BY name",
    "campaigns": """SELECT campaign_id, campaign_name, channel, practice, platform, status
                    FROM dim_campaign ORDER BY start_date DESC""",
    "analyst_evaluations": """SELECT eval_id, firm, report_series, current_placement,
                              prior_placement, direction FROM fact_analyst_eval
                              ORDER BY published_date DESC""",
}


class InvalidReference(ValueError):
    """The submitted set breaks a rule; the message says which and how to fix it."""


def read(query: Query, key: str) -> list:
    if key in NAME_SETS:
        return [r["name"] for r in query(f"SELECT name FROM {NAME_SETS[key]} ORDER BY sort_order")]
    return query(_SQL[key])


def _names(values: Any) -> list[str]:
    if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
        raise InvalidReference("Provide a non-empty list of names.")
    names = [v.strip() for v in values]
    if any(not n or len(n) > 60 for n in names):
        raise InvalidReference("Names must be 1–60 characters.")
    if len({n.lower() for n in names}) != len(names):
        raise InvalidReference("Names must be unique.")
    return names


def _same_keys(values: Any, current: list[dict], key_field: str) -> dict[str, Any]:
    if not isinstance(values, list):
        raise InvalidReference("Provide a list of rows.")
    got = [v.get(key_field) for v in values if isinstance(v, dict)]
    want = [r[key_field] for r in current]
    if sorted(map(str, got)) != sorted(want):
        raise InvalidReference(
            f"Rows cannot be added or removed here; the {key_field}s are: {', '.join(want)}."
        )
    return {v[key_field]: v for v in values}


def _number(row: dict, field: str, low: float = 0.0, high: float | None = None) -> float:
    v = row.get(field)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise InvalidReference(f"{field} must be a number.")
    if v < low or (high is not None and v > high):
        raise InvalidReference(
            f"{field} must be between {low:g} and {high:g}."
            if high is not None
            else f"{field} must be {low:g} or more."
        )
    return float(v)


def _bands(values: Any, lo: str, hi: str, step: int, extra: tuple[str, ...]) -> list[dict]:
    """Contiguous bands: start at 0, each starts where the previous ended, only the last is open."""
    if not isinstance(values, list) or not values:
        raise InvalidReference("Provide at least one band.")
    out: list[dict] = []
    for i, v in enumerate(values):
        if (
            not isinstance(v, dict)
            or not str(v.get("key", "")).strip()
            or not str(v.get("label", "")).strip()
        ):
            raise InvalidReference("Every band needs a key and a label.")
        last = i == len(values) - 1
        low = _number(v, lo)
        high = v.get(hi)
        if last and high is not None:
            raise InvalidReference(f"The last band must be open-ended (leave {hi} empty).")
        if not last:
            high = _number(v, hi)
            if high <= low:
                raise InvalidReference(f"{hi} must be greater than {lo} in band '{v['label']}'.")
        expected = 0 if i == 0 else (out[-1][hi] + step)
        if low != expected:
            raise InvalidReference(
                f"Band '{v['label']}' must start at {expected:g} so bands have no gap or overlap."
            )
        row = {"key": str(v["key"]).strip(), "label": str(v["label"]).strip(), lo: low, hi: high}
        row.update({f: bool(v.get(f)) for f in extra})
        out.append(row)
    if len({r["key"] for r in out}) != len(out):
        raise InvalidReference("Band keys must be unique.")
    return out


def validate(key: str, values: Any, current: list) -> list:
    """Return the normalised payload for `key` or raise InvalidReference."""
    if key in NAME_SETS:
        return _names(values)
    if key == "stage_probability":
        by = _same_keys(values, current, "stage")
        out = [
            {"stage": r["stage"], "probability": _number(by[r["stage"]], "probability", 0, 1)}
            for r in current
        ]
        open_stages = [r["probability"] for r in out[:5]]
        if open_stages != sorted(open_stages):
            raise InvalidReference(
                "A deal's probability cannot fall as it advances from Identify to Negotiate."
            )
        return out
    if key == "settings":
        by = _same_keys(values, current, "key")
        return [{"key": r["key"], "value": _number(by[r["key"]], "value")} for r in current]
    if key == "ageing_buckets":
        return _bands(values, "min_days", "max_days", 1, ("review",))
    if key == "size_bands":
        return _bands(values, "min_usd", "max_usd", 0, ())
    raise InvalidReference(f"'{key}' is not an editable reference set.")


def apply(conn, key: str, payload: list) -> None:
    """Replace the conformed table behind `key` with `payload` (used by the ELT overlay)."""
    if key in NAME_SETS:
        table = NAME_SETS[key]
        conn.execute(f"DELETE FROM {table}")
        conn.executemany(f"INSERT INTO {table} VALUES (?, ?)", [(v, i) for i, v in enumerate(payload)])
    elif key == "stage_probability":
        for r in payload:
            conn.execute(
                "UPDATE ref_stage_probability SET probability = ? WHERE stage = ?",
                [r["probability"], r["stage"]],
            )
    elif key == "settings":
        for r in payload:
            conn.execute("UPDATE ref_setting SET value = ? WHERE key = ?", [r["value"], r["key"]])
    elif key == "ageing_buckets":
        conn.execute("DELETE FROM ref_bucket")
        conn.executemany(
            "INSERT INTO ref_bucket VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    r["key"],
                    r["label"],
                    int(r["min_days"]),
                    None if r["max_days"] is None else int(r["max_days"]),
                    r["review"],
                    i,
                )
                for i, r in enumerate(payload)
            ],
        )
    elif key == "size_bands":
        conn.execute("DELETE FROM ref_size_band")
        conn.executemany(
            "INSERT INTO ref_size_band VALUES (?, ?, ?, ?, ?)",
            [(r["key"], r["label"], r["min_usd"], r["max_usd"], i) for i, r in enumerate(payload)],
        )
