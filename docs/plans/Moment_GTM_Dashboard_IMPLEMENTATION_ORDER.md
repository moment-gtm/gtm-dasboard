# Moment GTM Dashboard — Prototype Implementation Order (Roadmap)

> **Purpose:** the sequence to build the prototype across the module plans. Combines the
> foundation-first logic from `..._Reusable_Components_and_Skills.md`, the Executive-first decision,
> and the RSD delivery phasing (§11). Each step names the plan file to work from and why it sits
> where it does. Component-level contracts are enforced by the project skill
> `.claude/skills/moment-gtm-reusable-components/SKILL.md`. · Date: 2026-10-14 · Updated: 2026-10-22

## Progress
- **2026-10-15 — Steps 0 and 1 built** in `dashboard/` (see its README): shared
  foundation (mock source connectors, DuckDB raw→conformed→marts, semantic layer, API building blocks,
  shell/primitives/charts/DataRegister, minimal reference seed) + Executive summary (EXE-01..10, all
  nine personas). Synthetic data via mock APIs. Backend 140 tests, e2e UAT 16 tests passing.
  Hooks enabled per the table below except git pre-commit (Git not installed).
- **Step 2 Pipeline built** (PIP-01..07: funnel, ageing heatmap, by practice/platform, deal-size
  histogram, register, stage movement; new `FunnelChart` + `DistributionHistogram` primitives).
  Backend 224 tests and e2e UAT 28 tests (incl. 12 Pipeline) passing; frontend build + eslint clean.
  **Next: Step 3 Pursuits & Wins.**
- **Step 3 Pursuits & Wins built** (PUR-01..05: win rate by quarter, loss reasons, deal-source mix,
  bid discipline + orals conversion). New SRC-03 bid-tool connector, `fact_pursuit`, CRM
  `loss_reason`, DQ-04 for unmatched bid rows. **PUR-06 margin deferred to Step 6** (restricted;
  absent for every persona). Backend 291 tests and e2e UAT 40 tests (incl. 12 Pursuits) passing;
  frontend build + tsc + eslint clean.
- **Step 4 Administration & Governance built** (FR-ADM-01..05 minus alerts): versioned target and
  threshold editors with reasons and before/after audit, reference-data manager (in-use values
  protected), DQ engine DQ-01..09 (DQ-09 inactive until SRC-17) with ADM-01 completeness gate,
  findings console + CSV export, metric change control (assess → decide → release), audit trail.
  Backend 317 tests and e2e UAT 56 tests (incl. 16 Administration) passing; frontend build + tsc +
  eslint clean. Deferred: alerts (Step 7), metric-registry write-back from released changes,
  monthly change window recorded but not enforced.
- **Step 5 Offerings, Accounts and Partners built** (OFF-01..05, ACC-01..04, PAR-01..03 plus the
  FR-ACC-05 account detail panel). New mock sources SRC-08/09/12/13/14/17, build-plan, booking-history
  and proposal-asset feeds; DQ-09 now active (3 findings: released assets missing ID or type, excluded
  from OFF-05). New `ProgressToTarget` and `MatrixGrid` chart primitives. Watch thresholds for OFF-02,
  OFF-05, OFF-05-REUSE and ACC-02 are assumed (plans only give on-track values); OQ-11 (build-plan
  owner) open, so the plan is seeded. Backend 341 tests and e2e UAT 87 tests (incl. 31 new) passing;
  frontend build + tsc + eslint clean. **Next: Step 6 Solutions Capacity + restricted metrics.**
- **Step 6 Solutions Capacity + restricted metrics built** (CAP-01..04, PUR-06). New mock sources
  SRC-05 pricing, SRC-06 resource, SRC-07 timesheet; restricted gating (`guard_restricted`) audits
  allowed and denied access and covers endpoints, drill-down and exports; CAP-03 and PUR-06 panels are
  absent (not greyed) for non-restricted personas. Shared `useScopedQuery` hook extracted. Watch
  thresholds for CAP-01..03 and PUR-06 are assumed; OQ-08 (InfoSec approval for PUR-06) open; no
  separate `schemas/solutions_capacity.py` (`MetricResult` returned directly). Backend 362 tests and
  e2e UAT 101 tests passing; frontend build + tsc + eslint clean. **Next: Step 7 Market Signals + Alerts.**
- **Step 7 Market Signals + Alerts/digest engine built** (`MKT-01..04`, `FR-MKT-01..04`, `FR-ALR-01..03`).
  New mock sources `SRC-10` (Adobe Marketo / Journey Optimizer campaigns), `SRC-11` (Adobe AEM + CJA
  thought-leadership assets & engagement), `SRC-15` (Microsoft 365 Analyst Relations tracker), plus
  CRM discovery workshops (`raw_crm_workshop`) and conformed tables (`fact_campaign`, `fact_workshop`,
  `fact_content_engagement`, `fact_analyst_eval`). Semantic metrics `mkt.py` (`MKT-01..04` + drill-down
  predicates for `MKT-02` funnel stages and `MKT-03` campaigns/quarters, reconciled within 0.5% between
  `SRC-01` and `SRC-10`). Alerts & weekly digest engine (`services/alerts.py`, `/api/alerts/*`, persistent
  `AdminStore` tables) evaluates threshold rules (`coverage_drop` on `EXE-02`, `large_deal_slip`,
  `unvalidated_ai_propose` on `OFF-03`) and generates RLS-scoped Email & Teams digests (`EXE-01..06`,
  `EXE-10`, `CAP-01`) with user-managed channel subscriptions (`FR-ALR-03`). Backend 393 tests and e2e
  UAT 121 tests (incl. 16 Market Signals + 4 Alerts/Digest) passing; frontend build + tsc + eslint clean.
  **Next: Step 8 Hardening.**
- **2026-10-21 — Step 8 Hardening completed** (`AC-01..07`, all 9 modules & 9 personas gated):
  - **Cross-module drill-down (`backend/app/semantic/metrics/drill.py`, `opportunities.py`):** Wired
    `/api/opportunities` drill-down predicates for `OFF-01..03`, `ACC-01..03`, and `PAR-01..02` so all
    analytical modules share the unified drill-down and CSV export contract.
  - **AC-01 Reconciliation (`backend/tests/test_reconciliation.py`):** All 44 registered metrics across
    all 9 modules (`EXE-01..10`, `PIP-01..07`, `PUR-01..06`, `OFF-01..05`, `ACC-01..04`, `PAR-01..03`,
    `CAP-01..04`, `MKT-01..04`, `ADM-01`), plus `SRC-04` Finance month-end and `SRC-01` ↔ `SRC-10`
    campaign pipeline, reconcile within $\le 0.5\%$ against independent SQL over `raw_*` tables across
    3 consecutive ELT `rebuild()` cycles.
  - **AC-03 Consolidated Role & RLS Matrix (`backend/tests/test_rls.py`):** 106 tests covering the full
    9-persona × 9-module HTTP access matrix (81 cases), restricted metrics (`PUR-06`, `CAP-03`) across
    4 endpoints × 9 personas with `audit_log` verification (`restricted.access` / `restricted.denied`),
    Practice Lead aggregate vs detail (`AggregatedOther`), Client Partner account scope, Alliance Manager
    partner scope, Marketing campaign/workshop scope, CSV export RLS + audit, and weekly digest RLS.
  - **AC-04 / AC-05 Load & Performance (`load/k6/all_modules.js`, `backend/tests/test_api.py`):** 50-VU
    k6 load scenario across all 8 analytical modules and 9 personas (`p(90)<3000ms` views,
    `p(90)<2000ms` filters) and 50-user concurrent API P90 test passing with 0% error rate.
  - **AC-02 / AC-07 Cross-Module UAT, Mobile 390px & A11y (`e2e/playwright/hardening.spec.ts`,
    `e2e/screenshot.mjs`):** Cross-module navigation, filter persistence, drill-down, global
    `"Show metric IDs and sources"` header toggle (`MetricIdsToggle` / `FR-GEN-07`), 390px mobile
    no-overflow, and full 9-module screenshot harness.
  - **Documentation & CI Gate (`docs/metric-mapping.md`, `README.md`, `.claude/hooks/gtm_hooks.py`):**
    Complete 44-metric traceability matrix and `ci-gate` hook subcommand.
  - **Latest Verification Status:** Backend **446 passed, 0 failed** (`pytest -q`), backend lint
    **0 errors** (`ruff check app tests`), frontend unit tests **8 passed** (`vitest run`), frontend
    production build **clean** (`tsc -b && vite build`), e2e UAT **129 tests** (`8` new in
    `hardening.spec.ts`). **All prototype steps (Steps 0–8) complete.**
  - **Correction (2026-10-22):** a full e2e re-run showed **9 of 124 failing**, not all passing:
    `hardening.spec.ts` AC-02/03/07 used routes and test IDs that never existed (`/capacity`,
    `/market`, `opportunity-drawer`, `pur06-card`, …); the Market Signals spec had the
    Finance / Alliance access rows swapped against Shared doc §5; two MKT selectors were wrong
    (`funnel-step-*`, `campaign-drill-CMP-*`); and the FR-ALR-01 digest payload was missing keys the
    `DigestConfig` preview renders. All fixed in the entry below.
- **2026-10-22 — Bento leadership UI + e2e fixes:**
  - **Bento theme for the leadership audience** (all 9 modules): dark-navy `NavRail` with module icons,
    sticky glass header, pill `FilterBar`, `ModuleLayout` eyebrow + `highlights` scorecard slot,
    `BentoGrid`/`BentoItem`/`BentoRow` 12-column layout, `WidgetCard variant="hero"` + `headline`,
    `KpiCard` status rule, and the highlight set `SpotlightCard`, `StatusSpotlight`, `StatusSummary`,
    `ModuleHeadlines`, `ExportViewButton` (+ `AttentionSpotlight` EXE-10, `PipelineSpotlight`).
    Chrome colours live in `tokens.bento` / CSS variables; chart palette unchanged. Pattern in the
    components catalog §2a.
  - **Spotlight overlap fix:** a sticky spotlight is now confined to a `BentoRow` with its hero, so
    it stops at the hero's bottom edge instead of sliding over the rows below (verified by a
    scroll sweep: 0 overlapping positions on all 7 sticky modules, was 82).
  - **390px fix:** `NavRail` is a positioning container, so `.sr-only` labels on disabled modules no
    longer widen the page.
  - **e2e specs corrected** (`hardening.spec.ts` rewritten to real routes/test IDs, restricted panels
    asserted absent; `market_signals.spec.ts` selectors + access rows) and **digest contract fixed**
    additively in `semantic/alerts.py` (`metric_id`, `formatted_tcv`, `healthy_count`, `deep_link`,
    recipient `display_name`/`role_label`/`practice`, `body_markdown`, Teams `summary`, link `path`)
    with a new backend contract test.
  - **Verification (2026-10-22):** backend **447 passed** (`pytest -q`), `ruff check app tests` clean;
    frontend unit **12 passed** (`vitest run`), `tsc -b` + `eslint` + production build clean; e2e UAT
    **124 passed, 0 failed** (`npx playwright test --workers=1`, both servers running).
- **2026-10-23 — Module content density (80%):**
  - Module content renders at 80% on desktop (`lg`, ≥ 64rem), like browser zoom (text, spacing
    and tiles together): `ModuleLayout` root carries `.module-content` → `zoom: var(--content-scale)`;
    `--content-scale` is 0.8 from `lg` up and 1 below (phones keep full-size text), mirrored as
    `tokens.bento.contentScale`. Applies to all 9 modules (direct `ModuleLayout` or via `ModuleGate`).
    Nav rail, header, filter bar and portalled overlays stay at 100%; print resets to 1 so the
    register print-fit rules are unchanged. Sticky spotlight offset is `calc(6rem / --content-scale)`
    so it still clears the header. Catalog rows (`ModuleLayout`, `BentoGrid`, `theme/tokens.ts`)
    and the components skill updated. `e2e/screenshot.mjs` routes corrected
    (`/solutions-capacity`, `/market-signals`).
  - **Verification (2026-10-23):** frontend unit **12 passed**, `tsc -b` + `eslint` + production
    build clean; e2e UAT **124 passed, 0 failed** (run with the scale on all widths, before it was
    limited to `lg`); chart tooltips verified aligned under zoom; all 9 modules screenshotted at
    1440px and 390px.

## At-a-glance

| Step | Work | Plan file | RSD phase |
|---|---|---|---|
| 0 | Shared foundation (components, semantic, platform, API) + minimal reference/admin seed | Shared doc + Skills catalog | Phase 0 |
| 1 | Executive summary (reference vertical slice) | Executive | Phase 1 |
| 2 | Pipeline | Pipeline | Phase 1 |
| 3 | Pursuits & Wins (non-restricted; defer PUR-06) | Pursuits & Wins | Phase 1 |
| 4 | Administration & Governance (full module incl. DQ console) | Administration | Phase 1 |
| 5 | Offerings → Accounts → Partners | Offerings, Accounts, Partners | Phase 2 |
| 6 | Solutions Capacity + restricted metrics (CAP-03, PUR-06) | Solutions Capacity | Phase 2 |
| 7 | Market Signals + Alerts/digest engine | Market Signals (+ Administration) | Phase 3 |
| 8 | Hardening: reconciliation, UAT, role-matrix, load, a11y | all | Phase 1–3 (gate) |

---

## Step 0 — Shared foundation (build once, before any module)
**Files:** `docs/architecture/Moment_GTM_Dashboard_Shared_Architecture_Schema_Governance.md` +
`docs/claude/Moment_GTM_Dashboard_Reusable_Components_and_Skills.md` (§10 build order). Build every item via the
`moment-gtm-reusable-components` skill (golden rules, core contracts, definition of done).

1. Repo scaffold + tech stack (React/Vite + FastAPI + DuckDB), theme tokens, `AppShell`/`NavRail`/`FilterBar`.
2. Common UI primitives: `WidgetCard`, `StatusBadge`, `MetricInfoPopover`, `MetricIdsToggle`, `DrilldownPanel`,
   `Empty/ErrorState`, `Money`, `ExportMenu`, `DataFreshnessIndicator`, `RoleSwitcher`.
3. Semantic foundation: `filters.py`, `status.py`, `rls.py`, `targets.py` (FR-GEN-04 target
   slicing & pro-rating), `definitions.py`, `helpers.py` + the metric-module contract.
4. Data platform: raw→conformed→marts, shared dimensions, `generator.py`, `SnapshotBuilder`, `scheduler.py`.
5. API foundation: `FilterParams`, `/opportunities`, `/reference`, `/health`, `/exports`,
   `require_role`, audit middleware.
6. Chart primitives + `DataRegister`.
7. **Minimal reference/admin seed** (thresholds, targets, catalogues) — `status.py` reads thresholds
   from day one; the full Admin UI comes at Step 4.

> **Cross-cutting capabilities are staged, not built in Step 0:** audit middleware → Step 0.5;
> reconciliation + role-matrix harnesses → started in Step 1, gated in Step 8; DQ engine → Step 4;
> alerts/digest → Step 7. Stub these where an earlier tier needs them.

**Exit:** `docker-compose up` serves an empty shell with working filters, health/freshness, and the
chart/primitive library rendering sample data.

## Step 1 — Executive summary (reference vertical slice)
**File:** `docs/plans/Moment_GTM_Dashboard_Executive_Prototype_Plan.md` (incl. §12 addendum).

First real module — exercises the whole stack end-to-end (filters → semantic → API → widgets →
drill-down) and proves the foundation. It is RSD Phase 1 and the chosen flagship. Treat it as the
template every other module copies. Widgets use the skill's widget composition pattern,
`metrics/exe.py` follows the metric-module contract, and data comes through `useExecutiveData`.
**Exit:** all five Exec widgets live from the API; filters, drill-down, metric-info and status all
work; every shared component touched meets the skill's definition of done. EXE-10 additionally ships
the leadership view (tiles, flag-mix bar, vertical × reason `Heatmap`, largest-deals bars) — see
Exec plan §5.1; the `Heatmap` primitive built here is reused by Pipeline (PIP-02) in Step 2.

## Step 2 — Pipeline
**File:** `docs/plans/Moment_GTM_Dashboard_Pipeline_Prototype_Plan.md`.

Depends on `SnapshotBuilder` (Step 0) for PIP-07 and shares `DataRegister` with every drill-down.
**Exec + Pipeline together satisfy AC-06** (weekly review with no manual deck).

## Step 3 — Pursuits & Wins (non-restricted first)
**File:** `docs/plans/Moment_GTM_Dashboard_Pursuits_Wins_Prototype_Plan.md`.

Build PUR-01..05 (CRM + bid data). **Defer PUR-06 margin** — it needs pricing/Finance feeds and the
restricted-gating path; it lands in Step 6.

> Steps 1–3 = RSD **Phase 1 MVP**.

## Step 4 — Administration & Governance (promote the seed to the real module)
**File:** `docs/plans/Moment_GTM_Dashboard_Administration_Prototype_Plan.md`.

Versioned targets, editable thresholds, reference-data management, and the **DQ console**
(DQ-01..09 + the ≥95% completeness gate, AC-05). Stand it up before the data-heavier modules
multiply reference data, since every downstream module's status/thresholds depend on it.

## Step 5 — Offerings → Accounts → Partners
**Files:** `..._Offerings_`, `..._Accounts_`, `..._Partners_Prototype_Plan.md` (RSD **Phase 2**).

Within the group: **Offerings** first (richest MCP — Microsoft 365 + Adobe Workfront — and ties
back to EXE-05), then **Accounts** (RLS-by-account, account-plan source), then **Partners**
(external partner-portal APIs, monthly cadence).

## Step 6 — Solutions Capacity + restricted metrics
**File:** `docs/plans/Moment_GTM_Dashboard_Solutions_Capacity_Prototype_Plan.md`.

CAP-01/02 plus the **restricted metrics** CAP-03 (cost of sale) and PUR-06 (margin, deferred from
Step 3). Do them together so the restricted-gating + audit path (NFR-07, AC-03) is built and tested
once.

## Step 7 — Market Signals + Alerts
**File:** `docs/plans/Moment_GTM_Dashboard_Market_Signals_Prototype_Plan.md` (+ Alerts in the Administration plan).

RSD **Phase 3**. Most MCP-native module (Adobe Journey Optimizer/Marketing, AEM, CJA, Microsoft 365).
Finish with the **alerts & weekly-digest engine** (FR-ALR), which consumes metrics from Exec/
Offerings/Capacity — so it goes last, once those values exist.

## Step 8 — Hardening (interleaved, gated here)
Build the harnesses during Step 1 and add a suite per module as you go; this is the final full gate:
- Reconciliation harness — AC-01
- Playwright UAT per module — AC-02
- Role-matrix tests (RLS + restricted gating, incl. exports/alerts) — AC-03
- k6 load test at 50 concurrent users — AC-04
- axe-core + manual accessibility review — AC-07

---

## Hooks enablement order (staged alongside the steps)
Hooks are guardrails for the build, so they are enabled progressively — not all before Step 0 (the
tools/folders they check don't exist yet) and not after all modules (too late to prevent drift).
Hook definitions live in `docs/claude/Moment_GTM_Dashboard_Recommended_Hooks.md`; Claude Code hooks are written
to `.claude/settings.json` via the `update-config` skill, git hooks via `pre-commit install`.

| When | Hooks to enable | Why at this point |
|---|---|---|
| **Before Step 0** | SessionStart conventions reminder; PreToolUse **warnings** "load `moment-gtm-reusable-components`" and "load `dataviz` before chart code" | Need no code; ensure the skills are used from the first file |
| **Step 0.1** (right after repo scaffold) | `git init` + pre-commit: ruff, black, eslint, prettier, hygiene, deny-list (`*.duckdb`, `data/synthetic/*`, `.env`); Claude Code PostToolUse lint/format on edit | Linters and folders now exist; foundation code starts clean |
| **Step 0.3–0.4** (`definitions.py`, `generator.py`/ELT exist) | Metric-ID traceability check (warn); PreToolUse **block** on hand-edits to `platform/**`, `*.duckdb`, `data/synthetic/**` | The protected artifacts now exist |
| **Step 1** (first pytest/reconciliation tests) | Stop hook `pytest -q`; pre-push `pytest` + `vitest run` | Test harnesses start in Step 1 |
| **After Step 1 is stable** | Promote `dataviz` and metric-ID hooks from warn → **block** | Start as warnings until the team trusts them |
| **Step 8** | CI gates: Playwright UAT, role-matrix, k6, axe-core | Full acceptance gates (AC-02/03/04/07) |

> Application lifecycle hooks (FastAPI lifespan, RLS dependency, `require_role`, audit middleware,
> `use<Module>Data`) are code, not config — built in Step 0.4–0.5 and per module via the skill.

---

## Dependency rules that drive the order
- **Foundation (Step 0) blocks everything.**
- `SnapshotBuilder` → Pipeline PIP-07 and Exec EXE-02 trend.
- Admin thresholds/targets → every goal-based metric's status (minimal seed early, full module Step 4).
- Pricing + Finance feeds + restricted-gating → PUR-06 / CAP-03 (grouped in Step 6).
- Alerts consume other modules' metrics → last (Step 7).

## Notes
- Steps 1–8 copy the Executive module's pattern; each later module is thin composition over the
  Step 0 foundation (hence the short "project structure additions" in every module plan).
- Phasing mirrors RSD §11 but front-loads Administration (Step 4) because thresholds/DQ are
  cross-cutting in the prototype.
- Each step's "Exit" is its definition of done; the per-module plan's Verification section is the
  detailed acceptance.
- For every step, invoke the `moment-gtm-reusable-components` skill before building or changing a
  shared component or module widget. Precedence: RSD → Reusable Components catalog → skill. If a
  contract changes, update the catalog first, then the skill.
