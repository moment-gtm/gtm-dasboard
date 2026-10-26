# Moment GTM Dashboard — Solutions Capacity Module: Prototype Implementation Plan

> Companion to the Shared doc for stack, architecture, project structure, global UI/governance and
> roles. · RSD §4.8, §5 (CAP-01..04).

## 1. Context & scope
Solutions capacity gives the solutions lead the pre-sales capacity view: active pursuits per
architect, RFP turnaround and SLA adherence, cost of sale (restricted), and pursuit quality-review
scores. Supports OBJ-04 (no architect over capacity >2 weeks). Scope = FR-CAP-01..04, metrics
CAP-01..04. **CAP-03 (cost of sale) is a restricted metric.**

## 2. Functional requirements & metrics

| Requirement | Metric | Widget | Endpoint |
|---|---|---|---|
| FR-CAP-01 pursuits per architect | CAP-01 | ArchitectLoad (healthy/stretched/over-capacity + callout) | `GET /api/capacity/architect-load` |
| FR-CAP-02 RFP turnaround & SLA | CAP-02 | RfpTurnaround | `GET /api/capacity/rfp-turnaround` |
| FR-CAP-03 cost of sale (**restricted**) | CAP-03 | CostOfSale | `GET /api/capacity/cost-of-sale` (role-gated) |
| FR-CAP-04 pursuit quality score | CAP-04 | QualityScores (by won/lost) | `GET /api/capacity/quality-scores` |

Priorities: FR-CAP-01/02 **Must**; FR-CAP-03 **Should**; FR-CAP-04 **Could**. Capacity (Appendix B):
healthy ≤3, stretched 4, over capacity ≥5. Cost of sale goal ≤2%. Architect = person holding the
Solution Architect role on the opportunity team for open Qualify/Propose/Orals deals.

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-01 CRM | CAP-01 | Salesforce REST/Bulk/CDC (OpportunityTeamMember roles, stages) | No Salesforce MCP — direct API | `raw_crm_*` |
| SRC-03 Bid mgmt | CAP-02, CAP-04 | Responsive/Loopio API or SharePoint via **Microsoft Graph** | **Microsoft 365 MCP** (SharePoint) | `raw_bid_*` |
| SRC-06 Resource mgmt | CAP-01 | Enterprise resource/staffing system API/extract | No MCP — direct API | `raw_resource`, `raw_resource_allocation` |
| SRC-07 Timesheets | CAP-03 | Enterprise timesheet extract (weekly) | No MCP — direct extract | `raw_timesheet_entry` |
| SRC-04 Finance ERP | CAP-03 | Cost rates (finance DW) | No MCP — direct extract | `raw_finance_cost_rate` |

MCP note: **Microsoft 365 MCP** for SharePoint-based bid data; resource/timesheet/finance via direct
APIs/extracts.

## 4. Data-store & extract schema (module-specific)
- **Raw:** `raw_resource` + `raw_resource_allocation` (nightly, SRC-06: architect roster, role,
  practice, allocation %), `raw_timesheet_entry` (weekly, SRC-07: hours to pursuit charge codes —
  **mapped to Opportunity ID**), `raw_finance_cost_rate` (monthly, SRC-04), `raw_bid_gate_review`
  (nightly, SRC-03: gate/red-team scores 1–5), `raw_bid_pursuit` (SLA target & adherence).
- **Conformed:** `fact_resource` (person × week allocation), `fact_pursuit` (turnaround, SLA),
  `fact_gate_review` (pursuit quality score + outcome), cost-of-sale fact
  (pursuit hours × cost rate ÷ TCV). Reused: `fact_opportunity`, `dim_person`, `dim_practice`.

## 5. Roles / personas with access (RSD §9)

| Role | Capacity access | CAP-03 (restricted) |
|---|---|---|
| GTM Lead, Moment leadership, Finance | Yes | **Yes** |
| Solutions lead & architects | Yes (default view) | **No** (CAP-03 hidden) |
| Practice lead | Yes (all modules) | No |
| Client partner, Alliance, Marketing | **No** | — |

RLS + restricted-metric gating on CAP-03 enforced in the semantic layer and on exports (AC-03).

## 6. UI requirements (module-specific)
- Architect-load chart colour-codes stretched/over-capacity **and** names over-capacity architects
  in a text callout (OBJ-04).
- RFP turnaround: mean days + share within RACI SLA, by quarter, with status.
- Cost-of-sale panel renders only for restricted roles; access logged (NFR-07).
- Quality scores split won vs lost. Metric-info popover cites SRC-06/07/03/04.

## 7. Governance notes
Owners: CAP-01/02/04 Solutions lead; CAP-03 Finance. Healthy/stretched/over-capacity limits and SLA
targets are admin reference data (FR-ADM-02). CAP-03 restricted per §9; audit on access.

## 8. Project structure additions
- Backend: `semantic/metrics/cap.py`, `api/routes/solutions_capacity.py`,
  `schemas/solutions_capacity.py`; RLS gate on cost-of-sale endpoint.
- Frontend: `routes/SolutionsCapacity.tsx`; `components/widgets/capacity/` (ArchitectLoad,
  RfpTurnaround, CostOfSale, QualityScores); `hooks/useCapacityData.ts`.

## 9. Task splitup
1. Generator: opportunity-team architect roles; resource roster/allocation; pursuit SLA + turnaround;
   timesheet hours to charge codes; cost rates; gate-review scores with outcomes.
2. Build `fact_resource`, `fact_pursuit`, `fact_gate_review`, cost-of-sale fact (DQ-04 matching).
3. `cap.py`: CAP-01 load bands + over-capacity list, CAP-02 turnaround/SLA, CAP-03 cost of sale,
   CAP-04 quality score by outcome.
4. API + schemas; role-gate `/api/capacity/cost-of-sale`.
5. Frontend widgets (`moment-gtm-reusable-components` + `dataviz` skills; compose shared chart
   primitives, `StatusBadge`, `DrilldownPanel`); conditional cost-of-sale panel (`state/role.ts` +
   `require_role`).
6. Tests: `test_metrics_cap.py`; `test_rls.py` for CAP-03 gating; Playwright UAT FR-CAP-01/02 (Must).

## 10. Verification
- Architect counts and over-capacity list match seeded team assignments (AC-01); OBJ-04 callout fires.
- Turnaround/SLA reconcile to bid records; cost of sale = hours×rate÷TCV.
- CAP-03 hidden for Solutions roles and absent from their exports (AC-03).
