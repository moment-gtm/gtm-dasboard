# Moment GTM Dashboard — Pursuits & Wins Module: Prototype Implementation Plan

> Companion to the Shared doc (`..._Shared_Architecture_Schema_Governance.md`) for stack,
> architecture, project structure, global UI/governance and roles. · RSD §4.4, §5 (PUR-01..06).

## 1. Context & scope
Pursuits & wins measures win performance and bid discipline: win-rate trends, loss reasons, deal
source mix, bid discipline (no-bid/pursued win/orals conversion) and — for restricted roles — the
margin at bid vs delivery. Scope = FR-PUR-01..05, metrics PUR-01..06. **PUR-06 is a restricted
metric** (margin), visible only to GTM Lead, leadership and Finance.

## 2. Functional requirements & metrics

| Requirement | Metric(s) | Widget | Endpoint |
|---|---|---|---|
| FR-PUR-01 win rate by quarter (count & value) | PUR-01 | WinRateTrend | `GET /api/pursuits/win-rate` |
| FR-PUR-02 loss reasons | PUR-02 | LossReasons (highlight most frequent) | `GET /api/pursuits/loss-reasons` |
| FR-PUR-03 source mix & win rate | PUR-03 | SourceMix (Proactive/RFP/Partner/Campaign) | `GET /api/pursuits/source-mix` |
| FR-PUR-04 bid discipline | PUR-04, PUR-05 | BidDiscipline (+ rule-based callout) | `GET /api/pursuits/bid-discipline` |
| FR-PUR-05 margin at bid vs delivery (**restricted**) | PUR-06 | MarginBidVsDelivery | `GET /api/pursuits/margin` (role-gated) |

Priorities: FR-PUR-01..04 **Must**; FR-PUR-05 **Should**. No-bids and client-cancelled excluded
from win rate. Bid discipline callout fires when a low no-bid rate coincides with a low win rate.
Thresholds (Appendix B): win rate 40%; no-bid rate ≥20%; pursued-RFP win 35%; orals conversion 50%.

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-01 CRM | PUR-01..03, PUR-06 | Salesforce REST/Bulk/CDC (Opportunity, loss reason, source) | No Salesforce MCP — direct API | `raw_crm_*` |
| SRC-03 Bid & proposal mgmt | PUR-04, PUR-05 | Responsive(RFPIO)/Loopio vendor API, or SharePoint pursuit sites via **Microsoft Graph** | **Microsoft 365 MCP** (SharePoint fallback) | `raw_bid_*` |
| SRC-05 Deal pricing | PUR-06 | Pricing tool API / governed workbook | No MCP — direct API/file | `raw_pricing_version` |
| SRC-04 Finance ERP | PUR-06 | SAP S/4HANA OData / finance DW (monthly) | No MCP — direct extract | `raw_finance_project_financials` |

MCP note: when the bid tool is SharePoint/M365-based, use the **Microsoft 365 MCP** (Graph) to read
pursuit lists; vendor tools (Responsive/Loopio) and pricing/Finance use direct APIs.

## 4. Data-store & extract schema (module-specific)
- **Raw:** `raw_bid_pursuit` (nightly: RFP received/submitted, bid/no-bid decision, SLA target,
  orals reached, gate score — **must carry CRM Opportunity ID**), `raw_pricing_version` (on
  approval: approved bid margin % — carries Opportunity ID), `raw_finance_project_financials`
  (monthly: actual project margin by project→opportunity).
- **Conformed:** `fact_pursuit` (one row/pursuit linked to opportunity), `fact_pricing`
  (opportunity × pricing version), `fact_project_financials` (project × month). Unmatched
  bid/pricing/finance rows → matching queue (DQ-04).
- Reused: `fact_opportunity`, `dim_practice`, loss-reason picklist reference.

## 5. Roles / personas with access (RSD §9)

| Role | Access | PUR-06 (restricted margin) |
|---|---|---|
| GTM Lead, Moment leadership, Finance | Yes | **Yes** |
| Solutions lead & architects | Yes | **No** (PUR-06 hidden) |
| Practice lead | Yes (all modules) | No |
| Client partner, Alliance manager, Marketing | **No** | — |

RLS + restricted-metric gating enforced in the semantic layer and on exports/alerts (AC-03).

## 6. UI requirements (module-specific)
- Win-rate chart offers count and value variants against goal.
- Loss-reasons chart highlights the single most frequent reason (label + colour).
- Bid-discipline panel shows each metric with status badge and renders the rule-based callout text.
- Margin panel renders only for restricted roles; for others it is absent (not greyed) and the
  access is logged (NFR-07). Currency $M to 1 dp; metric-info popover on every panel.

## 7. Governance notes
Owners: PUR-01/03 GTM Lead; PUR-02/04/05 Solutions lead; PUR-06 Finance. Loss-reason and no-bid
picklists are controlled reference data (FR-ADM-03). PUR-06 requires InfoSec approval (OQ-08).

## 8. Project structure additions
- Backend: `semantic/metrics/pur.py`, `api/routes/pursuits.py`, `schemas/pursuits.py`; RLS gate on
  the margin endpoint via `semantic/rls.py`.
- Frontend: `routes/Pursuits.tsx`; `components/widgets/pursuits/` (WinRateTrend, LossReasons,
  SourceMix, BidDiscipline, MarginBidVsDelivery); `hooks/usePursuitsData.ts`; `api/pursuits.ts`.

## 9. Task splitup
1. Extend generator: closed-won/lost outcomes, loss reasons, lead-source categories, bid records
   (RFP dates, no-bid, orals, gate scores), pricing margins and (monthly) delivery margins.
2. Build `fact_pursuit`, `fact_pricing`, `fact_project_financials`; wire matching queue (DQ-04).
3. `pur.py`: PUR-01 (per-quarter win rate), PUR-02 (loss reasons), PUR-03 (source mix + win rate),
   PUR-04 (bid discipline + callout rule), PUR-05 (orals conversion), PUR-06 (bid vs delivery margin).
4. API + schemas; role-gate `/api/pursuits/margin`.
5. Frontend widgets (`moment-gtm-reusable-components` + `dataviz` skills; compose shared chart
   primitives, `StatusBadge`, `DrilldownPanel`); conditional render of margin panel by role
   (`state/role.ts` + `require_role`).
6. Tests: `test_metrics_pur.py`; `test_rls.py` asserting PUR-06 hidden for non-restricted roles and
   absent from their exports (AC-03); Playwright UAT FR-PUR-01..04 (Must).

## 10. Verification
- Win rate excludes no-bid/cancelled and reconciles to CRM outcomes within 0.5% (AC-01).
- Bid-discipline callout appears only when both no-bid and win rates are low (seeded case).
- Margin panel visible to Finance/GTM/leadership only; access written to `audit_log`.
- UAT scripts pass for all Must requirements (AC-02).
