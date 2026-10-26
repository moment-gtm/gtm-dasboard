"""Accounts source data (synthetic): account plans (SRC-14) and finance booking history (SRC-04).

Own seeded RNG (seed + 402), so every previously generated value is unchanged. Booking history
is a separate object from the finance contract extract, so the AC-01 reconciliation of
`raw_finance_contract` against the Closed-Won deals is untouched.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

HISTORY_START = date(2023, 1, 1)
NO_PLAN_STRATEGIC = 1  # a strategic account with no plan on file -> Overdue
HISTORY_SHARE = 0.7  # accounts with any booking history (the rest are new logos)


def _plans(accounts: list[dict], rng: random.Random, today: date) -> list[dict]:
    rows, skipped = [], 0
    for a in accounts:
        if not a["Strategic__c"]:
            continue
        if skipped < NO_PLAN_STRATEGIC:
            skipped += 1
            continue
        age = rng.choices(
            [rng.randint(10, 90), rng.randint(91, 120), rng.randint(121, 260)], [0.55, 0.25, 0.2]
        )[0]
        rows.append(
            {
                "Account_Id": a["Id"],
                "Plan_Status": rng.choice(["Active", "Active", "Draft"]),
                "Last_Review_Date": (today - timedelta(days=age)).isoformat(),
                "Whitespace_Targets": rng.randint(1, 6),
            }
        )
    return rows


def _history(accounts: list[dict], rng: random.Random, today: date) -> list[dict]:
    rows = []
    span = (today - HISTORY_START).days
    for a in accounts:
        if rng.random() >= HISTORY_SHARE:
            continue
        for _ in range(rng.randint(2, 6)):
            month = HISTORY_START + timedelta(days=rng.randint(0, span))
            rows.append(
                {
                    "Account_Id": a["Id"],
                    "Booked_Month": month.strftime("%Y-%m"),
                    "Amount_USD": round(rng.uniform(150_000, 6_000_000), 2),
                }
            )
    return rows


def generate(accounts: list[dict], seed: int, today: date) -> dict[str, list[dict]]:
    rng = random.Random(seed + 402)
    return {"account_plans": _plans(accounts, rng, today), "booking_history": _history(accounts, rng, today)}
