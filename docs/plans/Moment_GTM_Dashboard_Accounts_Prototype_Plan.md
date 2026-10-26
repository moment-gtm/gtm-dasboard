# Moment GTM Dashboard — Accounts Module: Prototype Implementation Plan

> Companion to the Shared doc for stack, architecture, project structure, global UI/governance and
> roles. · RSD §4.6, §5 (ACC-01..04).

## 1. Context & scope
Accounts gives client partners the strategic-account view: practice penetration, whitespace,
expansion vs new-logo, and account-plan health. Supports OBJ-02 (leading indicators) and the
whitespace-pursuit goal. Scope = FR-ACC-01..05, metrics ACC-01..04.

## 2. Functional requirements & metrics

| Requirement | Metric | Widget | Endpoint |
|---|---|---|---|
| FR-ACC-01 penetration matrix (accounts × 8 practices) | ACC-01 | PenetrationMatrix (Sold/Open/Not addressed) | `GET /api/accounts/penetration` |
| FR-ACC-02 whitespace summary | ACC-02 | WhitespaceSummary (share pursued) | `GET /api/accounts/whitespace` |
| FR-ACC-03 expansion vs new logo | ACC-03 | ExpansionVsNewLogo | `GET /api/accounts/expansion` |
| FR-ACC-04 account-plan status | ACC-04 | AccountPlanHealth (Current/Needs update/Overdue) | `GET /api/accounts/plan-health` |
| FR-ACC-05 account detail panel | ACC-01 | AccountDetailPanel (opps; keyboard; Esc to close) | `GET /api/accounts/{id}/opportunities` |

Priorities: FR-ACC-01/02/03/05 **Must**; FR-ACC-04 **Should**. Thresholds: whitespace pursued 40%
(Appendix B). Expansion = account had a prior booking in the 24 months before close; else new logo.
Plan health: Current ≤90 days, Needs update 91–120, Overdue >120 or none.

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-01 CRM | ACC-01, ACC-02, ACC-03 | Salesforce REST/Bulk/CDC (Account, industry→vertical, opportunities, practice line items) | No Salesforce MCP — direct API | `raw_crm_*` |
| SRC-14 Account planning | ACC-04 | CRM account-plan object **or** SharePoint via **Microsoft Graph** | **Microsoft 365 MCP** (SharePoint) | `raw_account_plan` |
| SRC-04 Finance ERP | ACC-03 | SAP/Oracle/finance DW booking history (monthly) | No MCP — direct extract | `raw_finance_contract` |

MCP: **Microsoft 365 MCP** usable for the account-planning source when SharePoint-based.

## 4. Data-store & extract schema (module-specific)
- **Raw:** `raw_account_plan` (weekly, SRC-14: plan status, last review date, whitespace opps),
  `raw_finance_contract` (monthly, SRC-04: booking history by account for 24-month expansion test).
- **Conformed:** `dim_account_plan` (one/strategic account), reuse `dim_account` (strategic flag,
  vertical, hierarchy — subsidiaries roll to parent), `fact_opportunity`,
  `bridge_opportunity_practice`, `dim_practice` (the 8 practices).
- Penetration is computed account × practice (Sold if any Closed-Won in FY incl. that practice;
  Open if open opp incl. it; else Not addressed). Whitespace = Open ÷ (Open + Not addressed).

## 5. Roles / personas with access (RSD §9)

| Role | Accounts access | Scope |
|---|---|---|
| GTM Lead, Moment leadership, Finance | Yes | All |
| Practice lead | Yes | Own practice full; others aggregated |
| Client partner / account lead | Yes (default view) | **Assigned accounts only** |
| Solutions, Alliance, Marketing | **No** | — |

No restricted metrics. RLS by account is central here (client partners see only assigned accounts).

## 6. UI requirements (module-specific)
- Penetration matrix: each cell Sold/Open/Not addressed with text + colour (never colour alone);
  per-account FY bookings, open pipeline and whitespace count.
- Selecting an account opens the **detail panel** (FR-ACC-05): all opportunities with status,
  practices, TCV, close quarter; **keyboard accessible, closes with Escape** (NFR-08).
- Plan-health summary + per-account status with text labels. Metric-info popover per panel.

## 7. Governance notes
Owners: ACC-01/02/04 Client partners; ACC-03 GTM Lead. Strategic account list is reference data
(FR-ADM-03); OQ-07 (owner/refresh cadence) must be resolved. Vertical mapping is admin-maintained.

## 8. Project structure additions
- Backend: `semantic/metrics/acc.py`, `api/routes/accounts.py`, `schemas/accounts.py`.
- Frontend: `routes/Accounts.tsx`; `components/widgets/accounts/` (PenetrationMatrix,
  WhitespaceSummary, ExpansionVsNewLogo, AccountPlanHealth, AccountDetailPanel using Radix Dialog);
  `hooks/useAccountsData.ts`.

## 9. Task splitup
1. Generator: strategic accounts with vertical + hierarchy; opportunities across practices; account
   plans with review dates; 24-month booking history for expansion classification.
2. Build `dim_account_plan`; ensure `dim_account` strategic flag + hierarchy roll-up.
3. `acc.py`: ACC-01 penetration, ACC-02 whitespace, ACC-03 expansion/new-logo, ACC-04 plan health.
4. API + schemas incl. per-account opportunity list endpoint.
5. Frontend widgets (`moment-gtm-reusable-components` + `dataviz` skills; compose shared
   `MatrixGrid`, `DrilldownPanel`, `StatusBadge`); accessible detail panel (focus trap, Escape).
6. Tests: `test_metrics_acc.py`; a11y test for the detail panel (axe-core, keyboard); role test that
   client partners see only assigned accounts (AC-03); Playwright UAT FR-ACC-01/02/03/05 (Must).

## 10. Verification
- Penetration cell states and whitespace share reconcile to CRM-derived facts (AC-01).
- Expansion vs new-logo split matches seeded booking history.
- Detail panel fully keyboard operable and closes with Escape (AC-07/NFR-08).
- Client-partner RLS limits rows to assigned accounts, including exports (AC-03).
