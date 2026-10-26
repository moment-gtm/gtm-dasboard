"""Pursuits & Wins source data: CRM loss reasons and SRC-03 bid-tool records (synthetic).

Both passes use their own seeded RNG, so adding them leaves every previously generated CRM
value (and therefore the Executive and Pipeline numbers) unchanged.
"""

from __future__ import annotations

import random
from collections import defaultdict
from datetime import date, timedelta

from app.data import reference_data as ref
from app.domain.enums import Stage

# Weight order matches ref.LOSS_REASONS; price is deliberately the single most frequent reason.
LOSS_WEIGHTS = [0.27, 0.20, 0.16, 0.14, 0.13, 0.10]
MISSING_REASON_PROB = 0.06  # reps who close a deal as lost without a reason
SLA_CHOICES = (14, 21)
ORPHAN_BIDS = 3  # bid rows whose CRM opportunity id cannot be matched (DQ-04 matching queue)


def apply_loss_reasons(opps: list[dict], seed: int) -> None:
    rng = random.Random(seed + 302)
    for o in opps:
        reason = None
        if o["StageName"] == Stage.CLOSED_LOST and rng.random() >= MISSING_REASON_PROB:
            reason = rng.choices(ref.LOSS_REASONS, LOSS_WEIGHTS)[0]
        o["Loss_Reason__c"] = reason


def generate_bids(opps: list[dict], history: list[dict], seed: int) -> list[dict]:
    """One bid-tool record per Client RFP that has reached the bid/no-bid gate (Qualify)."""
    rng = random.Random(seed + 303)
    reached: dict[str, dict[str, date]] = defaultdict(dict)
    for h in history:
        reached[h["OpportunityId"]][h["StageName"]] = date.fromisoformat(h["CreatedDate"])
    rows: list[dict] = []
    for o in opps:
        stages = reached[o["Id"]]
        if o["LeadSource"] != "Client RFP" or Stage.QUALIFY not in stages:
            continue
        if o["StageName"] == Stage.QUALIFY:  # decision still pending
            continue
        no_bid = o["StageName"] == Stage.NO_BID
        received = date.fromisoformat(o["CreatedDate"]) + timedelta(days=rng.randint(0, 3))
        sla = rng.choice(SLA_CHOICES)
        submitted = None
        if not no_bid and Stage.PROPOSE in stages:
            submitted = received + timedelta(days=sla + rng.randint(-5, 4))
        rows.append(
            {
                "Pursuit_Id": f"BID-{len(rows) + 1:05d}",
                "CRM_Opportunity_Id": o["Id"],
                "RFP_Received": received.isoformat(),
                "RFP_Submitted": submitted.isoformat() if submitted else None,
                "Decision": "no_bid" if no_bid else "bid",
                "SLA_Target_Days": sla,
                "Orals_Reached": Stage.ORALS in stages,
                "Gate_Score": rng.randint(1, 2) if no_bid else rng.randint(2, 5),
            }
        )
    for i in range(ORPHAN_BIDS):
        rows.append(
            {
                "Pursuit_Id": f"BID-9{i + 1:04d}",
                "CRM_Opportunity_Id": f"006Mo{9_000_000 + i:013d}",
                "RFP_Received": "2026-06-01",
                "RFP_Submitted": None,
                "Decision": "bid",
                "SLA_Target_Days": 14,
                "Orals_Reached": False,
                "Gate_Score": 3,
            }
        )
    return rows
