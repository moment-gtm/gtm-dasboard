"""On track / Watch / Off track banding (FR-GEN-05). Bands come from `ref_threshold`, never code."""

from __future__ import annotations

from app.domain.enums import Status
from app.platform.db import Platform

_cache: dict[int, dict[str, dict]] = {}


def thresholds(platform: Platform) -> dict[str, dict]:
    key = id(platform)
    if key not in _cache:
        _cache.clear()
        _cache[key] = {r["metric_id"]: r for r in platform.query("SELECT * FROM ref_threshold")}
    return _cache[key]


def band(platform: Platform, metric_id: str, value: float | None) -> Status | None:
    t = thresholds(platform).get(metric_id)
    if t is None or value is None:
        return None
    if t["direction"] == "higher":
        if value >= t["on_track"]:
            return Status.ON_TRACK
        return Status.WATCH if value >= t["watch"] else Status.OFF_TRACK
    if value <= t["on_track"]:
        return Status.ON_TRACK
    return Status.WATCH if value <= t["watch"] else Status.OFF_TRACK


def threshold(platform: Platform, metric_id: str) -> dict | None:
    return thresholds(platform).get(metric_id)


def setting(platform: Platform, key: str, default: float) -> float:
    v = platform.scalar("SELECT value FROM ref_setting WHERE key = ?", [key])
    return default if v is None else float(v)
