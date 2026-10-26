"""Seeded synthetic source data (stands in for SRC-01 CRM, SRC-02 Planning, SRC-04 Finance,
SRC-16 Entra ID and the offering catalogue while external APIs are not available).

Each opportunity is simulated through the stage path Identify -> ... -> Negotiate -> Closed Won,
dropping out at each stage with a configured probability, so stage history, days-in-stage,
deal cycle and win rate all emerge from one consistent event log. Deals whose path extends
beyond the demo "today" are open at the stage they had reached on that day.

All accounts, deals and people are fictional.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache

from faker import Faker

from app.config import settings
from app.data import (
    account_data,
    capacity_data,
    market_data,
    offering_data,
    partner_data,
    pursuit_data,
)
from app.data import reference_data as ref
from app.domain.enums import Stage

SIM_START = date(2024, 7, 1)  # deals created from here so FY25 closes exist
N_ACCOUNTS = 40
DEALS_PER_DAY = 1.12  # base creation rate; grows ~22% a year
LOG_MEDIAN_TCV = 1_000_000.0
LOG_SIGMA = 0.85
TCV_MIN, TCV_MAX = 150_000.0, 28_000_000.0

# Forward transition per stage: (p_advance, p_no_bid, p_cancel); remainder = Closed Lost.
TRANSITIONS: dict[str, tuple[float, float, float]] = {
    Stage.IDENTIFY: (0.80, 0.00, 0.06),
    Stage.QUALIFY: (0.80, 0.11, 0.01),
    Stage.PROPOSE: (0.70, 0.00, 0.01),
    Stage.ORALS: (0.72, 0.00, 0.00),
    Stage.NEGOTIATE: (0.88, 0.00, 0.03),
}
# Days in stage: triangular(low, high, mode).
DURATION: dict[str, tuple[int, int, int]] = {
    Stage.IDENTIFY: (4, 40, 12),
    Stage.QUALIFY: (7, 45, 16),
    Stage.PROPOSE: (8, 50, 20),
    Stage.ORALS: (5, 40, 14),
    Stage.NEGOTIATE: (5, 40, 14),
}
STALL_PROB = 0.09  # chance a stage drags 2.5-4x (feeds EXE-10 Ageing/Stalled)
LOSER_SLOWDOWN = 2.4  # deals that will be lost linger longer before closing
PAST_DATED_PROB = 0.05  # DQ-02: open deals whose close date has already passed


@dataclass
class Dataset:
    accounts: list[dict] = field(default_factory=list)
    opportunities: list[dict] = field(default_factory=list)
    stage_history: list[dict] = field(default_factory=list)
    bid_pursuits: list[dict] = field(default_factory=list)
    line_items: list[dict] = field(default_factory=list)
    users: list[dict] = field(default_factory=list)
    targets: list[dict] = field(default_factory=list)
    finance_contracts: list[dict] = field(default_factory=list)
    identity_users: list[dict] = field(default_factory=list)
    identity_groups: list[dict] = field(default_factory=list)
    identity_memberships: list[dict] = field(default_factory=list)
    offerings: list[dict] = field(default_factory=list)
    validation_records: list[dict] = field(default_factory=list)
    kb_assets: list[dict] = field(default_factory=list)
    proposal_assets: list[dict] = field(default_factory=list)
    asset_builds: list[dict] = field(default_factory=list)
    build_plan: list[dict] = field(default_factory=list)
    account_plans: list[dict] = field(default_factory=list)
    booking_history: list[dict] = field(default_factory=list)
    partner_registrations: list[dict] = field(default_factory=list)
    partner_certifications: list[dict] = field(default_factory=list)
    partner_tiers: list[dict] = field(default_factory=list)
    lms_records: list[dict] = field(default_factory=list)
    resources: list[dict] = field(default_factory=list)
    opportunity_team: list[dict] = field(default_factory=list)
    timesheets: list[dict] = field(default_factory=list)
    cost_rates: list[dict] = field(default_factory=list)
    pricing_versions: list[dict] = field(default_factory=list)
    project_financials: list[dict] = field(default_factory=list)
    quality_reviews: list[dict] = field(default_factory=list)
    campaigns: list[dict] = field(default_factory=list)
    campaign_members: list[dict] = field(default_factory=list)
    workshops: list[dict] = field(default_factory=list)
    web_assets: list[dict] = field(default_factory=list)
    web_engagement: list[dict] = field(default_factory=list)
    analyst_evaluations: list[dict] = field(default_factory=list)


def _sf_id(prefix: str, n: int) -> str:
    """Salesforce-style 18-char record id (fictional)."""
    return f"{prefix}Mo{n:013d}"


def _tri(rng: random.Random, spec: tuple[int, int, int]) -> int:
    low, high, mode = spec
    return max(1, round(rng.triangular(low, high, mode)))


def _gen_accounts(rng: random.Random, fake: Faker) -> list[dict]:
    industries = list(ref.INDUSTRY_TO_VERTICAL)
    geo_weights = [0.55, 0.30, 0.15]
    accounts = []
    names: set[str] = set()
    for i in range(1, N_ACCOUNTS + 1):
        name = fake.company()
        while name in names:
            name = fake.company()
        names.add(name)
        cp = ref.CLIENT_PARTNERS[(i - 1) % len(ref.CLIENT_PARTNERS)]
        accounts.append(
            {
                "Id": _sf_id("001", i),
                "Name": name,
                "Industry": rng.choice(industries),
                "BillingRegion__c": rng.choices(ref.GEOGRAPHIES, geo_weights)[0],
                "Strategic__c": rng.random() < 0.3,
                "Client_Partner_UPN__c": cp["upn"],
            }
        )
    return accounts


def _currency_for(rng: random.Random, geography: str) -> str:
    if geography == "EMEA":
        return rng.choices(["EUR", "GBP", "USD"], [0.5, 0.3, 0.2])[0]
    if geography == "APAC":
        return rng.choices(["INR", "USD"], [0.4, 0.6])[0]
    return "USD"


def _simulate_path(rng: random.Random, created: date) -> tuple[list[tuple[str, date]], str, date]:
    """Return (history[(stage, entered)], terminal_stage_or_open_stage, end_date).

    end_date is the close date for closed deals, or the date the current stage was entered
    plus its full planned duration (used to project open deals).
    """
    # Decide the full path first so losers can be slowed down.
    path: list[str] = [Stage.IDENTIFY]
    terminal: str = Stage.CLOSED_WON
    for stage in (Stage.IDENTIFY, Stage.QUALIFY, Stage.PROPOSE, Stage.ORALS, Stage.NEGOTIATE):
        adv, nobid, cancel = TRANSITIONS[stage]
        r = rng.random()
        if r < adv:
            nxt = {
                Stage.IDENTIFY: Stage.QUALIFY,
                Stage.QUALIFY: Stage.PROPOSE,
                Stage.PROPOSE: Stage.ORALS,
                Stage.ORALS: Stage.NEGOTIATE,
                Stage.NEGOTIATE: Stage.CLOSED_WON,
            }[stage]
            if nxt == Stage.CLOSED_WON:
                terminal = Stage.CLOSED_WON
                break
            path.append(nxt)
            continue
        if r < adv + nobid:
            terminal = Stage.NO_BID
        elif r < adv + nobid + cancel:
            terminal = Stage.CLIENT_CANCELLED
        else:
            terminal = Stage.CLOSED_LOST
        break
    slow = LOSER_SLOWDOWN if terminal != Stage.CLOSED_WON else 1.0
    history: list[tuple[str, date]] = []
    cursor = created
    for stage in path:
        history.append((stage, cursor))
        days = _tri(rng, DURATION[stage]) * slow
        if rng.random() < STALL_PROB:
            days *= rng.uniform(2.5, 4.0)
        cursor = cursor + timedelta(days=round(days))
    history.append((terminal, cursor))
    return history, terminal, cursor


def _offering_for(rng: random.Random, created: date) -> str | None:
    # Offering-led share trends up over time (gives EXE-05 a real trend).
    t = (created - SIM_START).days / 800
    p_offering = 0.44 + 0.16 * min(1.0, max(0.0, t))
    p_untagged = 0.13 - 0.05 * min(1.0, max(0.0, t))
    r = rng.random()
    if r < p_offering:
        return rng.choice(ref.OFFERINGS)["name"]
    if r < p_offering + p_untagged:
        return None  # DQ-01 untagged
    return ref.CAPABILITY_LED


def _gen_opportunities(rng: random.Random, fake: Faker, accounts: list[dict], today: date):
    opps, history_rows, items = [], [], []
    n = 0
    day = SIM_START
    practice_w = list(ref.PRACTICE_TARGET_SHARE.values())
    platform_w = [0.30, 0.20, 0.10, 0.08, 0.08, 0.06, 0.18]
    source_w = [0.40, 0.18, 0.12, 0.12, 0.18]
    campaigns = [f"7015Mo{c:012d}" for c in range(1, 13)]
    while day <= today:
        years = (day - SIM_START).days / 365
        rate = DEALS_PER_DAY * (1.22**years)
        count = int(rate) + (1 if rng.random() < rate - int(rate) else 0)
        for _ in range(count):
            n += 1
            acct = rng.choice(accounts)
            tcv_usd = min(TCV_MAX, max(TCV_MIN, rng.lognormvariate(0, LOG_SIGMA) * LOG_MEDIAN_TCV))
            tcv_usd = round(tcv_usd, -3)
            history, terminal, end = _simulate_path(rng, day)
            # Cut the event log at today: everything after it hasn't happened yet.
            past = [(s, d) for s, d in history if d <= today]
            current_stage, _entered = past[-1]
            is_open = current_stage in (
                Stage.IDENTIFY,
                Stage.QUALIFY,
                Stage.PROPOSE,
                Stage.ORALS,
                Stage.NEGOTIATE,
            )
            if is_open:
                remaining = sum(
                    DURATION[s][2]
                    for s in (Stage.QUALIFY, Stage.PROPOSE, Stage.ORALS, Stage.NEGOTIATE)
                    if ref.STAGE_ORDER[s] > ref.STAGE_ORDER[current_stage]
                )
                close = today + timedelta(days=remaining + rng.randint(5, 45))
                if rng.random() < PAST_DATED_PROB:
                    close = today - timedelta(days=rng.randint(3, 40))
            else:
                close = end
            lead_source = rng.choices(ref.LEAD_SOURCES, source_w)[0]
            partner = None
            partner_role = None
            if lead_source == "Partner-sourced":
                partner, partner_role = rng.choice(ref.PARTNERS), "Sourced"
            elif rng.random() < 0.22:
                partner, partner_role = rng.choice(ref.PARTNERS), "Influenced"
            campaign = None
            if lead_source == "Campaign / Marketing" or rng.random() < 0.08:
                campaign = rng.choice(campaigns)
            currency = _currency_for(rng, acct["BillingRegion__c"])
            amount = round(tcv_usd / ref.PLAN_FX_TO_USD[currency], 2)
            std_p = ref.STAGE_PROBABILITY[current_stage]
            rep_p = std_p
            if is_open and rng.random() < 0.15:  # DQ-07 rep override
                rep_p = min(0.95, max(0.05, std_p + rng.choice([-0.15, -0.1, 0.1, 0.2])))
            ai_led = rng.random() < 0.25
            lead_practice = rng.choices(ref.PRACTICES, practice_w)[0]
            oid = _sf_id("006", n)
            opps.append(
                {
                    "Id": oid,
                    "Name": f"{acct['Name'].split(' ')[0]} {fake.bs().title()}"[:80],
                    "AccountId": acct["Id"],
                    "StageName": current_stage,
                    "Amount": amount,
                    "CurrencyIsoCode": currency,
                    "Probability": round(rep_p * 100),
                    "CreatedDate": day.isoformat(),
                    "CloseDate": close.isoformat(),
                    "IsClosed": not is_open,
                    "IsWon": current_stage == Stage.CLOSED_WON,
                    "Offering__c": _offering_for(rng, day),
                    "Lead_Practice__c": lead_practice,
                    "Primary_Platform__c": rng.choices(ref.PLATFORMS, platform_w)[0],
                    "LeadSource": lead_source,
                    "AI_Led__c": ai_led,
                    "Validation_ID__c": f"VAL-{n:05d}" if ai_led and rng.random() < 0.7 else None,
                    "Partner__c": partner,
                    "Partner_Role__c": partner_role,
                    "CampaignId": campaign,
                    "Workshop_Originated__c": rng.random() < 0.07,
                    "OwnerUPN": acct["Client_Partner_UPN__c"],
                }
            )
            for seq, (stage, entered) in enumerate(past):
                history_rows.append(
                    {"OpportunityId": oid, "StageName": stage, "CreatedDate": entered.isoformat(), "Seq": seq}
                )
            # Practice line items: lead practice + 0-2 participating practices (FR-OFF-02 basis).
            others = rng.sample(
                [p for p in ref.PRACTICES if p != lead_practice],
                rng.choices([0, 1, 2], [0.45, 0.35, 0.20])[0],
            )
            shares = [1.0] if not others else [0.6] + [0.4 / len(others)] * len(others)
            for li, (practice, share) in enumerate(zip([lead_practice, *others], shares)):
                items.append(
                    {
                        "Id": f"00k{oid[3:]}{li}",
                        "OpportunityId": oid,
                        "Practice__c": practice,
                        "TotalPrice": round(amount * share, 2),
                        "CurrencyIsoCode": currency,
                    }
                )
        day += timedelta(days=1)
    return opps, history_rows, items


def _gen_targets() -> list[dict]:
    rows = []
    for fy, total in ref.FY_TARGETS_USD.items():
        for q, phase in ref.QUARTER_PHASING.items():
            for practice, share in ref.PRACTICE_TARGET_SHARE.items():
                rows.append(
                    {
                        "version": f"FY{fy % 100}-Plan-v1",
                        "fiscal_year": fy,
                        "quarter": q,
                        "practice": practice,
                        "amount_usd": round(total * phase * share, 2),
                        "loaded_at": f"{fy - 1}-12-15T09:00:00",
                    }
                )
    return rows


def _gen_finance(opps: list[dict]) -> list[dict]:
    """Month-end booked contracts for Closed Won deals (SRC-04, reconciliation source)."""
    rows = []
    for i, o in enumerate(o for o in opps if o["IsWon"]):
        rows.append(
            {
                "contract_id": f"CTR-{i + 1:06d}",
                "crm_opportunity_id": o["Id"],
                "booked_month": o["CloseDate"][:7],
                "amount_usd": round(o["Amount"] * ref.PLAN_FX_TO_USD[o["CurrencyIsoCode"]], 2),
            }
        )
    return rows


def _gen_identity() -> tuple[list[dict], list[dict], list[dict]]:
    users: dict[str, dict] = {}
    for cp in ref.CLIENT_PARTNERS:
        users[cp["upn"]] = {
            "id": f"u-{cp['upn'].split('@')[0]}",
            "userPrincipalName": cp["upn"],
            "displayName": cp["name"],
            "jobTitle": "Client Partner",
        }
    roles = {r["role"]: r for r in ref.ROLES}
    for p in ref.PERSONA_USERS:
        users.setdefault(
            p["upn"],
            {
                "id": f"u-{p['upn'].split('@')[0]}",
                "userPrincipalName": p["upn"],
                "displayName": p["name"],
                "jobTitle": roles[p["role"]]["label"],
            },
        )
    groups: dict[str, dict] = {}
    members: list[dict] = []

    def group(name: str, role: str, scope_value: str | None = None) -> dict:
        if name not in groups:
            groups[name] = {
                "id": f"g-{len(groups) + 1:03d}",
                "displayName": name,
                "role": role,
                "scope_value": scope_value,
            }
        return groups[name]

    for p in ref.PERSONA_USERS:
        r = roles[p["role"]]
        scope_value = p.get("practice") or p.get("partner")
        g = group(
            r["group"].format(practice=p.get("practice"), partner=p.get("partner")), r["role"], scope_value
        )
        members.append({"groupId": g["id"], "userId": users[p["upn"]]["id"]})
    cp_group = group("GTM-Dashboard-ClientPartner", "client_partner")
    persona_ids = {users[p["upn"]]["id"] for p in ref.PERSONA_USERS}
    for cp in ref.CLIENT_PARTNERS:
        uid = users[cp["upn"]]["id"]
        if uid not in persona_ids:
            members.append({"groupId": cp_group["id"], "userId": uid})
    return list(users.values()), list(groups.values()), members


@lru_cache(maxsize=4)
def generate(seed: int | None = None, today: date | None = None) -> Dataset:
    seed = settings.seed if seed is None else seed
    today = settings.demo_today if today is None else today
    rng = random.Random(seed)
    fake = Faker("en_US")
    fake.seed_instance(seed)
    accounts = _gen_accounts(rng, fake)
    opps, history, items = _gen_opportunities(rng, fake, accounts, today)
    pursuit_data.apply_loss_reasons(opps, seed)
    bids = pursuit_data.generate_bids(opps, history, seed)
    users, groups, members = _gen_identity()
    extra = {
        **offering_data.generate(opps, bids, seed, today),
        **account_data.generate(accounts, seed, today),
        **partner_data.generate(opps, seed, today),
        **capacity_data.generate(opps, bids, seed, today),
        **market_data.generate(opps, accounts, seed, today),
    }
    return Dataset(
        **extra,
        accounts=accounts,
        opportunities=opps,
        stage_history=history,
        bid_pursuits=bids,
        line_items=items,
        users=[
            {"upn": u["userPrincipalName"], "name": u["displayName"], "title": u["jobTitle"]} for u in users
        ],
        targets=_gen_targets(),
        finance_contracts=_gen_finance(opps),
        identity_users=users,
        identity_groups=groups,
        identity_memberships=members,
        offerings=[dict(o) for o in ref.OFFERINGS],
    )
