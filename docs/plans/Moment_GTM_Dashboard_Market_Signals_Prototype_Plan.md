# Moment GTM Dashboard — Market Signals Module: Prototype Implementation Plan

> Companion to the Shared doc for stack, architecture, project structure, global UI/governance and
> roles. · RSD §4.9, §5 (MKT-01..04).

## 1. Context & scope
Market signals gives Marketing the view of demand-generation signals: thought-leadership output and
engagement, the workshop funnel, campaign-sourced pipeline, and analyst positioning. Scope =
FR-MKT-01..04, metrics MKT-01..04. This is the most MCP-rich module (Adobe sources).

## 2. Functional requirements & metrics

| Requirement | Metric | Widget | Endpoint |
|---|---|---|---|
| FR-MKT-01 thought-leadership output & engagement | MKT-01 | ThoughtLeadership | `GET /api/market/thought-leadership` |
| FR-MKT-02 workshop funnel & conversion | MKT-02 | WorkshopFunnel | `GET /api/market/workshop-funnel` |
| FR-MKT-03 campaign-sourced pipeline | MKT-03 | CampaignPipeline | `GET /api/market/campaign-pipeline` |
| FR-MKT-04 analyst positioning | MKT-04 | AnalystPositioning (prev vs current placement) | `GET /api/market/analyst-positioning` |

Priorities: FR-MKT-01/02/03 **Should**; FR-MKT-04 **Could**. Workshop conversion goal 50%
(opps created within 90 days and linked to a workshop ÷ workshops held).

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-01 CRM | MKT-02, MKT-03 | Salesforce REST/Bulk/CDC (Campaign, CampaignInfluence, Activity type) | No Salesforce MCP — direct API | `raw_crm_*` |
| SRC-10 Marketing automation | MKT-03 | **Adobe Marketo Engage / Journey Optimizer**; Salesforce Marketing Cloud | **Adobe Journey Optimizer MCP / Adobe Marketing Agent MCP** | `raw_mktg_*` |
| SRC-11 Web CMS & analytics | MKT-01 | **Adobe Experience Manager**; **Adobe Analytics / Customer Journey Analytics** | **Adobe Experience Manager MCP + Adobe Customer Journey Analytics MCP** | `raw_web_*` |
| SRC-15 Analyst relations tracker | MKT-04 | SharePoint List / governed Excel via **Microsoft Graph** | **Microsoft 365 MCP** | `raw_analyst_evaluation` |

MCP-rich: **Adobe Journey Optimizer / Adobe Marketing Agent** (SRC-10), **Adobe Experience Manager +
Adobe Customer Journey Analytics** (SRC-11), **Microsoft 365** (SRC-15) are all directly usable
here — the clearest fit for MCP-based retrieval in the whole dashboard.

## 4. Data-store & extract schema (module-specific)
- **Raw:** `raw_mktg_campaign` + `raw_mktg_campaign_member` (nightly, SRC-10: membership/responses
  synced to CRM campaigns), `raw_web_content_asset` + `raw_web_engagement_metric` (weekly, SRC-11:
  POV publications, downloads/engaged visits), `raw_analyst_evaluation` (on change, SRC-15:
  evaluations, placements, dates).
- **Conformed:** `fact_campaign_member`, `fact_content_engagement`, `fact_analyst_eval`. Reused:
  `fact_opportunity` (campaign-sourced attribution, workshop-linked activities), `dim_date`.

## 5. Roles / personas with access (RSD §9)

| Role | Market signals access | Scope |
|---|---|---|
| GTM Lead, Moment leadership, Finance | Yes | All |
| Marketing | Yes (default view) | Campaign-/workshop-linked opps |
| Practice lead | Yes (all modules) | Own practice full; others aggregated |
| Client partner, Solutions, Alliance | **No** | — |

No restricted metrics. RLS applies.

## 6. UI requirements (module-specific)
- Thought-leadership: POVs published per quarter + engagement (downloads/engaged visits).
- Workshop funnel: workshops → opps created → qualified → won, with conversion rate and pipeline
  originated (funnel labelled at each stage).
- Campaign pipeline: TCV created where a campaign is primary source, by quarter.
- Analyst positioning: latest placement with prior placement and change (text + direction icon).
- Note (Appendix A): in the mockup MKT-01/02/04 were fixed sample; prototype computes MKT-03 live and
  may seed MKT-01/02/04 from synthetic Adobe-style extracts. Metric-info popover cites SRC-10/11/15.

## 7. Governance notes
Owners: MKT-01/02/03 Marketing; MKT-04 Marketing (AR). Campaign taxonomy and analyst-evaluation list
are reference data. Engagement data from SRC-11 is weekly; freshness banner reflects cadence.

## 8. Project structure additions
- Backend: `semantic/metrics/mkt.py`, `api/routes/market_signals.py`, `schemas/market_signals.py`.
- Frontend: `routes/MarketSignals.tsx`; `components/widgets/market/` (ThoughtLeadership,
  WorkshopFunnel, CampaignPipeline, AnalystPositioning); `hooks/useMarketData.ts`.

## 9. Task splitup
1. Generator: campaigns + members, workshop activities linked to opps, POV content + engagement,
   analyst evaluations with prior/current placements.
2. Build `fact_campaign_member`, `fact_content_engagement`, `fact_analyst_eval`.
3. `mkt.py`: MKT-01 output/engagement, MKT-02 workshop funnel/conversion, MKT-03 campaign-sourced
   pipeline, MKT-04 analyst change.
4. API + schemas.
5. Frontend widgets (`moment-gtm-reusable-components` + `dataviz` skills; compose shared
   `FunnelChart`, `KpiCard`, `Sparkline`); funnel + positioning change indicators.
6. Tests: `test_metrics_mkt.py`; Playwright UAT FR-MKT-01/02/03 (Should); role test (only Marketing
   + leadership/Finance/GTM/practice reach the module, AC-03).

## 10. Verification
- MKT-03 campaign-sourced pipeline reconciles to CRM campaign attribution within 0.5% (AC-01).
- Workshop conversion matches seeded workshop→opp links within 90 days.
- Adobe/M365 MCP provenance recorded in `definitions.py`; freshness reflects SRC-11 weekly cadence.
