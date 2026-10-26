"""Solutions Capacity source data (synthetic): architect roster and opportunity-team roles
(SRC-06 / CRM), pursuit timesheets (SRC-07), finance cost rates and project financials (SRC-04),
pricing versions (SRC-05) and bid quality reviews (SRC-03).

Own seeded RNG (seed + 503), so every previously generated value is unchanged.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

from app.data import reference_data as ref
from app.domain.enums import Stage

ARCHITECT_ROLE = "Solution Architect"
BID_MANAGER_ROLE = "Bid Manager"
COST_RATES = {ARCHITECT_ROLE: 95.0, BID_MANAGER_ROLE: 70.0}
N_ARCHITECTS = 50
N_BID_MANAGERS = 6
# Open-pursuit load per architect: a few over capacity (5+), some stretched (4), the rest healthy.
OVER_CAPACITY_LOADS = (6, 5, 5)
STRETCHED_COUNT = 8
ARCHITECT_STAGES = (Stage.QUALIFY, Stage.PROPOSE, Stage.ORALS)
HOURS_PER_MUSD = 260.0  # pursuit effort per $1M of TCV
ARCHITECT_HOURS_SHARE = 0.6
MARGIN_EROSION_PTS = (0.5, 7.5)  # delivery margin vs the margin priced at bid
DELIVERY_LAG_DAYS = 90  # delivery margin exists only for deals closed at least a quarter ago
QUALITY_MEAN = {"won": 4.1, "lost": 3.2}

FIRST = ("Aarav", "Maya", "Liam", "Sofia", "Noah", "Priya", "Lucas", "Elena", "Ethan", "Zara")
LAST = ("Rao", "Silva", "Novak", "Okafor", "Lindqvist", "Tanaka", "Moreau", "Khan", "Brennan", "Duarte")


def _usd(o: dict) -> float:
    return o["Amount"] * ref.PLAN_FX_TO_USD[o["CurrencyIsoCode"]]


def _roster(rng: random.Random) -> list[dict]:
    names = [f"{f} {last}" for last in LAST for f in FIRST]
    rng.shuffle(names)
    rows = [
        {"Resource_Id": f"RES-A{i + 1:03d}", "Name": names[i], "Role": ARCHITECT_ROLE}
        for i in range(N_ARCHITECTS)
    ]
    rows += [
        {"Resource_Id": f"RES-B{i + 1:03d}", "Name": names[N_ARCHITECTS + i], "Role": BID_MANAGER_ROLE}
        for i in range(N_BID_MANAGERS)
    ]
    return rows


def _architect_slots(n_deals: int, rng: random.Random) -> list[int]:
    """Architect index per open deal, with a deterministic load profile."""
    stretched = [4] * STRETCHED_COUNT
    healthy_n = N_ARCHITECTS - len(OVER_CAPACITY_LOADS) - STRETCHED_COUNT
    rest = max(0, n_deals - sum(OVER_CAPACITY_LOADS) - sum(stretched))
    base, extra = divmod(rest, healthy_n)
    loads = [*OVER_CAPACITY_LOADS, *stretched, *[base + (1 if i < extra else 0) for i in range(healthy_n)]]
    slots = [i for i, load in enumerate(loads) for _ in range(load)]
    rng.shuffle(slots)
    return slots


def _team(opps: list[dict], bids: dict[str, dict], roster: list[dict], rng: random.Random) -> list[dict]:
    architects = [r for r in roster if r["Role"] == ARCHITECT_ROLE]
    managers = [r for r in roster if r["Role"] == BID_MANAGER_ROLE]
    open_deals = [o for o in opps if o["StageName"] in ARCHITECT_STAGES]
    slots = _architect_slots(len(open_deals), rng)
    rows: list[dict] = []
    for o, slot in zip(open_deals, slots):
        rows.append(
            {
                "Opportunity_Id": o["Id"],
                "Resource_Id": architects[slot]["Resource_Id"],
                "Role": ARCHITECT_ROLE,
            }
        )
    for o in opps:
        if o["Id"] in bids:
            if o["StageName"] in (Stage.CLOSED_WON, Stage.CLOSED_LOST):
                a, m = rng.choice(architects), rng.choice(managers)
                rows.append(
                    {"Opportunity_Id": o["Id"], "Resource_Id": a["Resource_Id"], "Role": ARCHITECT_ROLE}
                )
                rows.append(
                    {"Opportunity_Id": o["Id"], "Resource_Id": m["Resource_Id"], "Role": BID_MANAGER_ROLE}
                )
    return rows


def _timesheets(
    opps: dict[str, dict], bids: dict[str, dict], team: list[dict], rng: random.Random
) -> list[dict]:
    by_opp: dict[str, list[dict]] = {}
    for t in team:
        by_opp.setdefault(t["Opportunity_Id"], []).append(t)
    rows: list[dict] = []
    for opp_id, members in by_opp.items():
        o, bid = opps[opp_id], bids.get(opp_id)
        if bid is None or o["StageName"] not in (Stage.CLOSED_WON, Stage.CLOSED_LOST):
            continue
        start = date.fromisoformat(bid["RFP_Received"])
        end = date.fromisoformat(bid["RFP_Submitted"] or o["CloseDate"])
        weeks = max(1, math.ceil((end - start).days / 7))
        total = _usd(o) / 1e6 * HOURS_PER_MUSD * rng.uniform(0.7, 1.3)
        for m in members:
            share = ARCHITECT_HOURS_SHARE if m["Role"] == ARCHITECT_ROLE else 1 - ARCHITECT_HOURS_SHARE
            for w in range(weeks):
                rows.append(
                    {
                        "Entry_Id": f"TS-{len(rows) + 1:06d}",
                        "Opportunity_Id": opp_id,
                        "Resource_Id": m["Resource_Id"],
                        "Week_Start": (start + timedelta(days=7 * w)).isoformat(),
                        "Hours": round(total * share / weeks, 1),
                    }
                )
    return rows


def _margins(opps: list[dict], today: date, rng: random.Random) -> tuple[list[dict], list[dict]]:
    pricing, financials = [], []
    for o in opps:
        if o["StageName"] != Stage.CLOSED_WON:
            continue
        bid_margin = round(rng.uniform(26.0, 38.0), 1)
        pricing.append({"Opportunity_Id": o["Id"], "Version": "Final bid", "Bid_Margin_Pct": bid_margin})
        if date.fromisoformat(o["CloseDate"]) <= today - timedelta(days=DELIVERY_LAG_DAYS):
            erosion = rng.uniform(*MARGIN_EROSION_PTS)
            financials.append(
                {
                    "Opportunity_Id": o["Id"],
                    "Delivery_Margin_Pct": round(bid_margin - erosion, 1),
                    "As_Of_Month": today.isoformat()[:7],
                }
            )
    return pricing, financials


def _quality(opps: list[dict], bids: dict[str, dict], rng: random.Random) -> list[dict]:
    rows = []
    for o in opps:
        outcome = {Stage.CLOSED_WON: "won", Stage.CLOSED_LOST: "lost"}.get(o["StageName"])
        bid = bids.get(o["Id"])
        if outcome is None or bid is None or bid["Decision"] != "bid":
            continue
        score = round(min(5.0, max(1.0, rng.gauss(QUALITY_MEAN[outcome], 0.6))), 1)
        rows.append(
            {
                "Pursuit_Id": bid["Pursuit_Id"],
                "CRM_Opportunity_Id": o["Id"],
                "Quality_Score": score,
                "Reviewed_On": bid["RFP_Submitted"] or bid["RFP_Received"],
            }
        )
    return rows


def generate(opps: list[dict], bids: list[dict], seed: int, today: date) -> dict[str, list[dict]]:
    rng = random.Random(seed + 503)
    bid_by_opp = {b["CRM_Opportunity_Id"]: b for b in bids}
    opp_by_id = {o["Id"]: o for o in opps}
    roster = _roster(rng)
    team = _team(opps, bid_by_opp, roster, rng)
    pricing, financials = _margins(opps, today, rng)
    return {
        "resources": roster,
        "opportunity_team": team,
        "timesheets": _timesheets(opp_by_id, bid_by_opp, team, rng),
        "cost_rates": [{"Role": r, "Rate_USD_Hour": v} for r, v in COST_RATES.items()],
        "pricing_versions": pricing,
        "project_financials": financials,
        "quality_reviews": _quality(opps, bid_by_opp, rng),
    }
