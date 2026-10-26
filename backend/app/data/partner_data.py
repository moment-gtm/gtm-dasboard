"""Partners source data (synthetic): partner-portal deal registrations, certifications and tiers
(SRC-08) and LMS learning records (SRC-09).

Own seeded RNG (seed + 403), so every previously generated value is unchanged. CRM already
carries Partner__c / Partner_Role__c; the registrations here are the portal's side of those deals.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from app.data import reference_data as ref

REQUIRED_CERTS = {"Adobe": 24, "Salesforce": 20, "Microsoft": 16, "Google Cloud": 12}
CERT_PROGRESS = {"Adobe": 0.96, "Salesforce": 0.72, "Microsoft": 0.45, "Google Cloud": 0.85}
CERT_NAMES = ("Solution Architect", "Developer", "Consultant", "Administrator")
CO_SELL_SHARE = 0.75  # registered partner deals the partner confirmed as co-sell
LMS_IN_PROGRESS = 5


def _registrations(opps: list[dict], rng: random.Random) -> list[dict]:
    rows = []
    for o in opps:
        if not o["Partner__c"]:
            continue
        rows.append(
            {
                "Registration_Id": f"REG-{len(rows) + 1:05d}",
                "CRM_Opportunity_Id": o["Id"],
                "Partner": o["Partner__c"],
                "Co_Sell": rng.random() < CO_SELL_SHARE,
                "Registered_On": o["CreatedDate"],
            }
        )
    return rows


def _certifications(rng: random.Random, today: date) -> list[dict]:
    rows = []
    for partner, required in REQUIRED_CERTS.items():
        for i in range(round(required * CERT_PROGRESS[partner])):
            earned = today - timedelta(days=rng.randint(30, 600))
            rows.append(
                {
                    "Partner": partner,
                    "Certification": CERT_NAMES[i % len(CERT_NAMES)],
                    "Holder": f"Consultant {partner[:3].upper()}-{i + 1:02d}",
                    "Certified_On": earned.isoformat(),
                    "Expires_On": (earned + timedelta(days=730)).isoformat(),
                }
            )
    return rows


def _lms(rng: random.Random, today: date) -> list[dict]:
    rows = []
    for partner in REQUIRED_CERTS:
        for i in range(LMS_IN_PROGRESS):
            rows.append(
                {
                    "Learner": f"Learner {partner[:3].upper()}-{i + 1:02d}",
                    "Partner": partner,
                    "Course": f"{partner} {CERT_NAMES[i % len(CERT_NAMES)]} path",
                    "Status": "In progress" if i < 3 else "Completed",
                    "Updated_On": (today - timedelta(days=rng.randint(1, 60))).isoformat(),
                }
            )
    return rows


def generate(opps: list[dict], seed: int, today: date) -> dict[str, list[dict]]:
    rng = random.Random(seed + 403)
    return {
        "partner_registrations": _registrations(opps, rng),
        "partner_certifications": _certifications(rng, today),
        "partner_tiers": [
            {"Partner": p, "Tier": t, "Required_Certifications": REQUIRED_CERTS[p]}
            for p, t in zip(ref.PARTNERS, ("Platinum", "Gold", "Gold", "Silver"))
        ],
        "lms_records": _lms(rng, today),
    }
