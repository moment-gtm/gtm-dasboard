# Moment GTM Dashboard — Offerings Module: Prototype Implementation Plan

> Companion to the Shared doc for stack, architecture, project structure, global UI/governance and
> roles. · RSD §4.5, §5 (OFF-01..05).

## 1. Context & scope
Offerings measures offering-led GTM and the return on packaged assets: pipeline/wins by offering,
multi-practice attach rate, AI-led validation status, asset reuse, and the build of demos/
accelerators/solutions (OFF-05, added in v0.9.1). Supports OBJ-03 and OBJ-05 (AI governance).
Scope = FR-OFF-01..05, metrics OFF-01..05.

## 2. Functional requirements & metrics

| Requirement | Metric | Widget | Endpoint |
|---|---|---|---|
| FR-OFF-01 pipeline & wins by offering | OFF-01 | OfferingPipelineWins (Capability-led separate) | `GET /api/offerings/by-offering` |
| FR-OFF-02 attach rate & practices/deal | OFF-02 | AttachRate (+ distribution) | `GET /api/offerings/attach-rate` |
| FR-OFF-03 AI-led validation split | OFF-03 | AiValidation (callout largest unvalidated) | `GET /api/offerings/ai-validation` |
| FR-OFF-04 asset reuse | OFF-04 | AssetReuse (low-reuse/refresh-due flags) | `GET /api/offerings/asset-reuse` |
| FR-OFF-05 demos/accelerators/solutions developed | OFF-05 | AssetBuild (released vs plan, in-dev, reuse%, build time) | `GET /api/offerings/asset-build` |

Priorities: FR-OFF-01/02/03/05 **Must**; FR-OFF-04 **Should**. Thresholds (Appendix B): attach
rate 55%; assets released vs plan pace 90%; released assets used in a pursuit 70%. OFF-03 splits
open TCV into AI-led validated / AI-led not validated / not AI-led and calls out unvalidated value.

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-01 CRM | OFF-01, OFF-02, OFF-03 | Salesforce REST/Bulk/CDC (offering, practice line items, AI-led flag/validation ID) | No Salesforce MCP — direct API | `raw_crm_*` |
| SRC-13 AI validation register | OFF-03 | SharePoint List (AI Offering Validation Framework) via **Microsoft Graph** | **Microsoft 365 MCP** | `raw_validation_record` |
| SRC-12 Knowledge repository | OFF-04 | SharePoint/M365 via **Microsoft Graph** | **Microsoft 365 MCP** | `raw_kb_asset` |
| SRC-17 Asset development tracker | OFF-05 | **Adobe Workfront** / Jira / Azure DevOps | **Adobe Workfront MCP** | `raw_asset_build` |
| SRC-03 Bid mgmt | OFF-04 | Vendor API / SharePoint (proposal asset usage) | Microsoft 365 MCP (if SharePoint) | `raw_bid_proposal_asset` |
| SRC-02 Planning | OFF-05 | Build plan (targets) API / governed file | Microsoft 365 MCP (SharePoint file) | `dim_build_plan` |

MCP-rich module: **Microsoft 365 MCP** for SRC-12/13 and **Adobe Workfront MCP** for SRC-17 are
directly usable. Offering catalogue is governed reference data (FR-ADM-03) in SharePoint.

## 4. Data-store & extract schema (module-specific)
- **Raw:** `raw_validation_record` (nightly, SRC-13: validation ID, offering, status
  Submitted/Approved/Rejected, score, review date), `raw_kb_asset` (weekly, SRC-12: asset, type,
  owner, last refresh), `raw_asset_build` (nightly, SRC-17: type, owning practice, platform,
  status, start/target/actual release dates, effort — **carries KB Asset ID once released**),
  `raw_bid_proposal_asset` (nightly, SRC-03: asset used per proposal).
- **Conformed:** `fact_validation` (one/validation), `fact_asset` + `fact_asset_usage`
  (asset; asset × pursuit), `fact_asset_build` (build item), `dim_build_plan` (quarter × type ×
  practice). Join development→publication→pursuit use via Asset ID.
- Reused: `fact_opportunity`, `bridge_opportunity_practice`, `dim_offering`, `dim_practice`,
  `dim_platform`, `dim_vertical`. Cross-industry assets appear under every vertical (OFF-05 filter).

## 5. Roles / personas with access (RSD §9)

| Role | Offerings access | Scope |
|---|---|---|
| GTM Lead, Moment leadership, Finance | Yes | All |
| Practice lead | Yes | Own practice full; others aggregated |
| Solutions lead & architects | Yes | All pursuits |
| Alliance manager | Yes | Partner-tagged opps |
| Client partner, Marketing | **No** | — |

No restricted metrics. RLS applies.

## 6. UI requirements (module-specific)
- Capability-led shown as a distinct bucket; untagged opps shown separately and counted against
  offering-led share (ties to EXE-05).
- OFF-03 calls out the value/count of unvalidated AI-led deals and lists the largest (label-led).
- OFF-04 flags low reuse (<8 uses) and refresh-due (>180 days) with text badges.
- OFF-05 filterable by practice/platform/vertical; shows released-vs-plan status, in-development by
  target quarter, reuse share, and mean build time (weeks). Metric-info popover cites SRC-17/12/03/02.

## 7. Governance notes
Owners: OFF-01/04/05 Offering portfolio lead; OFF-02 Offering portfolio lead; OFF-03 Offering
governance. Offering catalogue, asset types and the annual build plan are reference data
(FR-ADM-03); OQ-11 (tool + build-plan owner) must be resolved for real OFF-05 data.

## 8. Project structure additions
- Backend: `semantic/metrics/off.py`, `api/routes/offerings.py`, `schemas/offerings.py`; ELT joins
  for Asset ID lineage.
- Frontend: `routes/Offerings.tsx`; `components/widgets/offerings/` (OfferingPipelineWins,
  AttachRate, AiValidation, AssetReuse, AssetBuild); `hooks/useOfferingsData.ts`.

## 9. Task splitup
1. Generator: offering tags (+ Capability-led/untagged), practice line items, AI-led flag +
   validation records, KB assets, build items (Workfront-style) with plan, proposal asset usage.
2. Build `fact_validation`, `fact_asset(_usage)`, `fact_asset_build`, `dim_build_plan`; Asset-ID lineage.
3. `off.py`: OFF-01..05 incl. released-vs-plan pace and build-time math.
4. API + schemas; filters for practice/platform/vertical on OFF-05.
5. Frontend widgets (`moment-gtm-reusable-components` + `dataviz` skills; compose shared
   `GoalBarChart`, `StackedSplitChart`, `ProgressToTarget`, `StatusBadge`); unvalidated AI-led
   callout + reuse/refresh flags.
6. Tests: `test_metrics_off.py` (attach rate, validation split, released-vs-plan, build time);
   Playwright UAT FR-OFF-01/02/03/05 (Must).

## 10. Verification
- OFF-03 split sums to total open TCV; unvalidated AI-led callout matches seeded records (AC-01).
- OFF-05 released counts exclude build items missing Asset ID/type (DQ-09) and reconcile to plan.
- Microsoft 365 / Workfront MCP paths documented in `definitions.py` provenance.
- Role tests: Client partner/Marketing cannot access Offerings (AC-03).
