# Moment GTM Dashboard — Executive Summary Prototype: Implementation Plan

> **Derived from:** `docs/requirements/Moment_GTM_Dashboard_RSD_v0.9_Summary.md` (RSD v0.9.1)
> **Prototype scope:** Executive summary module only · **Date:** 2026-10-14
> **Companion:** `docs/architecture/Moment_GTM_Dashboard_Shared_Architecture_Schema_Governance.md` — the shared doc
> defines the common tech stack (justified vs NFR-01..13 & AC-01..07), the layered architecture, the
> monorepo structure, the full data-store/extract schema, global UI/governance and the roles matrix.
> Section 12 below (Addendum) aligns this Executive plan with that shared foundation.

---

## 1. Context

The RSD specifies a read-only, role-based GTM BI dashboard. This plan covers a **high-fidelity
prototype of the Executive summary module only** — FR-EXE-01..05 and metrics EXE-01..EXE-10, plus
the Executive-relevant global features (filters, drill-down, metric info, status, freshness).

This is a **greenfield** build (the folder contains only the RSD `.docx` and its summary; the
companion mockup HTML referenced by the RSD is not present, so the UI is built from the RSD).

**Confirmed decisions**
- **Frontend:** custom web app — React + TypeScript + Vite.
- **Data:** a mock **backend acting as the semantic layer**, computing all metrics from a synthetic
  dataset and exposing them over REST (demonstrates the RSD's layered architecture).
- **Backend:** Python + FastAPI, synthetic data via Faker.

**Intended outcome:** a runnable two-service app (FastAPI + React) reproducing the Executive
summary — bookings runway, six north-star KPIs, bookings by quarter, open pipeline by vertical, and
deals needing attention — computed live from synthetic deals, responsive to global filters, with
drill-down to underlying opportunities. It becomes the reference implementation for extending to the
other seven modules.

---

## 2. Recommended tech stack

**Frontend**
- **React 18 + TypeScript + Vite** — fast dev, portable SPA.
- **Recharts** — declarative charts (runway, quarterly bars, vertical split, sparklines). Chart
  design/colors follow the `dataviz` skill (consulted before writing chart code).
- **TanStack Query** — server-state fetching/caching for metric endpoints.
- **Zustand** — global filter state, persisted for the session (FR-GEN-02).
- **React Router** — routing (Executive route now; structured to add modules).
- **Tailwind CSS + Radix UI primitives** — styling + accessible popover/dialog (metric-info
  popover, drill-down panel) to meet WCAG 2.1 AA with minimal custom a11y code.

**Backend**
- **Python 3.11+ + FastAPI + Uvicorn**, **Pydantic v2** for API contracts.
- **Faker** (seeded) for synthetic opportunities, accounts, targets.
- **pandas** (optional) for aggregations; plain Python is fine at prototype scale.
- **pytest** for metric/API unit tests.

**Tooling:** ruff + black (Python), ESLint + Prettier (TS), `docker-compose` to run both services,
`.env` for the frontend API base URL.

---

## 3. Standard architecture (layered, mirrors the RSD)

Metric logic is defined **once** in a semantic layer:

```
Synthetic data (data/)  →  Semantic layer (semantic/)  →  API (api/)  →  React presentation
   "raw/conformed"          authoritative metric defs      REST           widgets per FR-EXE-*
```

Clean separation: `domain` (entities) ← `data` (generation/store) ← `semantic` (business/metric
logic) ← `api` (interface) ← `schemas` (contracts). Frontend is feature/layered: `routes` →
`components` (layout / widgets / common) → `hooks` → `api` → `state`/`theme`/`utils`.

---

## 4. Project structure

```
dashboard/
  README.md                      # run instructions (both services)
  docker-compose.yml             # optional one-command run
  .gitignore
  docs/
    architecture.md              # layer diagram + data flow
    metric-mapping.md            # metric ID → backend fn → widget (traceability)
  backend/
    pyproject.toml / requirements.txt
    app/
      main.py                    # FastAPI app, CORS, routers
      config.py                  # seed, plan FX, fiscal calendar, demo "today"
      domain/
        models.py                # Opportunity, StageHistory, Account, Target
        enums.py                 # Stage, Vertical, Practice, Platform, LeadSource
      data/
        generator.py             # seeded synthetic deal generator (Faker)
        reference_data.py        # stage probabilities, thresholds, catalogue, targets
        store.py                 # in-memory dataset singleton (+ weekly snapshot stub)
      semantic/                  # THE semantic layer (authoritative)
        filters.py               # apply period/vertical/practice/platform filters
        status.py                # On track/Watch/Off track banding (FR-GEN-05)
        definitions.py           # metric registry: id → {name, definition, sources, owner}
        helpers.py               # weighted pipeline, plan pace, coverage, cycle
        metrics/exe.py           # EXE-01 … EXE-10
      api/routes/
        executive.py             # /api/executive/* (runway, kpis, by-quarter, by-vertical, attention)
        opportunities.py         # /api/opportunities (filtered drill-down list)
        reference.py             # /api/reference (filter options, thresholds, metric meta)
        health.py                # /api/health + data freshness
      schemas/                   # pydantic response models
    tests/
      test_metrics.py            # per-metric unit tests (EXE-01..10)
      test_filters.py
      test_api.py
  frontend/
    index.html, vite.config.ts, tsconfig.json, package.json, .env
    src/
      main.tsx, App.tsx
      routes/ExecutiveSummary.tsx
      components/
        layout/   NavRail.tsx · FilterBar.tsx · DataFreshnessIndicator.tsx
        widgets/  BookingsRunway.tsx · KpiStrip.tsx · KpiCard.tsx · Sparkline.tsx ·
                  BookingsByQuarter.tsx · PipelineByVertical.tsx · DealsNeedingAttention.tsx
        common/   StatusBadge.tsx · MetricInfoPopover.tsx · DrilldownPanel.tsx ·
                  EmptyState.tsx · ErrorState.tsx · Money.tsx
      api/        client.ts · executive.ts · types.ts
      state/      filters.ts (Zustand)
      hooks/      useExecutiveData.ts (TanStack Query)
      theme/      tokens.ts · global.css
      utils/      format.ts ($M to 1 dp, %, dates)
```

---

## 5. Metric → requirement → widget mapping (prototype core)

| Widget (FR) | Metrics | Backend endpoint |
|---|---|---|
| Bookings runway (FR-EXE-01) | EXE-07 (+ EXE-01 pace) | `GET /api/executive/runway` |
| North-star KPI strip (FR-EXE-02) | EXE-01..EXE-06 + 4-qtr sparklines | `GET /api/executive/kpis` |
| Bookings by quarter (FR-EXE-03) | EXE-08 | `GET /api/executive/bookings-by-quarter` |
| Pipeline by vertical (FR-EXE-04) | EXE-09 | `GET /api/executive/pipeline-by-vertical` |
| Deals needing attention (FR-EXE-05) | EXE-10 | `GET /api/executive/deals-attention` |
| Global filters (FR-GEN-02/03) | all | query params on every endpoint; options from `/api/reference` |
| Filtered target comparison & pro-rating (FR-GEN-04) | EXE-01, EXE-02, EXE-07, EXE-08 | `semantic/targets.py` (slice/pro-rate/label); see Shared doc §6.1 |
| Drill-down (FR-GEN-06) | all | `GET /api/opportunities?...` |
| Metric info (FR-GEN-07) | all | `/api/reference/metrics` |
| Status labels (FR-GEN-05) | goal-based | computed in `semantic/status.py` |
| Freshness (FR-GEN-09) | all | `/api/health` |

Metric definitions per RSD §5 / Appendix B: bookings vs plan pace, coverage (3.0x goal), win rate
(40%), new pipeline created, offering-led share (60%), avg deal cycle (≤120d), runway
(commit/best-case via stage probabilities), bookings by quarter vs target, open pipeline by vertical
(qualified vs Identify), deals needing attention (≥$2M, 61–90 Ageing, >90 Stalled). Status bands
come from Appendix B.

### 5.1 EXE-10 "Deals needing attention" — leadership view (built)

**Rule (defaults, admin-configurable):** open deal AND TCV ≥ $2M AND (days in stage > 60 OR close date
already past). Flag precedence: **Stalled** (>90 days) › **Ageing** (61–90) › **Past close date**.
Data flow: SRC-01 CRM → `raw_crm_opportunity` (+ history) → `fact_opportunity` (`days_in_stage`,
`past_dated` DQ-02) → `mart_opportunity` → `exe.exe_10` → `GET /api/executive/deals-attention` →
`DealsNeedingAttention` widget. Rows follow detail-scope RLS; deals outside the caller's practice are
counted in the totals and shown only as the "aggregated other" note.

Widget layout, top to bottom (each visual answers one leadership question):

| # | Visual | Reuses | Question answered | Click-through (EXE-10 drill segment) |
|---|---|---|---|---|
| 1 | 3 headline tiles: deals flagged · TCV at risk · Stalled count | `Money`, card tokens | How big is the problem? | — |
| 2 | Flag-mix stacked bar (TCV by Ageing / Stalled / Past close date) | `StackedSplitChart` | Why are deals flagged? | `<flag>` |
| 3 | Vertical × reason heatmap (count + TCV per cell, shade = count) | **`Heatmap`** (new shared primitive) | Where does it concentrate? | `<vertical>\|<flag>` |
| 4 | Largest 5 deals: days-in-stage bar with 60 / 90-day threshold lines + flag badge | `FlagBadge` | Which deals do I call about first? | `<flag>` |
| 5 | Collapsible full register ("Show all N deals") | `DataRegister` | Full detail + CRM deep link | — |

```
┌ Deals needing attention ───────────────────────────────────────────┐
│ [ 14 deals ] [ $48.2M at risk ] [ 5 Stalled ]                      │
│ Why flagged  ▓▓▓▓▓▓░░░░▒▒▒▒▒░░  Ageing | Stalled | Past close      │
│ Where        vertical × reason heat grid (e.g. BFSI × Stalled 3·$9M)│
│ Biggest      Acme · $6.1M ████████████|███ Stalled  (60 | 90 lines) │
│ ▸ Show all 14 deals                                                │
└────────────────────────────────────────────────────────────────────┘
```

Accessibility: every cell/bar prints its number (colour is never the only signal), flags carry icon +
text, all visuals are keyboard-operable buttons, and the data stays available via the register.
Backend addition: `meta.by_vertical` (full aggregate scope) on EXE-10 and flag / vertical|flag drill
segments in `drill_condition`; covered by `tests/test_metrics.py` and `e2e/playwright/executive.spec.ts`.

---

## 6. Source-of-record integrations (real APIs & MCP servers)

The prototype runs on **synthetic data**, but each synthetic feed stands in for a real source. For
a production/real-data Executive summary, these are the systems to invoke. Only sources feeding
EXE-01..EXE-10 are listed (per RSD §5 and §6.3).

**Executive-summary source systems and their metrics**

| RSD source | Feeds | Real integration | Prototype stand-in |
|---|---|---|---|
| **SRC-01 CRM** (system of record for pipeline) | EXE-01..EXE-10 (all) | Salesforce Sales Cloud API | `data/generator.py` opportunities |
| **SRC-02 Planning** (targets) | EXE-01, EXE-02, EXE-04, EXE-07, EXE-08 | Anaplan / SAP BPC API, or governed Excel on SharePoint | `data/reference_data.py` targets |
| **SRC-04 Finance ERP** (reconciliation, secondary) | EXE-01, EXE-08 (month-end) | SAP S/4HANA OData / finance DW extract | not modeled in prototype |
| **Offering catalogue** (reference, FR-ADM-03) | EXE-05 | SharePoint List via Microsoft Graph | `data/reference_data.py` catalogue |
| **SRC-16 Entra ID** (access/RLS) | all (auth, RLS) | Microsoft Graph / SCIM | mock role switcher (optional) |

**External REST APIs (no MCP server available — call directly in production)**
- **Salesforce Sales Cloud (SRC-01)** — primary. OAuth 2.0 (JWT bearer / connected app).
  - REST + **Bulk API 2.0** for batch loads; **Pub/Sub (CDC/Streaming) API** for incremental deltas.
  - Base: `https://<instance>.my.salesforce.com/services/data/v60.0/`.
  - Objects: `Opportunity`, `OpportunityHistory`/`OpportunityFieldHistory` (stage history →
    EXE-10 days-in-stage), `OpportunityLineItem` (practice line items → EXE-05),
    `OpportunityTeamMember`, `Account` (industry → vertical, EXE-09), `Campaign`,
    `CampaignInfluence`, `User`. Nightly delta; hourly optional (NFR-02: refreshed by 07:00 IST).
- **Planning system (SRC-02)** — bookings targets by quarter/practice/vertical(/account).
  - **Anaplan API** (`https://api.anaplan.com/2/0/…`, token auth) **or SAP BPC**; interim =
    governed Excel template on SharePoint (read via Microsoft Graph). On change / ≥quarterly.
- **Finance ERP (SRC-04)** — month-end bookings reconciliation. SAP S/4HANA OData / Oracle /
  finance data warehouse extract. Monthly after period close (secondary source for Exec).
- **Microsoft Entra ID (SRC-16)** — SSO + RLS group memberships. Microsoft Graph
  (`https://graph.microsoft.com/v1.0/users|groups|…`) / SCIM, OAuth client-credentials (NFR-04 SSO).

**MCP servers available in this environment that map to RSD sources**
- **Microsoft 365 MCP** — directly relevant for the Executive summary: Entra ID identity (SRC-16)
  for SSO/RLS, SharePoint for the **interim governed targets template (SRC-02)** and the
  **offering-catalogue / reference Lists**. Use this MCP for those feeds where available.
- Available but mapped to **non-Executive** modules (note for later phases, out of Exec scope):
  **Adobe Workfront** → SRC-17 asset development tracker (Offerings); **Adobe Journey Optimizer /
  Adobe Marketing Agent** → SRC-10 marketing automation (Market signals); **Adobe Experience
  Manager + Adobe Customer Journey Analytics** → SRC-11 web CMS/analytics (Market signals).
- Not relevant to this dashboard: FactSet, Gmail, Google Calendar, Google Drive, account-twin.
- **Gap:** there is **no Salesforce MCP** here, so the CRM (SRC-01) — the dominant Executive-summary
  source — must be integrated via the external Salesforce API above, not an MCP server.

For the prototype, the backend's `semantic/definitions.py` records each metric's source IDs so the
metric-info popover (FR-GEN-07) shows true provenance even while data is synthetic.

---

## 7. Roles / personas with access to the Executive summary

Derived from RSD §3 (personas) and §9 (roles & access). The Executive summary is accessible to the
roles whose module list includes it; **Solutions leads & architects are excluded** (their modules
are Pipeline, Pursuits, Offerings, Solutions capacity — not Executive summary).

| Role / persona | Exec access | Data scope (RLS) | Restricted metrics (PUR-06, CAP-03) |
|---|---|---|---|
| GTM Lead (business owner) | Yes (+ admin) | All data | Yes |
| Moment leadership | Yes (read-only) | All data | Yes |
| Finance business partner | Yes | All data (incl. margin) | Yes |
| Practice lead | Yes | Own practice in full; others aggregated | No |
| Client partner / account lead | Yes | Assigned accounts only | No |
| Alliance manager | Yes | Partner-tagged opportunities | No |
| Marketing | Yes | Campaign-/workshop-linked opportunities | No |
| Sales Operations (administrator) | Yes (+ admin, DQ console) | All data | No (unless granted) |
| Solutions lead & architects | **No** | n/a for this module | n/a |

Notes: the Executive summary displays **no restricted metrics** (PUR-06/CAP-03 live in other
modules), so restricted-metric gating is not exercised here; **RLS by practice/account still
applies** (practice leads see own-practice detail + others aggregated; client partners see assigned
accounts). Enforced in production via Entra ID groups (SRC-16) in the semantic layer (NFR-05). In
the prototype, model this with an **optional mock role switcher** (Open Question 6).

---

## 8. Task splitup

> **Alignment with the roadmap and skill:** shell items (E.14–16), semantic foundation items (C.7–8,
> plus `semantic/targets.py`) and the common primitives under G (22–25) are built **once** in
> Step 0 of `docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md` via the `moment-gtm-reusable-components`
> skill. In Step 1 the Executive module **composes** them: `metrics/exe.py` follows the
> metric-module contract and widgets follow the skill's widget composition pattern (`KpiCard`/
> `KpiStrip`, `RunwayChart`, `GoalBarChart`, `StackedSplitChart`, `DataRegister`).

**A. Scaffolding & tooling**
1. Create repo structure, `README`, `.gitignore`, `docker-compose.yml`.
2. Backend: FastAPI app skeleton, config (seed/FX/fiscal/demo-today), CORS, health route.
3. Frontend: Vite + React + TS, Tailwind, Router, TanStack Query provider, `.env` API base URL.

**B. Backend — domain & synthetic data**
4. `domain/models.py` + `enums.py`: Opportunity (TCV, stage, stage-entry dates, close/created
   dates, vertical, practice, platform, offering/Capability-led, lead source, AI-led flag, owner),
   Account, Target, StageHistory.
5. `data/reference_data.py`: stage probability table, Appendix B thresholds, offering catalogue,
   verticals/practices/platforms, quarterly targets by practice/vertical.
6. `data/generator.py` + `store.py`: seeded generation of accounts and deals across FY with a
   realistic stage/close/age distribution; in-memory singleton + simple weekly-snapshot stub.

**C. Backend — semantic layer (metrics)**
7. `semantic/filters.py`: apply period (FYTD / quarter / current QTD / custom), vertical, practice,
   platform; keep filter grain consistent across metrics.
8. `semantic/helpers.py` + `status.py`: weighted pipeline, plan pace, coverage, deal cycle, and
   On track/Watch/Off track banding.
9. `semantic/metrics/exe.py`: implement EXE-01..EXE-10 exactly per §5; `definitions.py` registry
   carrying id/name/definition/sources/owner for FR-GEN-07.
10. `tests/test_metrics.py`: assert each metric against hand-computed values on a fixed seed.

**D. Backend — API**
11. `api/routes/executive.py`: the five metric endpoints returning pydantic schemas incl. status +
    narrative (runway one-sentence narrative per FR-EXE-01).
12. `api/routes/opportunities.py`: filtered, sortable drill-down list (deal, account, stage, TCV,
    close, days-in-stage, offering, owner).
13. `api/routes/reference.py` + `health.py`: filter options, thresholds, metric metadata, freshness
    timestamps; `tests/test_api.py` smoke tests.

**E. Frontend — shell**
14. `theme/tokens.ts` + `global.css`: accessible palette (placeholder for Moment brand), typography.
15. `layout/NavRail.tsx`, `FilterBar.tsx` (bound to Zustand, persisted), `DataFreshnessIndicator.tsx`.
16. `api/client.ts` + `types.ts` + `hooks/useExecutiveData.ts`: typed fetch + Query hooks; filters
    feed into query keys so widgets refetch on change.

**F. Frontend — Executive widgets** (invoke `dataviz` skill first)
17. `BookingsRunway` (FR-EXE-01/EXE-07): booked/commit/best-case/target/pace markers + narrative.
18. `KpiStrip` + `KpiCard` + `Sparkline` (FR-EXE-02/EXE-01..06): value, goal, status, 4-qtr trend.
19. `BookingsByQuarter` (FR-EXE-03/EXE-08): bars vs target, current quarter marked QTD.
20. `PipelineByVertical` (FR-EXE-04/EXE-09): qualified vs Identify split.
21. `DealsNeedingAttention` (FR-EXE-05/EXE-10): leadership-first layout (see §5.1) — headline tiles,
    flag-mix bar, vertical × reason heatmap, largest-deals days-in-stage bars, collapsible register.

**G. Cross-cutting (FR-GEN + NFR)**
22. `StatusBadge`: text label + icon + colour (never colour alone — NFR-08/FR-GEN-05).
23. `MetricInfoPopover` (FR-GEN-07): metric ID, definition, sources, last refresh per widget.
24. `DrilldownPanel` (FR-GEN-06): opportunity list opened from any aggregate; keyboard accessible,
    Escape to close (NFR-08).
25. `EmptyState`/`ErrorState` (FR-GEN-13); `Money` ($M to 1 dp) + responsive to 390px (FR-GEN-12/NFR-09).

**H. Finishing**
26. `docs/architecture.md` + `docs/metric-mapping.md` (traceability table).
27. End-to-end run via docker-compose; README with local run steps.

---

## 9. Open questions to proceed (prototype-specific)

Sensible defaults noted so implementation is not blocked:
1. **Brand assets** — Moment palette/logo/fonts available, or use an accessible placeholder?
   *(Default: placeholder palette, swapped later.)*
2. **Synthetic data volume** — how many accounts/opportunities for a convincing demo?
   *(Default: ~40 accounts, ~400 open + closed deals across FY.)*
3. **Demo "today" / fiscal reference** — fix a demo current date so plan pace/QTD are stable?
   *(Default: freeze "today" mid-current-quarter of FY26.)*
4. **Vertical names** — RSD mentions five Moment verticals but doesn't name them; which five?
   *(Default: placeholders e.g. BFSI, Retail/CPG, Health/Life Sciences, Comms/Media/Tech,
   Manufacturing — confirm.)*
5. **Primary measure** — TCV vs ACV (RSD OQ-05)? *(Default: TCV, per RSD.)*
6. **Auth/roles** — include a mock role switcher to demo RLS scoping, or skip?
   *(Default: optional mock role switcher; no real SSO in prototype.)*
7. **Deployment** — local-only, or container/cloud demo-ready?
   *(Default: local via docker-compose; cloud deferred.)*
8. **Tests depth** — backend metric/API tests only, or also frontend component tests?
   *(Default: backend metric/API unit tests; frontend smoke only.)*

(Distinct from the RSD's own open questions OQ-01..11, which concern production, not the prototype.)

---

## 10. Verification

- **Backend:** `pytest` passes; each EXE-01..10 metric matches hand-computed expectations on the
  fixed seed; endpoints return 200 with valid schemas (`test_api.py`).
- **Run end-to-end:** `docker-compose up` (or uvicorn + `npm run dev`); open the frontend and
  confirm the Executive summary renders all five widgets from live API data.
- **Interactivity:** changing a global filter updates every widget and the narrative; clicking an
  aggregate opens the drill-down panel with matching opportunities; metric-info popover shows
  ID/definition/source/refresh.
- **Quality gates:** status shown as label + colour (not colour alone); drill-down panel keyboard
  accessible with Escape close; layout usable at 390 px; empty/error states render when a filter
  returns no rows or the API is down.

---

## 11. Notes

- Chart work follows the `dataviz` skill (read before writing chart code).
- Shared components and module widgets follow the `moment-gtm-reusable-components` skill (golden
  rules, contracts, definition of done). As the reference slice, Executive sets the pattern later
  modules copy.
- Structured so the remaining seven modules can be added as new routes + semantic metric modules
  without reworking the architecture.

---

## 12. Addendum — missing items (alignment with shared architecture, schema & acceptance criteria)

Added after the full module set was planned, to keep the Executive plan consistent with the Shared
doc. These supersede the original "in-memory only" data approach.

### 12.1 Data-store & extract schema for Executive sources
Adopt the Shared doc's **DuckDB** store (raw → conformed → marts) instead of pure in-memory data, so
the prototype demonstrates real extract cadence. Executive-relevant tables:
- **Raw (daily, SRC-01 CRM):** `raw_crm_opportunity`, `raw_crm_opportunity_history` (stage entry
  dates → EXE-10 days-in-stage), `raw_crm_opportunity_line_item` (practice → EXE-05),
  `raw_crm_account` (industry → vertical, EXE-09).
- **Raw (on change/quarterly, SRC-02 Planning):** `raw_planning_target`.
- **Raw (monthly, SRC-04 Finance — secondary):** `raw_finance_contract` (month-end reconciliation).
- **Conformed/marts:** `fact_opportunity`, `fact_stage_history`, `fact_opportunity_snapshot`
  (weekly, for EXE-02 coverage trend sparkline), `fact_target`, plus `dim_vertical`,
  `dim_practice`, `dim_platform`, `ref_stage_probability`, `ref_threshold`.
- Offering catalogue is governed reference data (`ref_offering`) feeding EXE-05.

### 12.2 Data quality & audit (previously missing)
- Apply the relevant **DQ rules** (§6.6) to Executive data: DQ-01 untagged (offering/practice/
  platform) shown as an Untagged bucket counting against EXE-05; DQ-02 past-dated open deals forced
  into EXE-10; DQ-06 non-USD converted at plan FX; DQ-07 rep probability overridden by the standard
  stage-probability table for weighted runway. Findings surface in the Admin DQ console.
- **Audit log (NFR-07):** record every export of Executive data to `audit_log` (12-month retention).

### 12.3 Testing driven by acceptance criteria (previously under-specified)
Extend §10 verification with:
- **Reconciliation harness (AC-01):** each EXE-01..10 result vs a direct raw-zone query, within 0.5%
  over 3 refresh cycles; bookings reconcile to `raw_finance_contract` at month end.
- **Playwright UAT (AC-02):** scripts for every Must requirement (FR-EXE-01..05, FR-GEN-02/05/06/07).
- **Role-matrix tests (AC-03):** verify the eight Executive-eligible roles and their RLS scope;
  confirm Solutions leads/architects cannot reach the module.
- **k6 load test (AC-04):** 50 concurrent users meet NFR-01 (<3s P90; filters <2s).
- **axe-core + manual review (AC-07):** WCAG 2.1 AA, incl. the keyboard-accessible drill-down panel.

### 12.4a Filtered target comparison & pro-rating (FR-GEN-04 — previously missing)
When a global filter is applied, bookings-vs-target (EXE-01), coverage (EXE-02) and the runway
(EXE-07/EXE-08) must compare against the **matching target slice**, not the whole-year target: use
the exact `fact_target` slice when it exists, otherwise **pro-rate the parent target by the slice's
pipeline share and label it "pro-rated"** in both the API payload and a widget badge. Implemented
once in the shared `semantic/targets.py` (Shared doc §6.1) and reused by the runway narrative and
status banding. Add a Playwright UAT case that asserts the pro-rated label appears when filtering to
a grain with no stored target.

### 12.4 NFR & governance alignment
- NFR mapping is in the Shared doc §1; Executive specifics: NFR-02 freshness banner by 07:00 IST,
  NFR-05 RLS by practice/account (no restricted metrics in this module), NFR-08/09 accessibility +
  390px responsiveness.
- **Metric owners (governance, §10.2):** EXE-01/03/04/07/08 GTM Lead (EXE-01 with Finance);
  EXE-02/06/09 Sales Operations; EXE-05 Offering portfolio lead. Thresholds come from `ref_threshold`
  (admin-editable, FR-ADM-02) so status recomputes without a code change.

### 12.5 Cross-module hooks
- **Alerts (FR-ALR-02):** the coverage-drop alert (EXE-02 below amber) and the ≥$5M close-date-slip
  alert are defined in the Administration module but driven by Executive metrics — expose the values
  the alert engine reads.
- Project-structure deltas (`platform/`, DuckDB tables, `semantic/rls.py`, `e2e/`, `load/`) follow
  the Shared doc §3; add them to the original §4 structure when scaffolding.
