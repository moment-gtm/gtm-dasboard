# Moment GTM Dashboard — Partners Module: Prototype Implementation Plan

> Companion to the Shared doc for stack, architecture, project structure, global UI/governance and
> roles. · RSD §4.7, §5 (PAR-01..03).

## 1. Context & scope
Partners gives alliance managers the view of partner-sourced/influenced pipeline, co-sell
performance, and certification progress against target tier/specialization. Adobe and Salesforce
at launch, extensible. Scope = FR-PAR-01..03, metrics PAR-01..03.

## 2. Functional requirements & metrics

| Requirement | Metric | Widget | Endpoint |
|---|---|---|---|
| FR-PAR-01 pipeline by partner (sourced/influenced) | PAR-01 | PartnerPipeline | `GET /api/partners/pipeline` |
| FR-PAR-02 co-sell performance | PAR-02 | CoSell (win rate w/ vs w/o partner) | `GET /api/partners/co-sell` |
| FR-PAR-03 certification status | PAR-03 | Certifications (progress vs required) | `GET /api/partners/certifications` |

Priorities: FR-PAR-01/02 **Must**; FR-PAR-03 **Should**. Sourced = partner originated (registered
deal); Influenced = materially contributed. Certification threshold (Appendix B): on track ≥90% of
target tier/specialization requirement; Watch 60–90%.

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-01 CRM | PAR-01, PAR-02 | Salesforce REST/Bulk/CDC (partner & partner-role fields) | No Salesforce MCP — direct API | `raw_crm_*` |
| SRC-08 Partner portals | PAR-01, PAR-03 | **Adobe Solution Partner Portal** API; **Salesforce Partner Community** API; monthly export fallback | **No partner-portal MCP** — direct API / export | `raw_partner_*` |
| SRC-09 LMS | PAR-03 | Enterprise LMS extract (internal certifications) | No MCP — direct extract | `raw_lms_learning_record` |

MCP note: there is **no MCP** for the partner portals or LMS in this environment — integrate via
the vendors' APIs (or a monthly governed export where the API is limited, a known risk/mitigation).

## 4. Data-store & extract schema (module-specific)
- **Raw:** `raw_partner_deal_registration` (monthly, SRC-08: registrations, co-sell records),
  `raw_partner_certification` + `raw_partner_tier` (monthly, SRC-08), `raw_lms_learning_record`
  (weekly, SRC-09: internal certification completions).
- **Conformed:** `fact_partner_engagement` (opportunity × partner; role Sourced/Influenced/None),
  `fact_certification` (partner × certification × month; certified count vs required for tier).
- Reused: `fact_opportunity`, `dim_partner` (Adobe, Salesforce; extensible), `dim_person`.

## 5. Roles / personas with access (RSD §9)

| Role | Partners access | Scope |
|---|---|---|
| GTM Lead, Moment leadership, Finance | Yes | All |
| Alliance manager | Yes (default view) | Partner-tagged opps; certification data |
| Client partner | Yes | Assigned accounts |
| Practice lead | Yes (all modules) | Own practice full; others aggregated |
| Solutions, Marketing | **No** | — |

No restricted metrics. RLS applies.

## 6. UI requirements (module-specific)
- Pipeline-by-partner split Sourced vs Influenced (stacked, labelled).
- Co-sell: wins/value, share of bookings with partner involvement, and win rate with vs without a
  partner side-by-side.
- Certifications: progress bars vs required count with status badges (text + colour).
- Metric-info popover cites SRC-08/SRC-09; freshness banner flags monthly-export staleness.

## 7. Governance notes
Owner: Alliance managers (PAR-01..03). Partner list and certification targets are reference data
(FR-ADM-03). Risk: limited partner-portal APIs → monthly governed export fallback (RSD §13.3).

## 8. Project structure additions
- Backend: `semantic/metrics/par.py`, `api/routes/partners.py`, `schemas/partners.py`.
- Frontend: `routes/Partners.tsx`; `components/widgets/partners/` (PartnerPipeline, CoSell,
  Certifications); `hooks/usePartnersData.ts`.

## 9. Task splitup
1. Generator: partner tags/roles on opportunities; deal registrations; certification counts vs
   required; LMS completions.
2. Build `fact_partner_engagement`, `fact_certification`; `dim_partner`.
3. `par.py`: PAR-01 sourced/influenced pipeline, PAR-02 co-sell (win rate w/ vs w/o partner),
   PAR-03 certification progress.
4. API + schemas.
5. Frontend widgets (`moment-gtm-reusable-components` + `dataviz` skills; compose shared chart
   primitives, `StatusBadge`, `DrilldownPanel`).
6. Tests: `test_metrics_par.py`; Playwright UAT FR-PAR-01/02 (Must); role test (Solutions/Marketing
   excluded, AC-03).

## 10. Verification
- Sourced/influenced split and co-sell win-rate comparison reconcile to CRM/partner facts (AC-01).
- Certification progress matches seeded counts vs targets.
- Freshness indicator reflects the monthly cadence of SRC-08 (FR-GEN-09/NFR-02).
