# Moment GTM Dashboard — Prototype: Shared Architecture, Schema & Governance

> **Derived from:** `docs/requirements/Moment_GTM_Dashboard_RSD_v0.9_Summary.md` (RSD v0.9.1)
> **Scope:** foundation document shared by all 9 module plans · **Date:** 2026-10-14

This document holds everything common to every module prototype so the per-module plans stay
focused. It covers the tech stack (justified against the NFRs and acceptance criteria), the
standard layered architecture, the monorepo project structure, the full data-store / extract
schema across all source systems, the global UI and governance requirements, and the consolidated
roles & access matrix.

**Module plan set (9 modules):**
1. Executive summary — `docs/plans/Moment_GTM_Dashboard_Executive_Prototype_Plan.md`
2. Pipeline — `..._Pipeline_Prototype_Plan.md`
3. Pursuits & wins — `..._Pursuits_Wins_Prototype_Plan.md`
4. Offerings — `..._Offerings_Prototype_Plan.md`
5. Accounts — `..._Accounts_Prototype_Plan.md`
6. Partners — `..._Partners_Prototype_Plan.md`
7. Solutions capacity — `..._Solutions_Capacity_Prototype_Plan.md`
8. Market signals — `..._Market_Signals_Prototype_Plan.md`
9. Administration & governance — `..._Administration_Prototype_Plan.md`

**Working assumptions** (consistent with the Executive prototype decisions): custom React/TS web
app; Python/FastAPI backend acting as the semantic layer; synthetic data standing in for real
sources; metric logic defined once in the semantic layer; prototype runs locally (docker-compose).

---

## 1. Tech stack (justified against NFRs & acceptance criteria)

**Frontend:** React 18 + TypeScript + Vite · Recharts (charts, via `dataviz` skill) · TanStack
Query (server-state cache) · Zustand (filter state) · React Router · Tailwind CSS + Radix UI
(accessible popover/dialog).

**Backend / data platform:** Python 3.11+ · FastAPI + Uvicorn · Pydantic v2 (API contracts) ·
**DuckDB** as the embedded analytical store (raw → conformed → marts; swappable for Fabric/
Snowflake in production) · SQL transforms (dbt-style) or SQLAlchemy Core · Faker (seeded synthetic
data) · APScheduler (simulate daily/monthly extract cadence).

**Quality / testing:** pytest (metrics & API) · Playwright (e2e/UAT scripts) · axe-core
(accessibility) · k6 or Locust (load) · ruff/black + ESLint/Prettier · docker-compose.

**Why these — mapping to NFRs (§8):**

| NFR | Requirement | How the stack meets it |
|---|---|---|
| NFR-01 | Views <3s P90 @ 50 users; filters <2s | DuckDB columnar marts (pre-aggregated), TanStack Query cache, server-side pagination for registers |
| NFR-02 | CRM metrics fresh by 07:00 IST | APScheduler ELT jobs per source cadence; `/api/health` exposes per-source freshness |
| NFR-03 | 99.5% availability | Stateless FastAPI, containerized, horizontally scalable (prototype: single node) |
| NFR-04 | SSO via Entra ID | Pluggable Entra ID SSO: Mock Entra provider with 9 official personas and standard OIDC claims tokens (`oid`, `sub`, `upn`, `roles`, `groups`) in prototype; live Azure MSAL plug-in ready via `GTM_AUTH_MODE=azure` (no local accounts in prod) |
| NFR-05 | RLS by practice/account | Enforced in the semantic layer: every query takes a role-scope filter derived from Entra groups |
| NFR-06 | Data protection / classification | No client PII beyond business contacts; config-driven classification; residency per policy |
| NFR-07 | Audit (restricted access, target/threshold changes, exports) 12 mo | `audit_log` table written by API middleware |
| NFR-08 | WCAG 2.1 AA; status never colour alone | Radix primitives, `StatusBadge` (text+icon+colour), keyboard nav, visible focus; axe-core checks |
| NFR-09 | Responsive (Exec 390px, others tablet) | Tailwind responsive layout |
| NFR-10 | 5 yrs / 50k opportunities | DuckDB columnar + indexes + snapshot partitioning; pagination |
| NFR-11 | Maintainable, version-controlled defs | Metric definitions as code in `semantic/`; SQL transforms in VCS |
| NFR-12 | Observability (failures <30 min; run log) | ELT run-log table + structured logging; alert hook |
| NFR-13 | Edge/Chrome/Safari | Vite modern browser build |

**Why these — mapping to acceptance criteria (§12):**

| AC | Criterion | Plan |
|---|---|---|
| AC-01 | Metrics reconcile to source within 0.5% (3 cycles); bookings reconcile with Finance | Reconciliation test harness: metric result vs direct raw-zone query; monthly Finance reconciliation job |
| AC-02 | Must requirements pass UAT from RSD + mockup | Playwright UAT scripts per module keyed to FR IDs |
| AC-03 | RLS & restricted-metric access verified per role (incl. exports/alerts) | Role-matrix test suite running every role in §5 against every endpoint/export |
| AC-04 | NFR-01 met in load test | k6/Locust scenario at 50 concurrent users |
| AC-05 | Mandatory-field completeness gate (≥95%, 2 wks) | DQ console + completeness metric (see Administration plan) |
| AC-06 | Two weekly reviews run from dashboard, no deck | Process/adoption; dashboard must cover the full review flow (Exec + Pipeline) |
| AC-07 | WCAG 2.1 AA review | axe-core automated + manual keyboard/contrast review |

---

## 2. Standard layered architecture

```
External sources (CRM, Planning, Bid, Finance, Partner, M365/SharePoint, Adobe, LMS, …)
        │   (prototype: Faker generator writes the raw zone directly)
        ▼
Ingestion / ELT (APScheduler jobs; per-source cadence daily/nightly/weekly/monthly/on-change)
        ▼
Data platform  ──  RAW zone (landed per-source extract tables, partitioned by extract date)
                   CONFORMED zone (keys matched, currency→USD, reference data applied)
                   MARTS (per-module curated tables; weekly snapshot tables)
        ▼
Semantic layer (governed measures implementing RSD §5 exactly; RLS applied; metric registry)
        ▼
API (FastAPI REST; filters, drill-down, metric metadata, freshness, exports)
        ▼
Presentation (React SPA: nav rail, filter bar, module widgets per FR)
        ▼
Distribution (alerts & weekly digest; CSV/Excel/PDF export)
```

Metric logic lives **once** in the semantic layer and is reused by every view, export and alert.

---

## 3. Monorepo project structure

```
dashboard/
  README.md · docker-compose.yml · .gitignore
  docs/ architecture.md · metric-mapping.md · schema.md · governance.md
  backend/
    pyproject.toml / requirements.txt
    app/
      main.py · config.py                    # seed, plan FX, fiscal calendar, demo "today", RLS
      domain/ models.py · enums.py            # Pydantic/dataclass entities + enums
      platform/                               # the data platform (DuckDB)
        db.py                                 # DuckDB connection/bootstrap
        schema_raw.sql · schema_conformed.sql · schema_marts.sql
        elt/ run.py · raw_to_conformed.py · conformed_to_marts.py
        scheduler.py                          # APScheduler cadence per source
      data/
        generator.py                          # seeded synthetic extracts → raw zone
        reference_data.py                     # stage probs, thresholds, catalogues, targets
      semantic/
        filters.py · status.py · rls.py       # period/dim filters, status bands, row-level scope
        targets.py                            # filtered target slicing + pro-rating (FR-GEN-04)
        definitions.py                        # metric registry: id → {name, def, sources, owner}
        metrics/ exe.py · pip.py · pur.py · off.py · acc.py · par.py · cap.py · mkt.py
      api/routes/                             # one router per module + shared
        executive.py · pipeline.py · pursuits.py · offerings.py · accounts.py ·
        partners.py · solutions_capacity.py · market_signals.py ·
        opportunities.py · reference.py · admin.py · exports.py · alerts.py · health.py
      schemas/                                # pydantic response models per module
    tests/ test_metrics_*.py · test_rls.py · test_reconciliation.py · test_api.py
  frontend/
    index.html · vite.config.ts · tsconfig.json · package.json · .env
    src/
      main.tsx · App.tsx
      routes/ Executive.tsx · Pipeline.tsx · Pursuits.tsx · Offerings.tsx · Accounts.tsx ·
              Partners.tsx · SolutionsCapacity.tsx · MarketSignals.tsx · Admin.tsx
      components/
        layout/ AppShell · ModuleLayout · NavRail · FilterBar · DataFreshnessIndicator ·
                MetricIdsToggle · RoleSwitcher
        widgets/<module>/...                  # module widgets — compose shared parts only
        common/ WidgetCard · StatusBadge · MetricInfoPopover · DrilldownPanel · EmptyState ·
                ErrorState · Money · ExportMenu · SavedViews
        charts/ GoalBarChart · StackedSplitChart · FunnelChart · Heatmap · MatrixGrid ·
                DistributionHistogram · ProgressToTarget · Sparkline · KpiCard · KpiStrip ·
                RunwayChart                   # generic Recharts wrappers, data-in only
        data/ DataRegister                    # TanStack Table register
      api/ client.ts · <module>.ts · types.ts
      state/ filters.ts · role.ts · metricIds.ts (Zustand)
      hooks/ use<Module>Data.ts
      theme/ tokens.ts · global.css
      utils/ format.ts
  e2e/ playwright/<module>.spec.ts            # UAT scripts (AC-02)
  load/ k6/<scenario>.js                      # AC-04
```

Each module adds: a `semantic/metrics/<mod>.py`, an `api/routes/<mod>.py`, a `schemas/<mod>.py`,
a `routes/<Module>.tsx` + widgets, and (where new) raw/conformed/mart tables. Shared parts
(`layout/`, `common/`, `charts/`, `data/`, `semantic/` core, API building blocks) are built and
extended only via the project skill `.claude/skills/moment-gtm-reusable-components/SKILL.md`; build
sequence is in `docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md`.

---

## 4. Data-store & extract schema (all sources, daily/monthly cadence)

The **raw zone** lands one table per source object, partitioned by `extract_date`
(or `extract_month` for monthly sources); the **conformed zone** matches keys and applies reference
data; **marts** feed the semantic layer. Prototype: these are DuckDB tables seeded by the generator;
in production they are populated by the ELT from the APIs in each module plan.

**Extract cadence by source (RSD §6.2):**

| Source | Logical system | Cadence | Raw tables (prototype) |
|---|---|---|---|
| SRC-01 | CRM (pipeline SoR) | **Daily/nightly** (hourly optional) | `raw_crm_opportunity`, `raw_crm_opportunity_history`, `raw_crm_opportunity_line_item`, `raw_crm_opportunity_team_member`, `raw_crm_account`, `raw_crm_campaign`, `raw_crm_campaign_influence`, `raw_crm_user` |
| SRC-02 | Planning (targets) | On change / **quarterly** | `raw_planning_target` (+ version) |
| SRC-03 | Bid & proposal mgmt | **Nightly** | `raw_bid_pursuit`, `raw_bid_gate_review`, `raw_bid_proposal_asset` |
| SRC-04 | Finance ERP | **Monthly** (post close) | `raw_finance_contract`, `raw_finance_project_financials`, `raw_finance_cost_rate` |
| SRC-05 | Deal pricing | On approval | `raw_pricing_version` |
| SRC-06 | Resource mgmt | **Nightly** | `raw_resource`, `raw_resource_allocation` |
| SRC-07 | Timesheets | **Weekly** | `raw_timesheet_entry` |
| SRC-08 | Partner portals | **Monthly** | `raw_partner_deal_registration`, `raw_partner_certification`, `raw_partner_tier` |
| SRC-09 | LMS | **Weekly** | `raw_lms_learning_record` |
| SRC-10 | Marketing automation | **Nightly** | `raw_mktg_campaign`, `raw_mktg_campaign_member` |
| SRC-11 | Web CMS & analytics | **Weekly** | `raw_web_content_asset`, `raw_web_engagement_metric` |
| SRC-12 | Knowledge repository | **Weekly** | `raw_kb_asset` |
| SRC-13 | AI validation register | **Nightly** | `raw_validation_record` |
| SRC-14 | Account planning | **Weekly** | `raw_account_plan` |
| SRC-15 | Analyst relations tracker | On change | `raw_analyst_evaluation` |
| SRC-16 | Entra ID (identity) | **Nightly** | `raw_identity_user`, `raw_identity_group`, `raw_identity_group_membership` |
| SRC-17 | Asset development tracker | **Nightly** | `raw_asset_build` |

**Conformed zone — shared dimensions (built once, used by all modules):**
`dim_date` (with fiscal quarter), `dim_account` (vertical, strategic flag, hierarchy),
`dim_offering`, `dim_practice`, `dim_platform`, `dim_vertical`, `dim_partner`, `dim_person`
(architects/owners, Entra UPN), plus reference tables `ref_stage_probability`, `ref_threshold`,
`ref_bucket`, `ref_size_band`.

**Conformed facts / module tables** (detailed in each module plan):
`fact_opportunity`, `fact_opportunity_snapshot` (weekly), `fact_stage_history`,
`bridge_opportunity_practice`, `fact_target`, `fact_pursuit`, `fact_gate_review`, `fact_pricing`,
`fact_project_financials`, `fact_partner_engagement`, `fact_certification`, `fact_asset`,
`fact_asset_usage`, `fact_asset_build`, `dim_build_plan`, `fact_validation`, `dim_account_plan`,
`fact_campaign_member`, `fact_content_engagement`, `fact_analyst_eval`.

**Cross-cutting tables:** `audit_log` (NFR-07), `dq_finding` (DQ-01..09, §6.6), `elt_run_log`
(NFR-12), `ref_metric_definition` (feeds FR-GEN-07 metric-info popover).

**Master keys (RSD §6.4):** `CRM Opportunity ID` is the master key for every deal-level fact; all
other deal-level sources (bid, pricing, timesheet, validation) must carry it, else they go to a
matching queue surfaced in the DQ console.

---

## 5. Consolidated roles & access matrix (RSD §3, §9)

The dashboard enforces authentication and role-based access control (RBAC) via Microsoft Entra ID (SRC-16). In the prototype, 9 official Entra ID personas represent corporate directory users across 4 functional categories, issuing standard OIDC claims tokens (`oid`, `sub`, `upn`, `name`, `email`, `roles`, `groups`) matching DuckDB `raw_identity_*` records:

| Entra ID Persona | Official UPN | Assigned Role | Entra Security Group | Modules Accessible | Data Scope (RLS) | Restricted Metrics (`PUR-06`, `CAP-03`) |
|---|---|---|---|---|---|---|
| **Jordan Chen** | `jordan.chen@moment.internal` | `executive` (GTM Lead) | `GTM-Leadership-Restricted` | All 8 Modules + Admin | Unrestricted / Global | **Yes** |
| **Sam Rivera** | `sam.rivera@moment.internal` | `sales_leader` | `GTM-Sales-Leaders` | All 8 Modules | Unrestricted / Global | No |
| **Lena Ortiz** | `lena.ortiz@moment.internal` | `commercial_lead` (Finance BP) | `GTM-Commercial-Restricted` | All 8 Modules | Unrestricted (incl. margins) | **Yes** |
| **Ravi Kumar** | `ravi.kumar@moment.internal` | `practice_lead` | `GTM-Practice-DxP` | All 8 Modules | Own practice full (DxP/Commerce); others aggregated | No |
| **Asha Patel** | `asha.patel@moment.internal` | `client_partner` | `GTM-Client-Partners` | Exec, Pipeline, Accounts, Partners | Assigned strategic accounts | No |
| **Noah Brooks** | `noah.brooks@moment.internal` | `solution_architect` | `GTM-Solution-Architects` | Pipeline, Pursuits, Offerings, Capacity | All technical pursuits | No |
| **Mia Zhang** | `mia.zhang@moment.internal` | `alliance_lead` | `GTM-Alliance-Managers` | Exec, Partners, Offerings | Partner-tagged deals & tiers | No |
| **Omar Hassan** | `omar.hassan@moment.internal` | `marketing_lead` | `GTM-Marketing-Demand` | Exec, Market Signals | Campaign- & workshop-linked deals | No |
| **Kai Lindberg** | `kai.lindberg@moment.internal` | `offering_lead` | `GTM-Offering-Leaders` | All 8 Modules | Offering-tagged portfolio deals | No |

RLS is enforced in `semantic/rls.py` from Entra group membership and persona UPN claims (`SRC-16`); restricted metrics (PUR-06 margin erosion, CAP-03 presales cost of sale) are strictly gated to `executive` (Jordan Chen) and `commercial_lead` (Lena Ortiz) only, including on all API endpoints, exports, and alerts (NFR-05, AC-03).

---

## 6. Global UI requirements (RSD §10.1)

Applies to every module:
- Layout follows the mockup intent: **navigation rail**, **filter bar**, module panels.
- Every panel has a plain-language title, a one-line description, an **info control** (`MetricInfoPopover`)
  revealing the metric ID, definition, source systems and last refresh time (FR-GEN-07), and inline
  metric ID + source badges (`MetricTraceabilityBadges`) controlled by the global header
  **"Show metric IDs and sources"** toggle (`MetricIdsToggle`, RSD §1.1 & FR-GEN-07).
- Charts include tooltips with exact values; currency shown in **$M to one decimal**.
- Colour palette/typography follow Moment brand (mockup palette indicative; prototype uses an
  accessible placeholder in `theme/tokens.ts`).
- **Status never by colour alone** — always label + icon + colour (FR-GEN-05, NFR-08).
- Clear **empty and error states** explaining what is missing and what to do (FR-GEN-13).
- Global filters (period, vertical, practice, platform) persist within a session (FR-GEN-02);
  drill-down from any aggregate to opportunities and out to the CRM record (FR-GEN-06).
- **Additional filters (FR-GEN-03, Should):** account, **client partner**, deal source, geography,
  and a custom date range — available across modules in the filter bar.
- Data **freshness indicator** per source + staleness banner (FR-GEN-09).
- Export widget→CSV/Excel, view→PDF (FR-GEN-08). Responsive per NFR-09.

### 6.1 Filtered target comparison & pro-rating (FR-GEN-04, Must)

When filters are applied, every goal-based result must be compared against the **matching target
slice** from the planning source, not the whole-population target. This is a shared semantic
capability (`semantic/targets.py`), used by EXE-01, EXE-02, EXE-07, EXE-08 and any filtered goal
metric in other modules:
- **Exact slice first:** if `fact_target` holds a target at the active grain (e.g. quarter ×
  practice × vertical), use it directly.
- **Pro-rate when no target exists at that grain:** allocate the nearest-available parent target in
  proportion to the filtered slice's **pipeline share** (slice open/√ TCV ÷ parent-population TCV),
  so a practice/vertical filter still gets a sensible target.
- **Always label the result as "pro-rated"** in the API payload and in the UI (a badge on the
  widget), so users never mistake a derived target for a planned one.
- Plan-pace (the target pro-rated to today) is computed on the resulting slice target via
  `semantic/helpers.py`.
Reference data: `fact_target` / `target_version` (SRC-02), managed in Administration (FR-ADM-01).

---

## 7. Governance & change control (RSD §10.2) + Administration hooks

- **Metric ownership:** every metric has a named owner (RSD §5) who approves its definition and any
  change. The semantic layer's `definitions.py` + `ref_metric_definition` table are the single
  source of truth; changes are version-controlled (NFR-11).
- **Change control:** add/change-metric requests are logged, assessed by GTM Lead + Sales Ops, and
  released in a **monthly change window**. Goals/thresholds reviewed at FY start and after re-plan.
- **Data stewardship:** Sales Ops runs a weekly DQ review via the console (FR-ADM-04, DQ-01..09).
- **Admin console (FR-ADM-01..04):** load/version targets (audit trail); maintain goals,
  thresholds, buckets, bands, stage-probability table; maintain reference data; DQ console.
  Detailed in the Administration plan. All target/threshold/reference changes write to `audit_log`.

---

## 8. Shared verification

- `pytest` metric suites per module reconcile to raw-zone queries (AC-01).
- Playwright UAT scripts cover every **Must** requirement per module (AC-02).
- Role-matrix test suite verifies module visibility, RLS scope and restricted-metric gating,
  including exports/alerts (AC-03).
- k6 load test at 50 concurrent users meets NFR-01 (AC-04).
- axe-core + manual review confirm WCAG 2.1 AA (AC-07).
- `docker-compose up` runs DuckDB-backed API + React app; `/api/health` shows per-source freshness.
- Detail-scope RLS pattern (reference: EXE-10 — Executive plan §5.1): listed rows respect the caller's
  detail scope, while counts/aggregates (incl. `meta.by_vertical`) cover the full aggregate scope and
  the remainder is surfaced as an "aggregated other" note.

> Each module plan references this document for the stack, architecture, project structure, global
> UI/governance and the roles matrix, and adds only its module-specific metrics, APIs, schema,
> widgets, tasks and verification.
