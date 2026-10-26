"""Offerings source data (synthetic): AI validation register (SRC-13), knowledge repository
(SRC-12), asset development tracker (SRC-17), proposal-asset usage (SRC-03) and the annual
build plan (SRC-02).

Own seeded RNG (seed + 401), so every previously generated value is unchanged.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from app.data import reference_data as ref

ASSET_TYPES = ("Demo", "Accelerator", "Solution")
N_KB_ASSETS = 24
N_BUILDS = 30
RELEASED, IN_DEV, PLANNED = "Released", "In development", "Planned"
CROSS_INDUSTRY = "Cross-industry"
MISSING_ID_BUILDS = 3  # released rows without Asset ID / type (DQ-09)
BUILD_PLAN = {1: 5, 2: 5, 3: 5, 4: 5}  # planned releases per quarter of the current FY
BUILD_STATUSES = [RELEASED] * 15 + [IN_DEV] * 9 + [PLANNED] * 6
VALIDATED_SHARE = 0.85


def _validation(opps: list[dict], rng: random.Random, today: date) -> list[dict]:
    rows = []
    for o in opps:
        if not (o["AI_Led__c"] and o["Validation_ID__c"]):
            continue
        validated = rng.random() < VALIDATED_SHARE
        created = date.fromisoformat(o["CreatedDate"])
        rows.append(
            {
                "Validation_Id": o["Validation_ID__c"],
                "CRM_Opportunity_Id": o["Id"],
                "Status": "Validated" if validated else "In review",
                "Reviewed_On": (
                    min(created + timedelta(days=rng.randint(5, 40)), today).isoformat()
                    if validated
                    else None
                ),
            }
        )
    return rows


def _kb_assets(rng: random.Random, today: date) -> list[dict]:
    names = [o["name"] for o in ref.OFFERINGS]
    rows = []
    for i in range(1, N_KB_ASSETS + 1):
        kind = ASSET_TYPES[i % len(ASSET_TYPES)]
        offering = names[i % len(names)]
        rows.append(
            {
                "Asset_Id": f"KB-{i:03d}",
                "Title": f"{offering} {kind} {i}",
                "Asset_Type": kind,
                "Offering": offering,
                "Practice": ref.PRACTICES[i % len(ref.PRACTICES)],
                "Platform": ref.PLATFORMS[i % len(ref.PLATFORMS)],
                "Vertical": CROSS_INDUSTRY if rng.random() < 0.3 else rng.choice(ref.VERTICALS),
                "Last_Refreshed": (today - timedelta(days=rng.randint(15, 330))).isoformat(),
            }
        )
    return rows


def _proposal_assets(bids: list[dict], opp_ids: set[str], kb: list[dict], rng: random.Random) -> list[dict]:
    weights = [rng.random() ** 2 + 0.03 for _ in kb]  # a few popular assets, a long tail
    rows = []
    for b in bids:
        if b["Decision"] != "bid" or b["CRM_Opportunity_Id"] not in opp_ids:
            continue
        chosen: set[int] = set()
        for _ in range(rng.choices([0, 1, 2, 3], [0.25, 0.3, 0.28, 0.17])[0]):
            chosen.add(rng.choices(range(len(kb)), weights)[0])
        for idx in sorted(chosen):
            rows.append(
                {
                    "Pursuit_Id": b["Pursuit_Id"],
                    "CRM_Opportunity_Id": b["CRM_Opportunity_Id"],
                    "Asset_Id": kb[idx]["Asset_Id"],
                    "Used_On": b["RFP_Received"],
                }
            )
    return rows


def _builds(rng: random.Random, kb: list[dict], today: date) -> list[dict]:
    fy = today.year
    q_now = (today.month - 1) // 3 + 1
    released_ids = iter(rng.sample([a["Asset_Id"] for a in kb], BUILD_STATUSES.count(RELEASED)))
    rows = []
    n_released = 0
    for i, status in enumerate(BUILD_STATUSES, start=1):
        kind = ASSET_TYPES[i % len(ASSET_TYPES)]
        start = release = None
        if status == RELEASED:
            release = date(fy, 1, 1) + timedelta(
                days=rng.randint(10, max(11, (today - date(fy, 1, 1)).days - 1))
            )
            start = release - timedelta(days=rng.randint(28, 150))
            quarter = (release.month - 1) // 3 + 1
        elif status == IN_DEV:
            start = today - timedelta(days=rng.randint(7, 90))
            quarter = rng.choice([q for q in (q_now, min(q_now + 1, 4)) if q])
        else:
            quarter = rng.randint(min(q_now + 1, 4), 4)
        asset_id = None
        if status == RELEASED:
            n_released += 1
            asset_id = next(released_ids)
            if n_released <= MISSING_ID_BUILDS:  # incomplete tracker rows: no Asset ID, no type
                asset_id, kind = None, None
        rows.append(
            {
                "Build_Id": f"BLD-{i:03d}",
                "Asset_Id": asset_id,
                "Asset_Type": kind,
                "Name": f"{rng.choice(ref.OFFERINGS)['name']} build {i}",
                "Practice": ref.PRACTICES[i % len(ref.PRACTICES)],
                "Platform": ref.PLATFORMS[(i * 3) % len(ref.PLATFORMS)],
                "Vertical": CROSS_INDUSTRY if i % 4 == 0 else ref.VERTICALS[i % len(ref.VERTICALS)],
                "Status": status,
                "Target_Quarter": f"{fy}-Q{quarter}",
                "Start_Date": start.isoformat() if start else None,
                "Released_Date": release.isoformat() if release else None,
            }
        )
    return rows


def generate(opps: list[dict], bids: list[dict], seed: int, today: date) -> dict[str, list[dict]]:
    rng = random.Random(seed + 401)
    kb = _kb_assets(rng, today)
    return {
        "validation_records": _validation(opps, rng, today),
        "kb_assets": kb,
        "proposal_assets": _proposal_assets(bids, {o["Id"] for o in opps}, kb, rng),
        "asset_builds": _builds(rng, kb, today),
        "build_plan": [
            {"fiscal_year": today.year, "quarter": q, "planned_releases": n} for q, n in BUILD_PLAN.items()
        ],
    }
