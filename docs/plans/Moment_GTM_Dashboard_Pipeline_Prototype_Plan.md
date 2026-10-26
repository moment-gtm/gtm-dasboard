# Moment GTM Dashboard — Pipeline Module: Prototype Implementation Plan

> Companion to `docs/architecture/Moment_GTM_Dashboard_Shared_Architecture_Schema_Governance.md` (the "Shared doc"),
> which defines the tech stack, layered architecture, project structure, global UI/governance and
> roles matrix. This plan adds only the Pipeline-specific detail. · RSD §4.3, §5 (PIP-01..07).

## 1. Context & scope
The Pipeline module gives practice leads and Sales Ops the operational view of open pipeline:
stage funnel and conversion, ageing, mix by practice/platform, deal-size distribution, the
opportunity register, and week-over-week stage movement. It is central to the weekly pipeline
review (OBJ-01/AC-06). Scope = FR-PIP-01..06, metrics PIP-01..07.

## 2. Functional requirements & metrics

| Requirement | Metric(s) | Widget | Endpoint |
|---|---|---|---|
| FR-PIP-01 stage funnel + conversion | PIP-01 | StageFunnel (click stage → filter register) | `GET /api/pipeline/funnel` |
| FR-PIP-02 ageing heatmap | PIP-02 | AgeingHeatmap (stage × days-in-stage bucket) | `GET /api/pipeline/ageing` |
| FR-PIP-03 mix by practice & platform | PIP-03, PIP-04 | PipelineByPractice, PipelineByPlatform | `GET /api/pipeline/by-practice`, `.../by-platform` |
| FR-PIP-04 deal-size distribution | PIP-05 | DealSizeHistogram | `GET /api/pipeline/size-distribution` |
| FR-PIP-05 opportunity register | PIP-06 | OpportunityRegister (sort/search/export, ageing highlighted) | `GET /api/opportunities?...` |
| FR-PIP-06 week-over-week stage movement | PIP-07 | StageMovement (advanced/regressed/slipped/created/closed) | `GET /api/pipeline/stage-movement` |

Priorities: FR-PIP-01/02/03/05 **Must**; FR-PIP-04 **Should**; FR-PIP-06 **Should** (needs weekly
snapshots — FR-GEN-11). Conversion = reached stage s+1 ÷ reached s over trailing 4 quarters.
Ageing buckets 0–30 / 31–60 / 61–90 / >90 (configurable); >90 = Stalled (§Appendix B / EXE-10).

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-01 CRM | PIP-01..06 | Salesforce REST + Bulk 2.0 + Pub/Sub CDC (`Opportunity`, `OpportunityHistory`, `OpportunityLineItem`) | **No Salesforce MCP** — direct API | generator → `raw_crm_*` |
| Weekly snapshot | PIP-01, PIP-02, PIP-07 | Derived in the data platform (FR-GEN-11) | n/a | `fact_opportunity_snapshot` |

No MCP server applies to the Pipeline module's primary source. CRM is integrated via the external
Salesforce API (OAuth JWT; nightly delta, hourly optional per NFR-02). See Shared doc §1/§4.

## 4. Data-store & extract schema (module-specific)
- **Raw (daily, SRC-01):** `raw_crm_opportunity`, `raw_crm_opportunity_history`
  (stage changes w/ timestamps → days-in-stage, conversions), `raw_crm_opportunity_line_item`
  (practice participation → PIP-03).
- **Conformed:** `fact_opportunity` (grain: one row/opportunity; TCV, stage, stage-entry date,
  close date, created date, practice, platform, owner, account→vertical), `fact_stage_history`
  (grain: opportunity × stage change), `bridge_opportunity_practice`.
- **Snapshot (weekly):** `fact_opportunity_snapshot` (grain: opportunity × week; stage, amount,
  close date, probability) — taken Monday 00:00 IST, retained 3 years (§7.3); powers PIP-07 and
  trend/ageing.
- Dimensions reused: `dim_practice`, `dim_platform`, `dim_vertical`, `ref_stage_probability`,
  `ref_bucket` (ageing), `ref_size_band`.

## 5. Roles / personas with access (RSD §9)

| Role | Pipeline access | Data scope |
|---|---|---|
| GTM Lead, Moment leadership, Finance | Yes | All |
| Practice lead | Yes (default view, own practice) | Own practice full; others aggregated |
| Client partner | Yes | Assigned accounts |
| Solutions lead & architects | Yes | All pursuits |
| Alliance manager, Marketing | **No** | — |

No restricted metrics in this module. RLS by practice/account applies.

## 6. UI requirements (module-specific; global rules in Shared doc §6)
- Clicking a stage in the funnel filters the register; clicking again clears it (FR-PIP-01).
- Ageing heatmap: count + TCV per cell; buckets past the review threshold visually distinguished
  (and labelled, not colour-only). Buckets configurable via Admin.
- Register: every column sortable, searchable, exportable (CSV/Excel), ageing rows highlighted
  with a text badge.
- Each panel exposes metric ID/definition/source/refresh (FR-GEN-07); empty/error states (FR-GEN-13).

## 7. Governance notes
Metric owners: PIP-01/02/04/05/07 Sales Operations; PIP-03 Practice leads. Ageing buckets, size
bands and stage-probability table are admin-maintained (FR-ADM-02) and version-controlled.

## 8. Project structure additions
- Backend: `semantic/metrics/pip.py` (PIP-01..07), `api/routes/pipeline.py`, `schemas/pipeline.py`,
  snapshot build step in `platform/elt/conformed_to_marts.py`.
- Frontend: `routes/Pipeline.tsx`; `components/widgets/pipeline/` (StageFunnel, AgeingHeatmap,
  PipelineByPractice, PipelineByPlatform, DealSizeHistogram, OpportunityRegister, StageMovement);
  `hooks/usePipelineData.ts`; `api/pipeline.ts`.

## 9. Task splitup
1. Extend generator to emit stage history and weekly snapshots with realistic ageing distribution.
2. Build `fact_stage_history`, `fact_opportunity_snapshot` and ageing/size reference data.
3. `pip.py`: implement PIP-01 (funnel + trailing-4Q conversion), PIP-02 (ageing), PIP-03/04 (mix),
   PIP-05 (size bands), PIP-06 (register query), PIP-07 (week-over-week from snapshots).
4. API routes + pydantic schemas incl. per-cell count/TCV and conversion rates.
5. Frontend widgets (invoke `moment-gtm-reusable-components` + `dataviz` skills): compose shared
   `FunnelChart` (click-to-filter), `Heatmap`, `StackedSplitChart`, `DistributionHistogram`,
   `DataRegister` (register) and stage-movement; no module-local copies.
6. Wire global filters + drill-down + metric-info + export; empty/error states.
7. Tests: `test_metrics_pip.py` (conversion math, ageing buckets, snapshot movement) + Playwright
   UAT for FR-PIP-01/02/03/05 (Must).

## 10. Verification
- PIP-01 conversion and PIP-02 ageing counts reconcile to direct `fact_stage_history` queries
  within 0.5% on the fixed seed (AC-01).
- Stage click filters/clears the register; register sort/search/export work; ageing rows carry a
  text badge (not colour alone, NFR-08).
- PIP-07 reflects seeded week-over-week changes from two snapshots.
- Role tests: Alliance/Marketing cannot reach Pipeline; practice lead sees own practice in detail
  and others aggregated (AC-03).
