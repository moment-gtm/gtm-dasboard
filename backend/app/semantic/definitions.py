"""Metric registry — single source of truth for metric metadata (FR-GEN-07, RSD §5, §10.2).

Definitions are quoted from RSD v0.9.1 §5. Every widget's metric ID must resolve here; the
ELT also loads this registry into `ref_metric_definition`.
"""

from __future__ import annotations

SOURCE_NAMES: dict[str, str] = {
    "SRC-01": "CRM (Salesforce Sales Cloud)",
    "SRC-02": "Planning / targets (Anaplan)",
    "SRC-03": "Bid & proposal management",
    "SRC-04": "Finance ERP (SAP S/4HANA)",
    "SRC-16": "Identity (Microsoft Entra ID)",
    "REF-OFF": "Offering catalogue (SharePoint List, FR-ADM-03)",
    "SRC-12": "Knowledge repository (SharePoint via Microsoft Graph / M365 MCP)",
    "SRC-13": "AI validation register (SharePoint List via Microsoft Graph / M365 MCP)",
    "SRC-17": "Asset development tracker (Adobe Workfront MCP)",
    "SRC-14": "Account plans (CRM object or SharePoint via M365 MCP)",
    "SRC-08": "Partner portals (Adobe, Salesforce partner APIs / monthly export)",
    "SRC-09": "Learning management system (LMS extract)",
    "SRC-05": "Pricing tool / deal desk",
    "SRC-06": "Resource management",
    "SRC-07": "Timesheets",
    "SRC-10": "Marketing automation (Marketo / HubSpot)",
    "SRC-11": "Web & content analytics (Adobe Analytics)",
    "SRC-15": "Analyst relations register (SharePoint List via M365 MCP)",
}

METRICS: dict[str, dict] = {
    "EXE-01": {
        "name": "Bookings vs target",
        "definition": "Sum of TCV moved to Closed Won with close date in period, divided by the "
        "bookings target for the period. Status compares bookings with plan pace.",
        "calculation": "bookings = SUM(tcv_usd) WHERE stage = Closed Won AND close_date IN period; "
        "attainment vs pace = bookings / plan pace (target pro-rated to today).",
        "sources": ["SRC-01", "SRC-02"],
        "owner": "GTM Lead with Finance",
        "refresh": "Daily",
        "dimensions": ["Quarter", "Vertical", "Practice", "Platform", "Account"],
        "period_sensitive": True,
        "goal_label": "At or above plan pace (On track ≥97% of pace; Watch 85–97%)",
    },
    "EXE-02": {
        "name": "Pipeline coverage",
        "definition": "Qualified open pipeline (Qualify or later) with expected close in the current "
        "and next quarter, divided by the combined target for those two quarters less bookings "
        "already achieved in them.",
        "calculation": "SUM(tcv_usd) open Qualify+ closing in current/next quarter ÷ "
        "(target(current) + target(next) − bookings(current, next)).",
        "sources": ["SRC-01", "SRC-02"],
        "owner": "Sales Operations",
        "refresh": "Daily; weekly snapshot",
        "dimensions": ["Vertical", "Practice", "Platform"],
        "period_sensitive": False,
        "goal_label": "3.0x (Watch 2.5x–3.0x)",
    },
    "EXE-03": {
        "name": "Win rate",
        "definition": "Count of Closed Won divided by count of Closed Won plus Closed Lost, for "
        "opportunities closed in period. Value variant uses TCV. No-bid and client-cancelled "
        "excluded.",
        "calculation": "COUNT(won) ÷ (COUNT(won) + COUNT(lost)) for close_date IN period.",
        "sources": ["SRC-01"],
        "owner": "GTM Lead",
        "refresh": "Daily",
        "dimensions": ["Quarter", "Vertical", "Practice", "Source"],
        "period_sensitive": True,
        "goal_label": "40% (Watch 32–40%)",
    },
    "EXE-04": {
        "name": "New pipeline created",
        "definition": "Sum of TCV of opportunities with created date in period, regardless of later "
        "outcome. Goal: three times the bookings target for the period, pro-rated for the current "
        "quarter.",
        "calculation": "SUM(tcv_usd) WHERE created_date IN period ÷ (3 × plan-pace target for period).",
        "sources": ["SRC-01", "SRC-02"],
        "owner": "GTM Lead",
        "refresh": "Daily",
        "dimensions": ["Quarter", "Vertical", "Practice", "Source"],
        "period_sensitive": True,
        "goal_label": "3× bookings target, pro-rated (Watch 85–100% of goal)",
    },
    "EXE-05": {
        "name": "Offering-led pipeline share",
        "definition": "Open TCV where Offering is not Capability-led, divided by total open TCV. "
        "Untagged opportunities are shown as a separate bucket and count against the share.",
        "calculation": "SUM(open tcv_usd WHERE offering_class = Offering-led) ÷ SUM(open tcv_usd).",
        "sources": ["SRC-01", "REF-OFF"],
        "owner": "Offering portfolio lead",
        "refresh": "Daily",
        "dimensions": ["Offering", "Practice", "Vertical"],
        "period_sensitive": False,
        "goal_label": "60% (Watch 50–60%)",
    },
    "EXE-06": {
        "name": "Average deal cycle",
        "definition": "Mean of (close date minus created date) in days for Closed Won in period.",
        "calculation": "AVG(close_date − created_date) WHERE stage = Closed Won AND close_date IN period.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily",
        "dimensions": ["Quarter", "Practice", "Source", "Size band"],
        "period_sensitive": True,
        "goal_label": "120 days or fewer (Watch 121–150)",
    },
    "EXE-07": {
        "name": "Bookings runway",
        "definition": "Booked FY TCV; Commit = sum of TCV × stage probability for open deals in "
        "Orals or Negotiate closing this quarter; Best case = same for Qualify and Propose; "
        "full-year target; plan pace.",
        "calculation": "booked = SUM(won tcv_usd in FY); commit/best case = SUM(tcv_usd × standard "
        "stage probability) closing in current quarter; plan pace = completed quarter targets + "
        "current quarter target × elapsed share (calendar days).",
        "sources": ["SRC-01", "SRC-02"],
        "owner": "GTM Lead",
        "refresh": "Daily",
        "dimensions": ["Vertical", "Practice", "Platform"],
        "period_sensitive": False,
        "goal_label": "Full-year target",
    },
    "EXE-08": {
        "name": "Bookings by quarter",
        "definition": "Closed-won TCV per fiscal quarter with quarterly target.",
        "calculation": "SUM(won tcv_usd) GROUP BY close quarter, joined to quarterly target.",
        "sources": ["SRC-01", "SRC-02"],
        "owner": "GTM Lead",
        "refresh": "Daily",
        "dimensions": ["Quarter"],
        "period_sensitive": False,
        "goal_label": "Quarterly target",
    },
    "EXE-09": {
        "name": "Open pipeline by vertical",
        "definition": "Open TCV by account vertical, split Qualify-or-later versus Identify.",
        "calculation": "SUM(open tcv_usd) GROUP BY vertical, qualified (Qualify+) vs Identify.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily",
        "dimensions": ["Vertical"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "EXE-10": {
        "name": "Deals needing attention",
        "definition": "Open opportunities with TCV at or above threshold (default $2M) and days in "
        "current stage over 60 (Ageing) or over 90 (Stalled). Days in stage = today minus date "
        "the current stage was entered.",
        "calculation": "open AND tcv_usd ≥ threshold AND days_in_stage > 60; flag Ageing (61–90) / "
        "Stalled (>90). Past-dated open deals (DQ-02) are also listed.",
        "sources": ["SRC-01"],
        "owner": "Client partners",
        "refresh": "Daily",
        "dimensions": ["Owner", "Account", "Stage"],
        "period_sensitive": False,
        "goal_label": "60 days in stage or fewer",
    },
    "PIP-01": {
        "name": "Stage funnel and conversion",
        "definition": "Open opportunities (count and TCV) at each stage, with stage-to-stage "
        "conversion: opportunities that reached the next stage divided by those that reached "
        "this stage, for opportunities created in the trailing four quarters.",
        "calculation": "reached(s) = COUNT(DISTINCT opportunity with a stage-history row at s); "
        "conversion(s → s+1) = reached(s+1) ÷ reached(s); trailing 4 quarters by created date.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily; weekly snapshot",
        "dimensions": ["Stage", "Vertical", "Practice", "Platform"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "PIP-02": {
        "name": "Pipeline ageing",
        "definition": "Open opportunities by stage and days in current stage bucket "
        "(0–30 / 31–60 / 61–90 / over 90). Over 90 days is Stalled. Buckets are admin-configurable.",
        "calculation": "days_in_stage = today − date the current stage was entered; COUNT and "
        "SUM(tcv_usd) per stage × ref_bucket.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily; weekly snapshot",
        "dimensions": ["Stage", "Practice", "Platform"],
        "period_sensitive": False,
        "goal_label": "60 days in stage or fewer",
    },
    "PIP-03": {
        "name": "Pipeline by practice",
        "definition": "Open TCV by practice, from opportunity line items, split into the "
        "opportunity's lead practice and contributing practices.",
        "calculation": "SUM(line-item amount in USD) of open opportunities GROUP BY practice, "
        "lead vs contributing.",
        "sources": ["SRC-01"],
        "owner": "Practice leads",
        "refresh": "Daily",
        "dimensions": ["Practice"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "PIP-04": {
        "name": "Pipeline by platform",
        "definition": "Open TCV by primary technology platform, split Qualify-or-later versus Identify.",
        "calculation": "SUM(open tcv_usd) GROUP BY primary_platform, qualified (Qualify+) vs Identify.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily",
        "dimensions": ["Platform"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "PIP-05": {
        "name": "Deal-size distribution",
        "definition": "Open opportunities (count and TCV) by deal-size band. Bands are admin-configurable.",
        "calculation": "COUNT and SUM(tcv_usd) of open opportunities per ref_size_band.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily",
        "dimensions": ["Size band"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "PIP-06": {
        "name": "Opportunity register",
        "definition": "Every open opportunity within the caller's scope, sortable, searchable "
        "and exportable; ageing and stalled deals carry a text flag.",
        "calculation": "open opportunities; flag = Ageing (61–90 days in stage) / Stalled "
        "(over 90) / Past close date.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily",
        "dimensions": ["Stage", "Account", "Owner"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "PIP-07": {
        "name": "Week-over-week stage movement",
        "definition": "Change in open pipeline between the two latest weekly snapshots: "
        "created, advanced, regressed, slipped (same stage, close date passed or moved out) "
        "and closed.",
        "calculation": "Compare fact_opportunity_snapshot at the latest and previous Monday per "
        "opportunity; classify by stage order and close date.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Weekly snapshot (Mon 00:00 IST)",
        "dimensions": ["Movement type"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "PUR-01": {
        "name": "Win rate by quarter",
        "definition": "Closed Won deals divided by Closed Won plus Closed Lost, by close quarter "
        "over the last eight quarters. No-bid and client-cancelled deals are excluded. The headline "
        "is the trailing four quarters.",
        "calculation": "count(won) / count(won + lost) grouped by close quarter; a value-weighted "
        "variant divides won TCV by decided TCV.",
        "sources": ["SRC-01"],
        "owner": "GTM Lead",
        "refresh": "Daily, refreshed by 07:00 IST",
        "dimensions": ["Close quarter"],
        "period_sensitive": False,
        "goal_label": "Win-rate goal",
    },
    "PUR-02": {
        "name": "Loss reasons",
        "definition": "Closed Lost deals over the last four quarters by the loss reason recorded in "
        "CRM; deals with no reason are shown as Not recorded. The share is of all lost deals.",
        "calculation": "count(lost) grouped by coalesce(loss_reason, 'Not recorded'); the most "
        "frequent recorded reason is highlighted.",
        "sources": ["SRC-01"],
        "owner": "Solutions lead",
        "refresh": "Daily, refreshed by 07:00 IST",
        "dimensions": ["Loss reason"],
        "period_sensitive": False,
        "goal_label": None,
    },
    "PUR-03": {
        "name": "Win rate by deal source",
        "definition": "Win rate and share of decided deals by deal source (Client RFP, Proactive, "
        "Partner-sourced, Campaign / Marketing, Account expansion) over the last four quarters.",
        "calculation": "count(won) / count(won + lost) grouped by lead source.",
        "sources": ["SRC-01"],
        "owner": "GTM Lead",
        "refresh": "Daily, refreshed by 07:00 IST",
        "dimensions": ["Deal source"],
        "period_sensitive": False,
        "goal_label": "Win-rate goal",
    },
    "PUR-04": {
        "name": "Bid discipline",
        "definition": "Of RFPs that reached the bid/no-bid gate in the last four quarters: the "
        "no-bid rate, the win rate of pursued RFPs, and the share submitted within SLA. A callout "
        "fires when both the no-bid rate and the pursued win rate are below target.",
        "calculation": "no-bid = count(decision = no_bid) / count(RFPs); pursued win rate = won / "
        "(won + lost) among bid decisions; on-time = submitted on or before received + SLA days.",
        "sources": ["SRC-01", "SRC-03"],
        "owner": "Solutions lead",
        "refresh": "Nightly (bid tool), daily (CRM)",
        "dimensions": ["Decision"],
        "period_sensitive": False,
        "goal_label": "No-bid rate target",
    },
    "PUR-05": {
        "name": "Orals conversion",
        "definition": "Of pursuits that reached orals, the share that were won (Won divided by "
        "Won plus Lost); deals still open are shown separately.",
        "calculation": "count(won) / count(won + lost) among pursuits flagged orals_reached.",
        "sources": ["SRC-01", "SRC-03"],
        "owner": "Solutions lead",
        "refresh": "Nightly (bid tool), daily (CRM)",
        "dimensions": ["Outcome"],
        "period_sensitive": False,
        "goal_label": "Orals conversion goal",
    },
    "PUR-06": {
        "name": "Margin at bid vs delivery",
        "definition": "Margin priced into the final bid compared with the margin realised in delivery, "
        "for won deals that have been delivering for at least a quarter. Restricted to GTM Lead, "
        "Leadership and Finance.",
        "calculation": "erosion = TCV-weighted (bid margin − delivery margin) over won deals with project "
        "financials; shown by close quarter.",
        "sources": ["SRC-01", "SRC-05", "SRC-04"],
        "owner": "Finance with GTM Lead",
        "refresh": "Nightly (pricing), monthly (finance)",
        "dimensions": ["Quarter"],
        "period_sensitive": False,
        "goal_label": "Delivery margin within 3 points of bid margin",
        "restricted": True,
    },
    "OFF-01": {
        "name": "Pipeline and wins by offering",
        "definition": "Open pipeline and closed-won TCV per offering. Capability-led deals are a separate "
        "bucket and untagged deals are shown apart, counted against the offering-led share.",
        "calculation": "SUM(tcv_usd) by offering for open deals and for Closed Won deals closed in the "
        "period; offering-led share = offering-tagged TCV ÷ all TCV.",
        "sources": ["SRC-01"],
        "owner": "Offering portfolio lead",
        "refresh": "Daily",
        "dimensions": ["Offering", "Practice", "Vertical", "Platform"],
        "period_sensitive": True,
        "goal_label": "Offering-led share of pipeline and wins",
    },
    "OFF-02": {
        "name": "Attach rate and practices per deal",
        "definition": "Share of Closed Won deals that include more than one practice, plus the "
        "distribution of practices per deal.",
        "calculation": "count(won deals with ≥2 practice line items) ÷ count(won deals) in the period.",
        "sources": ["SRC-01"],
        "owner": "Offering portfolio lead",
        "refresh": "Daily",
        "dimensions": ["Practices per deal"],
        "period_sensitive": True,
        "goal_label": "Attach rate goal",
    },
    "OFF-03": {
        "name": "AI-led validation split",
        "definition": "Open pipeline TCV split into AI-led and validated, AI-led and not validated, and "
        "not AI-led. The unvalidated AI-led value is called out with the largest deals.",
        "calculation": "SUM(tcv_usd) of open deals by validation state; validated = AI-led with a "
        "Validated record in the AI validation register matching the deal's validation ID.",
        "sources": ["SRC-01", "SRC-13"],
        "owner": "Offering governance",
        "refresh": "Daily (CRM), nightly (register)",
        "dimensions": ["Validation state"],
        "period_sensitive": False,
        "goal_label": "No AI-led value left unvalidated",
    },
    "OFF-04": {
        "name": "Asset reuse",
        "definition": "Uses of each knowledge asset in proposals over the last 12 months. Assets with "
        "fewer than 8 uses are flagged low reuse; assets not refreshed for over 180 days are flagged "
        "refresh due.",
        "calculation": "count(proposal asset uses in the last 12 months) per asset; flags use the "
        "low-reuse and refresh-due settings.",
        "sources": ["SRC-12", "SRC-03"],
        "owner": "Offering portfolio lead",
        "refresh": "Weekly (repository), nightly (bid tool)",
        "dimensions": ["Asset", "Asset type"],
        "period_sensitive": False,
        "goal_label": "Assets with enough reuse and a recent refresh",
    },
    "OFF-05": {
        "name": "Demos, accelerators and solutions developed",
        "definition": "Assets released this fiscal year against the build plan pace, with items in "
        "development by target quarter, the share of released assets used in a pursuit, and mean "
        "build time in weeks. Items missing an Asset ID or type are excluded (DQ-09).",
        "calculation": "released ÷ plan pace (planned releases of completed quarters plus the current "
        "quarter pro-rated); reuse = released assets used in a proposal ÷ released assets.",
        "sources": ["SRC-17", "SRC-12", "SRC-03", "SRC-02"],
        "owner": "Offering portfolio lead",
        "refresh": "Nightly",
        "dimensions": ["Practice", "Platform", "Vertical", "Asset type"],
        "period_sensitive": False,
        "goal_label": "At or above build plan pace (On track ≥90% of pace)",
    },
    "ACC-01": {
        "name": "Practice penetration matrix",
        "definition": "For each account and practice: Sold (a Closed Won deal this fiscal year includes "
        "the practice), Open (an open deal includes it) or Not addressed.",
        "calculation": "state from practice line items of this fiscal year's Closed Won and open deals.",
        "sources": ["SRC-01"],
        "owner": "Client partners",
        "refresh": "Daily",
        "dimensions": ["Account", "Practice"],
        "period_sensitive": False,
        "goal_label": "More practices sold or pursued per account",
    },
    "ACC-02": {
        "name": "Whitespace pursued",
        "definition": "Share of whitespace (practices not yet sold) that is being pursued through an "
        "open deal.",
        "calculation": "Open cells ÷ (Open cells + Not addressed cells) across accounts in scope.",
        "sources": ["SRC-01"],
        "owner": "Client partners",
        "refresh": "Daily",
        "dimensions": ["Account", "Practice"],
        "period_sensitive": False,
        "goal_label": "Whitespace pursued goal",
    },
    "ACC-03": {
        "name": "Expansion vs new logo",
        "definition": "Closed Won TCV split between existing accounts (a booking in the 24 months "
        "before close) and new logos.",
        "calculation": "SUM(tcv_usd) of Closed Won deals in the period; expansion when the account has "
        "booking history in the 24 months before the close date.",
        "sources": ["SRC-01", "SRC-04"],
        "owner": "GTM Lead",
        "refresh": "Daily (CRM), monthly (finance)",
        "dimensions": ["Account type"],
        "period_sensitive": True,
        "goal_label": "Expansion share of bookings",
    },
    "ACC-04": {
        "name": "Account-plan health",
        "definition": "Strategic accounts by plan status: Current (reviewed within 90 days), Needs "
        "update (91–120 days) or Overdue (over 120 days or no plan).",
        "calculation": "days since last_review_date, banded by the account-plan health settings.",
        "sources": ["SRC-14"],
        "owner": "Client partners",
        "refresh": "Weekly",
        "dimensions": ["Account", "Plan status"],
        "period_sensitive": False,
        "goal_label": "Every strategic account plan current",
    },
    "PAR-01": {
        "name": "Pipeline by partner",
        "definition": "Open pipeline TCV tagged to a partner, split between deals the partner sourced "
        "and deals it influenced.",
        "calculation": "SUM(tcv_usd) of open deals by partner and partner role (Sourced / Influenced).",
        "sources": ["SRC-01", "SRC-08"],
        "owner": "Alliance managers",
        "refresh": "Daily (CRM), monthly (partner portal)",
        "dimensions": ["Partner", "Partner role"],
        "period_sensitive": False,
        "goal_label": "Partner-sourced pipeline growth",
    },
    "PAR-02": {
        "name": "Co-sell performance",
        "definition": "Win rate of deals with a partner against deals without one, and the share of "
        "bookings with partner involvement.",
        "calculation": "won ÷ (won + lost) for deals with and without a partner in the period; "
        "partner share = won TCV with a partner ÷ all won TCV.",
        "sources": ["SRC-01", "SRC-08"],
        "owner": "Alliance managers",
        "refresh": "Daily (CRM), monthly (partner portal)",
        "dimensions": ["Partner involvement"],
        "period_sensitive": True,
        "goal_label": "Win rate with partner above win rate without",
    },
    "PAR-03": {
        "name": "Certification status",
        "definition": "Active partner certifications held by Moment people against the number required "
        "for each partner tier, with learners still in progress in the LMS.",
        "calculation": "count(unexpired certifications) ÷ required certifications, per partner.",
        "sources": ["SRC-08", "SRC-09"],
        "owner": "Alliance managers",
        "refresh": "Monthly (partner portal), weekly (LMS)",
        "dimensions": ["Partner"],
        "period_sensitive": False,
        "goal_label": "Required certifications held (On track ≥90%)",
    },
    "CAP-01": {
        "name": "Architect load",
        "definition": "Open pursuits per Solution Architect. An architect is the person holding the "
        "Solution Architect role on an open deal at Qualify, Propose or Orals. Healthy is up to 3, "
        "stretched is 4 and over capacity is 5 or more.",
        "calculation": "count(open deals at Qualify/Propose/Orals) per Solution Architect on the "
        "opportunity team; banded from the CAP-01 thresholds.",
        "sources": ["SRC-01", "SRC-06"],
        "owner": "Solutions lead",
        "refresh": "Daily (CRM), weekly (resource management)",
        "dimensions": ["Architect"],
        "period_sensitive": False,
        "goal_label": "No architect over capacity (healthy up to 3 open pursuits)",
    },
    "CAP-02": {
        "name": "RFP turnaround and SLA",
        "definition": "Days from RFP received to proposal submitted, and the share of submissions "
        "inside the SLA agreed for that RFP, by quarter of submission.",
        "calculation": "avg(submitted − received) and count(submitted ≤ received + SLA) ÷ count(submitted).",
        "sources": ["SRC-03", "SRC-01"],
        "owner": "Solutions lead",
        "refresh": "Nightly",
        "dimensions": ["Quarter"],
        "period_sensitive": False,
        "goal_label": "Submissions within SLA (On track ≥80%)",
    },
    "CAP-03": {
        "name": "Cost of sale",
        "definition": "Pursuit effort priced at the finance cost rate, as a share of the TCV of the "
        "pursuits it was spent on (won and lost). Restricted to GTM Lead, Leadership and Finance.",
        "calculation": "SUM(timesheet hours × role cost rate) ÷ SUM(TCV) over pursuits decided in the "
        "last four quarters.",
        "sources": ["SRC-07", "SRC-04", "SRC-06", "SRC-01"],
        "owner": "Finance with Solutions lead",
        "refresh": "Weekly (timesheets), monthly (cost rates)",
        "dimensions": ["Quarter"],
        "period_sensitive": False,
        "goal_label": "At or below 2% of TCV",
        "restricted": True,
    },
    "CAP-04": {
        "name": "Proposal quality score",
        "definition": "Average gate-review quality score (1 to 5) of pursued proposals, compared for "
        "won and lost deals.",
        "calculation": "avg(quality_score) by outcome over pursued deals decided in the last four quarters.",
        "sources": ["SRC-03", "SRC-01"],
        "owner": "Solutions lead",
        "refresh": "Nightly",
        "dimensions": ["Outcome"],
        "period_sensitive": False,
        "goal_label": "Won proposals score higher than lost ones",
    },
    "MKT-01": {
        "name": "Thought leadership volume & reach",
        "definition": "Count of published POVs and major thought-leadership assets per quarter, "
        "alongside engagement (downloads and engaged visits).",
        "calculation": "count(assets) WHERE published_date IN quarter; sum(downloads), sum(engaged_visits).",
        "sources": ["SRC-11"],
        "owner": "Marketing lead",
        "refresh": "Weekly",
        "dimensions": ["Quarter", "Practice", "Platform", "Asset Type"],
        "period_sensitive": False,
        "goal_label": "Trend metric",
    },
    "MKT-02": {
        "name": "Discovery workshop conversion",
        "definition": "Conversion of client discovery workshops into opportunities created within "
        "90 days, qualified opportunities and wins.",
        "calculation": "workshops held -> opportunities created within 90 days -> qualified -> won; "
        "conversion rate = qualified / workshops held.",
        "sources": ["SRC-01"],
        "owner": "Marketing lead with Sales Operations",
        "refresh": "Daily",
        "dimensions": ["Stage", "Practice", "Platform", "Vertical"],
        "period_sensitive": True,
        "goal_label": "≥50% workshop-to-qualified conversion (On track ≥50%; Watch 35–50%)",
    },
    "MKT-03": {
        "name": "Campaign-sourced pipeline",
        "definition": "Pipeline TCV created in the period where a campaign is the primary source, "
        "by campaign and quarter.",
        "calculation": "SUM(tcv_usd) WHERE campaign_id IS NOT NULL AND primary_source = TRUE "
        "AND created_date IN period.",
        "sources": ["SRC-01", "SRC-10"],
        "owner": "Marketing lead",
        "refresh": "Daily",
        "dimensions": ["Quarter", "Campaign", "Practice", "Platform"],
        "period_sensitive": True,
        "goal_label": "Trend & campaign attribution",
    },
    "MKT-04": {
        "name": "Analyst positioning",
        "definition": "Placement and direction of travel in major analyst evaluations "
        "(Forrester Wave, Gartner Magic Quadrant, IDC MarketScape, Everest Group PEAK Matrix).",
        "calculation": "Current placement vs prior evaluation placement, with direction icon and text "
        "(↑ Improved, → Maintained, ↓ Declined).",
        "sources": ["SRC-15"],
        "owner": "Marketing lead with Analyst Relations",
        "refresh": "Quarterly / as published",
        "dimensions": ["Firm", "Practice", "Platform", "Direction"],
        "period_sensitive": False,
        "goal_label": "Leader / Strong Performer with positive or stable trajectory",
    },
    "ADM-01": {
        "name": "Mandatory-field completeness",
        "definition": "Share of qualified opportunities (Qualify or later) that have an offering tag, "
        "lead practice, primary platform, deal source and owner.",
        "calculation": "complete / qualified per ISO week; go-live gate is 95% for two consecutive weeks.",
        "sources": ["SRC-01"],
        "owner": "Sales Operations",
        "refresh": "Daily (CRM)",
        "dimensions": ["Field"],
        "period_sensitive": False,
        "goal_label": "Go-live gate",
    },
}


def get(metric_id: str) -> dict:
    try:
        return METRICS[metric_id]
    except KeyError as exc:  # every widget must carry a registered ID (FR-GEN-07)
        raise KeyError(f"Metric {metric_id} is not registered in semantic/definitions.py") from exc


def is_restricted(metric_id: str) -> bool:
    """Restricted metrics (PUR-06, CAP-03) are visible only to restricted roles, in every output."""
    return bool(METRICS.get(metric_id, {}).get("restricted"))


def sources_for(metric_id: str) -> list[dict]:
    return [{"source_id": s, "name": SOURCE_NAMES[s]} for s in get(metric_id)["sources"]]
