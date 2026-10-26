"""Governed reference data seed (Implementation order Step 0.7 — minimal admin seed).

Thresholds, targets basis, stage probabilities and catalogues live here until the
Administration module (Step 4) makes them editable. They are loaded into `ref_*` tables by
the ELT so the semantic layer only ever reads them from the platform, never from code.
All names are fictional.
"""

from __future__ import annotations

from app.domain.enums import Role, Scope, Stage

# --- Stage probability table (RSD 1.5; DQ-07 uses it to override rep probability) ----------
STAGE_PROBABILITY: dict[str, float] = {
    Stage.IDENTIFY: 0.10,
    Stage.QUALIFY: 0.25,
    Stage.PROPOSE: 0.40,
    Stage.ORALS: 0.60,
    Stage.NEGOTIATE: 0.80,
    Stage.CLOSED_WON: 1.0,
    Stage.CLOSED_LOST: 0.0,
    Stage.NO_BID: 0.0,
    Stage.CLIENT_CANCELLED: 0.0,
}
STAGE_ORDER: dict[str, int] = {s: i for i, s in enumerate(Stage)}

# --- Taxonomies ----------------------------------------------------------------------------
# RSD names five Moment verticals but not their labels (Exec plan OQ-4) — placeholders.
VERTICALS: list[str] = [
    "BFSI",
    "Retail & CPG",
    "Health & Life Sciences",
    "Comms, Media & Tech",
    "Manufacturing & Auto",
]
# CRM Account.Industry -> vertical mapping (EXE-09 source note: "Account industry mapped to vertical").
INDUSTRY_TO_VERTICAL: dict[str, str] = {
    "Banking": "BFSI",
    "Insurance": "BFSI",
    "Capital Markets": "BFSI",
    "Retail": "Retail & CPG",
    "Consumer Goods": "Retail & CPG",
    "Healthcare": "Health & Life Sciences",
    "Pharmaceuticals": "Health & Life Sciences",
    "Telecommunications": "Comms, Media & Tech",
    "Media & Entertainment": "Comms, Media & Tech",
    "Technology": "Comms, Media & Tech",
    "Automotive": "Manufacturing & Auto",
    "Industrial Manufacturing": "Manufacturing & Auto",
}
PRACTICES: list[str] = [
    "Strategy",
    "Design",
    "Marketing",
    "Content Ops",
    "DxP",
    "CCM",
    "ECM",
    "Commerce",
]
PLATFORMS: list[str] = [
    "Adobe",
    "Salesforce",
    "Sitecore",
    "Optimizely",
    "SAP Commerce",
    "Contentful",
    "Platform-agnostic",
]
LEAD_SOURCES: list[str] = [
    "Client RFP",
    "Proactive",
    "Partner-sourced",
    "Campaign / Marketing",
    "Account expansion",
]
LOSS_REASONS: list[str] = [
    "Price / commercial terms",
    "Incumbent advantage",
    "Solution fit",
    "Budget freeze / timing",
    "Relationship / sponsor",
    "Built in-house",
]
GEOGRAPHIES: list[str] = ["Americas", "EMEA", "APAC"]
PARTNERS: list[str] = ["Adobe", "Salesforce", "Microsoft", "Google Cloud"]

# Moment offering catalogue (FR-ADM-03; SharePoint List via Microsoft Graph in production).
OFFERINGS: list[dict] = [
    {"offering_id": "OFF-PULSE-INS", "name": "Pulse Insights", "family": "Pulse suite"},
    {"offering_id": "OFF-PULSE-EXP", "name": "Pulse Experience", "family": "Pulse suite"},
    {"offering_id": "OFF-MKT-OS", "name": "Marketing OS", "family": "Marketing OS"},
    {"offering_id": "OFF-AGC", "name": "Agentic Commerce", "family": "Commerce"},
    {"offering_id": "OFF-CSC", "name": "Content Supply Chain", "family": "Content"},
    {"offering_id": "OFF-DXM", "name": "DX Modernisation", "family": "Platforms"},
]
CAPABILITY_LED = "Capability-led"

# Plan FX for FY (DQ-06: non-USD converted at FY plan rate; original kept).
PLAN_FX_TO_USD: dict[str, float] = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "INR": 0.012}

# --- Thresholds (RSD Appendix B; admin-editable in Step 4 via ref_threshold) ---------------
# direction: "higher" = bigger is better; "lower" = smaller is better.
# on_track / watch are the inclusive bounds of each band.
THRESHOLDS: list[dict] = [
    {
        "metric_id": "PUR-01",
        "direction": "higher",
        "on_track": 0.40,
        "watch": 0.32,
        "unit": "pct",
        "label": "40% or more / 32% to 40% / below 32%",
    },
    {
        "metric_id": "PUR-04",
        "direction": "higher",
        "on_track": 0.20,
        "watch": 0.10,
        "unit": "pct",
        "label": "No-bid rate: 20% or more / 10% to 20% / below 10%",
    },
    {
        "metric_id": "PUR-04-WIN",
        "direction": "higher",
        "on_track": 0.35,
        "watch": 0.28,
        "unit": "pct",
        "label": "Pursued-RFP win rate: 35% or more / 28% to 35% / below 28%",
    },
    {
        "metric_id": "PUR-05",
        "direction": "higher",
        "on_track": 0.50,
        "watch": 0.40,
        "unit": "pct",
        "label": "50% or more / 40% to 50% / below 40%",
    },
    {
        "metric_id": "ADM-01",
        "direction": "higher",
        "on_track": 0.95,
        "watch": 0.90,
        "unit": "pct",
        "label": "95% or more / 90% to 95% / below 90%",
    },
    {
        "metric_id": "EXE-01",
        "direction": "higher",
        "on_track": 0.97,
        "watch": 0.85,
        "unit": "ratio_to_pace",
        "label": "97% of pace or more / 85% to 97% / below 85%",
    },
    {
        "metric_id": "EXE-02",
        "direction": "higher",
        "on_track": 3.0,
        "watch": 2.5,
        "unit": "x",
        "label": "3.0x or more / 2.5x to 3.0x / below 2.5x",
    },
    {
        "metric_id": "EXE-03",
        "direction": "higher",
        "on_track": 0.40,
        "watch": 0.32,
        "unit": "pct",
        "label": "40% or more / 32% to 40% / below 32%",
    },
    {
        "metric_id": "EXE-04",
        "direction": "higher",
        "on_track": 1.0,
        "watch": 0.85,
        "unit": "ratio_to_goal",
        "label": "100% of goal or more / 85% to 100% / below 85%",
    },
    {
        "metric_id": "EXE-05",
        "direction": "higher",
        "on_track": 0.60,
        "watch": 0.50,
        "unit": "pct",
        "label": "60% or more / 50% to 60% / below 50%",
    },
    {
        "metric_id": "EXE-06",
        "direction": "lower",
        "on_track": 120,
        "watch": 150,
        "unit": "days",
        "label": "120 days or fewer / 121 to 150 days / over 150 days",
    },
    {
        "metric_id": "EXE-10",
        "direction": "lower",
        "on_track": 60,
        "watch": 90,
        "unit": "days_in_stage",
        "label": "60 or fewer / 61 to 90 (Ageing) / over 90 (Stalled)",
    },
    {
        "metric_id": "OFF-02",
        "direction": "higher",
        "on_track": 0.55,
        "watch": 0.45,
        "unit": "pct",
        "label": "55% or more / 45% to 55% / below 45%",
    },
    {
        "metric_id": "OFF-05",
        "direction": "higher",
        "on_track": 0.90,
        "watch": 0.75,
        "unit": "ratio_to_pace",
        "label": "90% of plan pace or more / 75% to 90% / below 75%",
    },
    {
        "metric_id": "OFF-05-REUSE",
        "direction": "higher",
        "on_track": 0.70,
        "watch": 0.55,
        "unit": "pct",
        "label": "70% or more / 55% to 70% / below 55%",
    },
    {
        "metric_id": "ACC-02",
        "direction": "higher",
        "on_track": 0.40,
        "watch": 0.30,
        "unit": "pct",
        "label": "40% or more / 30% to 40% / below 30%",
    },
    {
        "metric_id": "PAR-03",
        "direction": "higher",
        "on_track": 0.90,
        "watch": 0.60,
        "unit": "pct",
        "label": "90% of required or more / 60% to 90% / below 60%",
    },
    # Step 6 — Solutions Capacity. CAP-01 is per architect (open pursuits); watch values are assumed.
    {
        "metric_id": "CAP-01",
        "direction": "lower",
        "on_track": 3,
        "watch": 4,
        "unit": "count",
        "label": "Healthy up to 3 open pursuits / stretched at 4 / over capacity at 5 or more",
    },
    {
        "metric_id": "CAP-02",
        "direction": "higher",
        "on_track": 0.80,
        "watch": 0.65,
        "unit": "pct",
        "label": "80% within SLA or more / 65% to 80% / below 65%",
    },
    {
        "metric_id": "CAP-03",
        "direction": "lower",
        "on_track": 0.02,
        "watch": 0.025,
        "unit": "pct",
        "label": "2% of TCV or less / 2% to 2.5% / above 2.5%",
    },
    {
        "metric_id": "PUR-06",
        "direction": "lower",
        "on_track": 0.03,
        "watch": 0.05,
        "unit": "pct",
        "label": "Margin erosion up to 3 points / 3 to 5 points / above 5 points",
    },
    # Step 7 — Market Signals (MKT-02 workshop-to-opportunity conversion goal 50%).
    {
        "metric_id": "MKT-02",
        "direction": "higher",
        "on_track": 0.50,
        "watch": 0.35,
        "unit": "pct",
        "label": "50% or more / 35% to 50% / below 35%",
    },
]
# Other configurable defaults (FR-EXE-05 value threshold; EXE-04 goal multiple).
SETTINGS: dict[str, float] = {
    "EXE-10.value_threshold_usd": 2_000_000.0,
    "EXE-04.goal_multiple": 3.0,
    "OFF-04.low_reuse_uses": 8.0,
    "OFF-04.refresh_due_days": 180.0,
    "ACC-04.current_days": 90.0,
    "ACC-04.overdue_days": 120.0,
}

# Pipeline module (PIP-02 ageing buckets, PIP-05 size bands) — admin-maintained, versioned (FR-ADM-02).
# `max_days` / `max_usd` of None = open-ended top band. `review` marks buckets past the review line.
AGEING_BUCKETS: list[dict] = [
    {"key": "0-30", "label": "0–30 days", "min_days": 0, "max_days": 30, "review": False},
    {"key": "31-60", "label": "31–60 days", "min_days": 31, "max_days": 60, "review": False},
    {"key": "61-90", "label": "61–90 days", "min_days": 61, "max_days": 90, "review": True},
    {"key": "90+", "label": "Over 90 days (Stalled)", "min_days": 91, "max_days": None, "review": True},
]
SIZE_BANDS: list[dict] = [
    {"key": "lt-0.5", "label": "Under $0.5M", "min_usd": 0, "max_usd": 500_000},
    {"key": "0.5-1", "label": "$0.5M–$1M", "min_usd": 500_000, "max_usd": 1_000_000},
    {"key": "1-2.5", "label": "$1M–$2.5M", "min_usd": 1_000_000, "max_usd": 2_500_000},
    {"key": "2.5-5", "label": "$2.5M–$5M", "min_usd": 2_500_000, "max_usd": 5_000_000},
    {"key": "5-10", "label": "$5M–$10M", "min_usd": 5_000_000, "max_usd": 10_000_000},
    {"key": "10+", "label": "$10M and over", "min_usd": 10_000_000, "max_usd": None},
]

# --- Planning targets basis (SRC-02 stand-in) ---------------------------------------------
# FY bookings targets (USD) and quarter phasing; split to practices by PRACTICE_TARGET_SHARE.
FY_TARGETS_USD: dict[int, float] = {2025: 200_000_000.0, 2026: 225_000_000.0, 2027: 260_000_000.0}
QUARTER_PHASING: dict[int, float] = {1: 0.22, 2: 0.24, 3: 0.26, 4: 0.28}
PRACTICE_TARGET_SHARE: dict[str, float] = {
    "Strategy": 0.08,
    "Design": 0.10,
    "Marketing": 0.14,
    "Content Ops": 0.10,
    "DxP": 0.22,
    "CCM": 0.10,
    "ECM": 0.08,
    "Commerce": 0.18,
}

# --- People & personas (SRC-16 Entra ID stand-in; all fictional) --------------------------
CLIENT_PARTNERS: list[dict] = [
    {"upn": "asha.menon@moment.example", "name": "Asha Menon"},
    {"upn": "daniel.brooks@moment.example", "name": "Daniel Brooks"},
    {"upn": "priya.raman@moment.example", "name": "Priya Raman"},
    {"upn": "marcus.lee@moment.example", "name": "Marcus Lee"},
    {"upn": "elena.rossi@moment.example", "name": "Elena Rossi"},
    {"upn": "tom.fischer@moment.example", "name": "Tom Fischer"},
]

MODULES_ALL = (
    "executive",
    "pipeline",
    "pursuits",
    "offerings",
    "accounts",
    "partners",
    "solutions_capacity",
    "market_signals",
)

# Consolidated roles & access matrix (Shared doc 5; Exec plan 7).
ROLES: list[dict] = [
    {
        "role": Role.GTM_LEAD,
        "label": "GTM Lead (business owner)",
        "scope": Scope.ALL,
        "modules": (*MODULES_ALL, "admin"),
        "restricted": True,
        "group": "GTM-Dashboard-GTMLead",
        "default_view": "executive",
    },
    {
        "role": Role.LEADERSHIP,
        "label": "Moment leadership",
        "scope": Scope.ALL,
        "modules": MODULES_ALL,
        "restricted": True,
        "group": "GTM-Dashboard-Leadership",
        "default_view": "executive",
    },
    {
        "role": Role.FINANCE,
        "label": "Finance business partner",
        "scope": Scope.ALL,
        "modules": MODULES_ALL,
        "restricted": True,
        "group": "GTM-Dashboard-Finance",
        "default_view": "pursuits",
    },
    {
        "role": Role.PRACTICE_LEAD,
        "label": "Practice lead",
        "scope": Scope.PRACTICE,
        "modules": MODULES_ALL,
        "restricted": False,
        "group": "GTM-Dashboard-PracticeLead-{practice}",
        "default_view": "pipeline",
    },
    {
        "role": Role.CLIENT_PARTNER,
        "label": "Client partner / account lead",
        "scope": Scope.ACCOUNTS,
        "modules": ("executive", "pipeline", "accounts", "partners"),
        "restricted": False,
        "group": "GTM-Dashboard-ClientPartner",
        "default_view": "accounts",
    },
    {
        "role": Role.ALLIANCE_MANAGER,
        "label": "Alliance manager",
        "scope": Scope.PARTNER,
        "modules": ("executive", "partners", "offerings"),
        "restricted": False,
        "group": "GTM-Dashboard-Alliance-{partner}",
        "default_view": "partners",
    },
    {
        "role": Role.MARKETING,
        "label": "Marketing",
        "scope": Scope.CAMPAIGN,
        "modules": ("executive", "market_signals"),
        "restricted": False,
        "group": "GTM-Dashboard-Marketing",
        "default_view": "market_signals",
    },
    {
        "role": Role.SALES_OPS,
        "label": "Sales Operations (administrator)",
        "scope": Scope.ALL,
        "modules": (*MODULES_ALL, "admin"),
        "restricted": False,
        "group": "GTM-Dashboard-SalesOps",
        "default_view": "admin",
    },
    {
        "role": Role.SOLUTIONS_LEAD,
        "label": "Solutions lead & architect",
        "scope": Scope.ALL,
        "modules": ("pipeline", "pursuits", "offerings", "solutions_capacity"),
        "restricted": False,
        "group": "GTM-Dashboard-Solutions",
        "default_view": "solutions_capacity",
    },
]

# One demo user per persona; the RoleSwitcher picks between them.
PERSONA_USERS: list[dict] = [
    {"upn": "jordan.avery@moment.example", "name": "Jordan Avery", "role": Role.GTM_LEAD},
    {"upn": "sam.okafor@moment.example", "name": "Sam Okafor", "role": Role.LEADERSHIP},
    {"upn": "lena.kovacs@moment.example", "name": "Lena Kovacs", "role": Role.FINANCE},
    {"upn": "ravi.iyer@moment.example", "name": "Ravi Iyer", "role": Role.PRACTICE_LEAD, "practice": "DxP"},
    {"upn": "asha.menon@moment.example", "name": "Asha Menon", "role": Role.CLIENT_PARTNER},
    {
        "upn": "noah.berg@moment.example",
        "name": "Noah Berg",
        "role": Role.ALLIANCE_MANAGER,
        "partner": "Adobe",
    },
    {"upn": "mia.chen@moment.example", "name": "Mia Chen", "role": Role.MARKETING},
    {"upn": "omar.haddad@moment.example", "name": "Omar Haddad", "role": Role.SALES_OPS},
    {"upn": "kai.watanabe@moment.example", "name": "Kai Watanabe", "role": Role.SOLUTIONS_LEAD},
    {"upn": "balaji.parthasarathy@moment.example", "name": "Balaji Parthasarathy", "role": Role.GTM_LEAD},
    {"upn": "bindya.somaraj@moment.example", "name": "Bindya Somaraj", "role": Role.GTM_LEAD},
    {"upn": "deepak.narayanan@moment.example", "name": "Deepak Narayanan", "role": Role.LEADERSHIP},
]

# --- Source registry (RSD 6.1/6.2) — Executive-relevant sources only --------------------
# sla_hours: staleness beyond one cycle triggers FR-GEN-09.
SOURCES: list[dict] = [
    {
        "source_id": "SRC-01",
        "key": "crm",
        "name": "CRM (Salesforce Sales Cloud)",
        "cadence": "Daily, refreshed by 07:00 IST",
        "sla_hours": 26,
    },
    {
        "source_id": "SRC-02",
        "key": "planning",
        "name": "Planning / targets (Anaplan)",
        "cadence": "On change / quarterly",
        "sla_hours": 24 * 95,
    },
    {
        "source_id": "SRC-03",
        "key": "bid",
        "name": "Bid & proposal management",
        "cadence": "Nightly",
        "sla_hours": 26,
    },
    {
        "source_id": "SRC-04",
        "key": "finance",
        "name": "Finance ERP (SAP S/4HANA)",
        "cadence": "Monthly after period close",
        "sla_hours": 24 * 35,
    },
    {
        "source_id": "SRC-16",
        "key": "identity",
        "name": "Identity (Microsoft Entra ID)",
        "cadence": "Nightly",
        "sla_hours": 26,
    },
    {
        "source_id": "REF-OFF",
        "key": "catalogue",
        "name": "Offering catalogue (SharePoint List)",
        "cadence": "On change",
        "sla_hours": 24 * 35,
    },
    {
        "source_id": "SRC-12",
        "key": "kb",
        "name": "Knowledge repository (SharePoint)",
        "cadence": "Weekly",
        "sla_hours": 24 * 8,
    },
    {
        "source_id": "SRC-13",
        "key": "validation",
        "name": "AI validation register (SharePoint List)",
        "cadence": "Nightly",
        "sla_hours": 26,
    },
    {
        "source_id": "SRC-17",
        "key": "assets",
        "name": "Asset development tracker (Workfront)",
        "cadence": "Nightly",
        "sla_hours": 26,
    },
    {
        "source_id": "SRC-14",
        "key": "account_plan",
        "name": "Account plans (CRM / SharePoint)",
        "cadence": "Weekly",
        "sla_hours": 24 * 8,
    },
    {
        "source_id": "SRC-08",
        "key": "partner",
        "name": "Partner portals (Adobe, Salesforce)",
        "cadence": "Monthly export",
        "sla_hours": 24 * 35,
    },
    {
        "source_id": "SRC-09",
        "key": "lms",
        "name": "Learning management system",
        "cadence": "Weekly",
        "sla_hours": 24 * 8,
    },
    {
        "source_id": "SRC-05",
        "key": "pricing",
        "name": "Pricing tool / deal desk",
        "cadence": "Nightly",
        "sla_hours": 26,
    },
    {
        "source_id": "SRC-06",
        "key": "resource",
        "name": "Resource management",
        "cadence": "Weekly",
        "sla_hours": 24 * 8,
    },
    {
        "source_id": "SRC-07",
        "key": "timesheet",
        "name": "Timesheets",
        "cadence": "Weekly",
        "sla_hours": 24 * 8,
    },
    {
        "source_id": "SRC-10",
        "key": "mktg",
        "name": "Marketing automation (Marketo / Journey Optimizer)",
        "cadence": "Nightly",
        "sla_hours": 26,
    },
    {
        "source_id": "SRC-11",
        "key": "web",
        "name": "Web CMS & analytics (AEM + Adobe CJA)",
        "cadence": "Weekly",
        "sla_hours": 24 * 8,
    },
    {
        "source_id": "SRC-15",
        "key": "analyst",
        "name": "Analyst relations tracker (SharePoint List)",
        "cadence": "On change",
        "sla_hours": 24 * 95,
    },
]
