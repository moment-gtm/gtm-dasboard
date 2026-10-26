"""Market Signals source data (synthetic): marketing automation campaigns & members (SRC-10),
web & thought-leadership content analytics (SRC-11), discovery workshops in CRM (SRC-01),
and analyst evaluations (SRC-15).

Uses its own seeded RNG (seed + 607) so existing generated dataset records remain identical.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from app.data import reference_data as ref
from app.domain.enums import Stage

CAMPAIGN_SPECS: list[tuple[str, str, str, str, str, float]] = [
    (
        "Agentic Experience Wave",
        "Executive Event",
        "Strategy",
        "Adobe",
        "2025-01-15",
        145_000.0,
    ),
    (
        "Adobe Summit Executive Forum",
        "Executive Event",
        "Marketing",
        "Adobe",
        "2025-03-10",
        180_000.0,
    ),
    (
        "Next-Gen Commerce Roadshow",
        "Workshop Series",
        "Commerce",
        "SAP Commerce",
        "2025-02-05",
        110_000.0,
    ),
    (
        "Salesforce Agentforce Accelerator",
        "Partner Co-Marketing",
        "DxP",
        "Salesforce",
        "2025-04-12",
        135_000.0,
    ),
    (
        "Global Content Supply Chain Tour",
        "ABM Program",
        "Content Ops",
        "Adobe",
        "2025-05-20",
        125_000.0,
    ),
    (
        "Loyalty & Personalisation Roundtable",
        "Executive Event",
        "CCM",
        "Salesforce",
        "2025-06-18",
        95_000.0,
    ),
    (
        "AI-Ready Experience Blueprint",
        "Thought Leadership",
        "DxP",
        "Sitecore",
        "2025-08-04",
        115_000.0,
    ),
    (
        "Digital Core Modernisation Series",
        "Webinar / Virtual",
        "ECM",
        "Contentful",
        "2025-09-15",
        85_000.0,
    ),
    (
        "Retail & CPG Experience Lab",
        "Workshop Series",
        "Commerce",
        "Optimizely",
        "2025-10-10",
        105_000.0,
    ),
    (
        "Financial Services Digital Trust Summit",
        "Executive Event",
        "Strategy",
        "Platform-agnostic",
        "2025-11-12",
        150_000.0,
    ),
    (
        "Composable Commerce Sprint",
        "ABM Program",
        "Commerce",
        "SAP Commerce",
        "2026-01-14",
        120_000.0,
    ),
    (
        "Healthcare Experience Transformation",
        "Partner Co-Marketing",
        "Design",
        "Salesforce",
        "2026-02-02",
        130_000.0,
    ),
]

POV_TEMPLATES: list[tuple[str, str, str, str, str]] = [
    (
        "Agentic AI in Customer Experience: From Co-Pilots to Autonomous Journeys",
        "POV",
        "Strategy",
        "Adobe",
        "2025-04-16",
    ),
    (
        "Composable Commerce Economics: Total Cost & Conversion Benchmarks",
        "Research Report",
        "Commerce",
        "SAP Commerce",
        "2025-05-19",
    ),
    (
        "The GenAI Content Supply Chain Playbook for Global Brands",
        "Playbook",
        "Content Ops",
        "Adobe",
        "2025-06-11",
    ),
    (
        "Zero-Copy Customer Data Architectures with Salesforce Data Cloud",
        "Whitepaper",
        "DxP",
        "Salesforce",
        "2025-07-23",
    ),
    (
        "Designing High-Trust Digital Banking Experiences in the AI Era",
        "POV",
        "Design",
        "Platform-agnostic",
        "2025-08-18",
    ),
    (
        "Next-Gen Loyalty: Moving Beyond Points to Predictive Engagement",
        "Executive Brief",
        "Marketing",
        "Adobe",
        "2025-09-14",
    ),
    (
        "Agentforce in the Contact Centre: Deflection, Resolution & Revenue",
        "POV",
        "DxP",
        "Salesforce",
        "2025-10-21",
    ),
    (
        "AI-Augmented Product Engineering: Velocity with Governance",
        "Research Report",
        "DxP",
        "Sitecore",
        "2025-11-17",
    ),
    (
        "B2B Commerce Modernisation for Industrial & Manufacturing Leaders",
        "Whitepaper",
        "Commerce",
        "Optimizely",
        "2025-12-08",
    ),
    (
        "Measuring Experience ROI: Linking Design Systems to Revenue Growth",
        "POV",
        "Design",
        "Platform-agnostic",
        "2026-01-20",
    ),
    (
        "Hyper-Personalisation at Scale with Composable Content & Data",
        "Playbook",
        "Marketing",
        "Contentful",
        "2026-02-09",
    ),
    (
        "Retail Media Networks: Monetising First-Party Shopper Signals",
        "Executive Brief",
        "Marketing",
        "Adobe",
        "2026-02-26",
    ),
    (
        "Autonomous Customer Communications & CCM Modernisation",
        "POV",
        "CCM",
        "Adobe",
        "2026-03-11",
    ),
    (
        "Content Velocity Benchmark 2026: How Leaders Cut Campaign Cycle Time by 45%",
        "Research Report",
        "Content Ops",
        "Adobe",
        "2026-04-14",
    ),
    (
        "Unified Store & Digital Commerce: The Omnichannel Fulfilment Blueprint",
        "Whitepaper",
        "Commerce",
        "SAP Commerce",
        "2026-05-12",
    ),
    (
        "State of Agentic Experience 2026: Enterprise Readiness & Value Realisation",
        "Research Report",
        "Strategy",
        "Adobe",
        "2026-06-08",
    ),
    (
        "Responsible AI Guardrails for Customer-Facing Digital Platforms",
        "POV",
        "DxP",
        "Salesforce",
        "2026-07-15",
    ),
    (
        "Enterprise Content Management Modernisation for Regulated Industries",
        "Playbook",
        "ECM",
        "Contentful",
        "2026-07-29",
    ),
    (
        "Dynamic B2B Pricing & Quoting in Composable Commerce Ecosystems",
        "Executive Brief",
        "Commerce",
        "Optimizely",
        "2026-08-07",
    ),
]

ANALYST_EVALUATIONS: list[dict] = [
    {
        "Eval_Id": "ANL-001",
        "Firm": "Forrester",
        "Report_Series": "Forrester Wave",
        "Report_Title": "The Forrester Wave™: Digital Experience Services, Q1 2026",
        "Practice": "DxP",
        "Platform": "Adobe",
        "Published_Date": "2026-02-18",
        "Current_Placement": "Leader",
        "Prior_Placement": "Strong Performer",
        "Direction": "Improved",
        "Direction_Icon": "↑",
        "Score_Delta": 0.42,
        "Lead_Analyst": "Clara Vance",
        "Summary_Note": (
            "Promoted to Leader on the strength of Agentic Experience Accelerator "
            "and Adobe GenStudio delivery scale."
        ),
    },
    {
        "Eval_Id": "ANL-002",
        "Firm": "Gartner",
        "Report_Series": "Gartner Magic Quadrant",
        "Report_Title": "Gartner Magic Quadrant for Custom Digital Experience & Platform Engineering",
        "Practice": "DxP",
        "Platform": "Sitecore",
        "Published_Date": "2026-01-29",
        "Current_Placement": "Leader",
        "Prior_Placement": "Leader",
        "Direction": "Maintained",
        "Direction_Icon": "→",
        "Score_Delta": 0.14,
        "Lead_Analyst": "Marcus Lindqvist",
        "Summary_Note": (
            "Retained Leader placement for third consecutive year; " "improved completeness of vision score."
        ),
    },
    {
        "Eval_Id": "ANL-003",
        "Firm": "IDC",
        "Report_Series": "IDC MarketScape",
        "Report_Title": "IDC MarketScape: Worldwide Adobe Experience Cloud Professional Services 2025–2026",
        "Practice": "Marketing",
        "Platform": "Adobe",
        "Published_Date": "2025-11-20",
        "Current_Placement": "Leader",
        "Prior_Placement": "Leader",
        "Direction": "Improved",
        "Direction_Icon": "↑",
        "Score_Delta": 0.31,
        "Lead_Analyst": "Priya Natarajan",
        "Summary_Note": (
            "Expanded position in the Leaders circle driven by global "
            "content supply chain automation references."
        ),
    },
    {
        "Eval_Id": "ANL-004",
        "Firm": "Everest Group",
        "Report_Series": "Everest PEAK Matrix",
        "Report_Title": "Everest Group PEAK Matrix® for AI-Led Customer Experience & CRM Services",
        "Practice": "Strategy",
        "Platform": "Salesforce",
        "Published_Date": "2026-02-05",
        "Current_Placement": "Leader",
        "Prior_Placement": "Major Contender",
        "Direction": "Improved",
        "Direction_Icon": "↑",
        "Score_Delta": 0.48,
        "Lead_Analyst": "Rohan Deshmukh",
        "Summary_Note": (
            "Named a Star Performer and newly elevated to Leader following "
            "rapid Agentforce deployment wins."
        ),
    },
    {
        "Eval_Id": "ANL-005",
        "Firm": "Forrester",
        "Report_Series": "Forrester Wave",
        "Report_Title": "The Forrester Wave™: Composable Commerce Services, Q4 2025",
        "Practice": "Commerce",
        "Platform": "SAP Commerce",
        "Published_Date": "2025-10-30",
        "Current_Placement": "Strong Performer",
        "Prior_Placement": "Strong Performer",
        "Direction": "Maintained",
        "Direction_Icon": "→",
        "Score_Delta": 0.08,
        "Lead_Analyst": "Elena Rostova",
        "Summary_Note": (
            "Strong scores in B2B composable reference architecture; " "expanding EMEA delivery bench."
        ),
    },
    {
        "Eval_Id": "ANL-006",
        "Firm": "Gartner",
        "Report_Series": "Gartner Magic Quadrant",
        "Report_Title": "Gartner Magic Quadrant for Customer Communications & Content Operations",
        "Practice": "Content Ops",
        "Platform": "Contentful",
        "Published_Date": "2025-12-11",
        "Current_Placement": "Visionary",
        "Prior_Placement": "Challenger",
        "Direction": "Improved",
        "Direction_Icon": "↑",
        "Score_Delta": 0.35,
        "Lead_Analyst": "David K. Sterling",
        "Summary_Note": (
            "Shifted into Visionaries quadrant on modular content supply chain " "and orchestration IP."
        ),
    },
    {
        "Eval_Id": "ANL-007",
        "Firm": "IDC",
        "Report_Series": "IDC MarketScape",
        "Report_Title": "IDC MarketScape: Worldwide Digital Commerce Transformation Services",
        "Practice": "Commerce",
        "Platform": "Optimizely",
        "Published_Date": "2025-09-18",
        "Current_Placement": "Major Player",
        "Prior_Placement": "Leader",
        "Direction": "Declined",
        "Direction_Icon": "↓",
        "Score_Delta": -0.18,
        "Lead_Analyst": "Hannah Abbott",
        "Summary_Note": (
            "Stepped back from Leader to Major Player while mid-market commerce "
            "accelerator assets are being refreshed."
        ),
    },
    {
        "Eval_Id": "ANL-008",
        "Firm": "Everest Group",
        "Report_Series": "Everest PEAK Matrix",
        "Report_Title": "Everest Group PEAK Matrix® for Experience Design & Research Services",
        "Practice": "Design",
        "Platform": "Platform-agnostic",
        "Published_Date": "2026-03-04",
        "Current_Placement": "Leader",
        "Prior_Placement": "Leader",
        "Direction": "Maintained",
        "Direction_Icon": "→",
        "Score_Delta": 0.19,
        "Lead_Analyst": "Ananya Sen",
        "Summary_Note": (
            "Consistent Leader ranking backed by executive discovery workshop "
            "conversion and design system reuse."
        ),
    },
]


def _campaigns() -> list[dict]:
    rows: list[dict] = []
    for idx, (name, channel, practice, platform, start_iso, budget) in enumerate(CAMPAIGN_SPECS, start=1):
        start_dt = date.fromisoformat(start_iso)
        end_dt = start_dt + timedelta(days=120)
        rows.append(
            {
                "Campaign_Id": f"7015Mo{idx:012d}",
                "Campaign_Name": name,
                "Channel": channel,
                "Practice": practice,
                "Platform": platform,
                "Start_Date": start_iso,
                "End_Date": end_dt.isoformat(),
                "Budget_USD": budget,
                "Status": "Active" if idx >= 9 else "Completed",
            }
        )
    return rows


def _campaign_members(
    opps: list[dict], campaigns: list[dict], accounts: list[dict], rng: random.Random
) -> list[dict]:
    """Generate SRC-10 campaign member attribution records.

    Every CRM opportunity with CampaignId gets a primary campaign member row so SRC-01 and SRC-10
    reconcile within 0.5% (AC-01). Additional non-deal touchpoints represent top-of-funnel leads.
    """
    rows: list[dict] = []
    for o in opps:
        cid = o.get("CampaignId")
        if not cid:
            continue
        tcv_usd = round(o["Amount"] * ref.PLAN_FX_TO_USD[o["CurrencyIsoCode"]], 2)
        rows.append(
            {
                "Member_Id": f"CM-{len(rows) + 1:05d}",
                "Campaign_Id": cid,
                "Account_Id": o["AccountId"],
                "Opportunity_Id": o["Id"],
                "Primary_Source": True,
                "Responded_Date": o["CreatedDate"],
                "Attended": True,
                "Attributed_TCV_USD": tcv_usd,
            }
        )

    for c in campaigns:
        for _ in range(rng.randint(5, 9)):
            acct = rng.choice(accounts)
            start_dt = date.fromisoformat(c["Start_Date"])
            resp_dt = start_dt + timedelta(days=rng.randint(1, 75))
            rows.append(
                {
                    "Member_Id": f"CM-{len(rows) + 1:05d}",
                    "Campaign_Id": c["Campaign_Id"],
                    "Account_Id": acct["Id"],
                    "Opportunity_Id": None,
                    "Primary_Source": False,
                    "Responded_Date": resp_dt.isoformat(),
                    "Attended": rng.random() < 0.78,
                    "Attributed_TCV_USD": 0.0,
                }
            )
    return rows


def _workshops(opps: list[dict], accounts: list[dict], rng: random.Random) -> list[dict]:
    """Generate SRC-01 discovery workshop records (MKT-02).

    Every opportunity with Workshop_Originated__c=True originates from a discovery workshop held
    within 90 days. Additional workshops without a downstream opportunity are generated so the
    overall workshop-to-qualified conversion rate sits just above the 50% target (On track).
    """
    acct_by_id = {a["Id"]: a for a in accounts}
    rows: list[dict] = []
    converting_opps = [o for o in opps if o.get("Workshop_Originated__c")]

    for o in converting_opps:
        acct = acct_by_id[o["AccountId"]]
        days_to_opp = rng.randint(12, 68)  # within 90-day conversion window
        is_qualified = o["StageName"] not in (Stage.IDENTIFY, Stage.NO_BID, Stage.CLIENT_CANCELLED)
        rows.append(
            {
                "Workshop_Id": f"WKS-{len(rows) + 1:05d}",
                "Workshop_Title": f"{acct['Name'].split(' ')[0]} Discovery & Value Lab",
                "Account_Id": o["AccountId"],
                "Practice": o["Lead_Practice__c"],
                "Platform": o["Primary_Platform__c"],
                "Vertical": ref.INDUSTRY_TO_VERTICAL[acct["Industry"]],
                "Geography": acct["BillingRegion__c"],
                "Facilitator_UPN": o["OwnerUPN"],
                "Workshop_Date": o["CreatedDate"],
                "Opportunity_Id": o["Id"],
                "Opportunity_Created_Date": o["CreatedDate"],
                "Days_To_Opportunity": days_to_opp,
                "Converted_Within_90d": True,
                "Is_Qualified": is_qualified,
                "Is_Won": bool(o["IsWon"]),
            }
        )

    # Add non-converting workshops (~1 per 3 converting workshops) so conversion rate is ~58-64%.
    for idx, o in enumerate(converting_opps):
        if idx % 3 != 0:
            continue
        acct = acct_by_id[o["AccountId"]]
        rows.append(
            {
                "Workshop_Id": f"WKS-{len(rows) + 1:05d}",
                "Workshop_Title": f"{acct['Name'].split(' ')[0]} Executive Visioning Session",
                "Account_Id": o["AccountId"],
                "Practice": o["Lead_Practice__c"],
                "Platform": o["Primary_Platform__c"],
                "Vertical": ref.INDUSTRY_TO_VERTICAL[acct["Industry"]],
                "Geography": acct["BillingRegion__c"],
                "Facilitator_UPN": o["OwnerUPN"],
                "Workshop_Date": o["CreatedDate"],
                "Opportunity_Id": None,
                "Opportunity_Created_Date": None,
                "Days_To_Opportunity": None,
                "Converted_Within_90d": False,
                "Is_Qualified": False,
                "Is_Won": False,
            }
        )
    return rows


def _web_content(rng: random.Random) -> tuple[list[dict], list[dict]]:
    """Generate SRC-11 thought leadership assets and engagement metrics (MKT-01)."""
    assets: list[dict] = []
    engagement: list[dict] = []

    for idx, (title, asset_type, practice, platform, pub_iso) in enumerate(POV_TEMPLATES, start=1):
        asset_id = f"POV-{idx:04d}"
        pub_dt = date.fromisoformat(pub_iso)
        quarter = f"{pub_dt.year}-Q{(pub_dt.month - 1) // 3 + 1}"
        assets.append(
            {
                "Asset_Id": asset_id,
                "Title": title,
                "Asset_Type": asset_type,
                "Practice": practice,
                "Platform": platform,
                "Published_Date": pub_iso,
                "Published_Quarter": quarter,
                "Author_Practice": practice,
                "URL_Slug": f"/insights/{asset_id.lower()}",
            }
        )
        # Newer quarters show higher digital reach to illustrate an upward trend.
        growth_boost = 1.0 + (idx * 0.045)
        downloads = round(rng.randint(320, 680) * growth_boost)
        engaged_visits = round(rng.randint(1450, 3100) * growth_boost)
        engagement.append(
            {
                "Metric_Id": f"WEM-{idx:04d}",
                "Asset_Id": asset_id,
                "Period_Quarter": quarter,
                "Downloads": downloads,
                "Engaged_Visits": engaged_visits,
                "Avg_Dwell_Seconds": rng.randint(145, 310),
                "Social_Shares": rng.randint(45, 210),
            }
        )
    return assets, engagement


def generate(opps: list[dict], accounts: list[dict], seed: int, today: date) -> dict[str, list[dict]]:
    del today
    rng = random.Random(seed + 607)
    campaigns = _campaigns()
    campaign_members = _campaign_members(opps, campaigns, accounts, rng)
    workshops = _workshops(opps, accounts, rng)
    web_assets, web_engagement = _web_content(rng)
    return {
        "campaigns": campaigns,
        "campaign_members": campaign_members,
        "workshops": workshops,
        "web_assets": web_assets,
        "web_engagement": web_engagement,
        "analyst_evaluations": [dict(row) for row in ANALYST_EVALUATIONS],
    }
