# Moment GTM Dashboard — Reusable Components & Capabilities ("Skills")

> **Purpose:** a build-once catalog of the reusable components, modules and capabilities identified
> by scanning all prototype plans (Executive, Pipeline, Pursuits & Wins, Offerings, Accounts,
> Partners, Solutions Capacity, Market Signals, Administration) and the Shared Architecture doc.
> Build these as a shared foundation **before** the per-module widgets; every module then composes
> them. · Derived from `docs/requirements/Moment_GTM_Dashboard_RSD_v0.9_Summary.md` + the 9 module plans.

**How to read the reuse column:** `EXE PIP PUR OFF ACC PAR CAP MKT ADM` = the modules that consume
the item (✓ = used; "all" = every module). RSD ref ties each item to the requirement it satisfies.

---

## 1. Frontend — layout & shell (build first; wraps every route)

| Component | What it does | Reused by | RSD ref |
|---|---|---|---|
| `NavRail` | Dark-navy left navigation across all modules with a decorative icon per module; active module indicated (pill + accent rule, `aria-current`); sticky on desktop | all | FR-GEN-01 |
| `FilterBar` | Global filters (period, vertical, practice, platform) + extras (account, **client partner**, deal source, geography, custom date range); persists within session | all | FR-GEN-02/03 |
| `DataFreshnessIndicator` | Per-source freshness + staleness warning banner when older than SLA | all | FR-GEN-09, NFR-02 |
| `MetricIdsToggle` | Global header toggle (`"Show metric IDs and sources"`) that shows/hides inline metric ID chips and source badges across all `WidgetCard` and `KpiCard` instances | all | §1.1, FR-GEN-07 |
| `PersonaBadge` | Read-only persona + RLS scope of the signed-in user (one persona per login) | all | §9, NFR-04/05 |
| `RoleSwitcher` | **Demo-only** persona dropdown, rendered only when `VITE_ENABLE_PERSONA_SWITCHER=true` (needs backend `GTM_ENABLE_PERSONA_SWITCHER=1` + `GTM_ALLOW_PASSWORDLESS_LOGIN=1`) | all | §9, NFR-04/05 |
| `UserProfile` | Active user avatar and Entra ID identity details popover in the top header with logout action | all | §9, NFR-04 |
| `AppShell` / `ModuleLayout` | Page scaffold: sticky glass header, title, one-line description, info control, responsive grid (390px → desktop). `ModuleLayout` adds an `eyebrow` (small uppercase context label) and a `highlights` slot under the title for the module scorecard. **Content density:** the `ModuleLayout` root carries `.module-content`, which renders the module at `--content-scale` (0.8 from the `lg` breakpoint up, 1 below — like browser zoom: text, spacing and tiles scale together). Nav rail, header, filter bar and portalled overlays stay at 100%; print resets to 1. Change the density in one place (`--content-scale` + `tokens.bento.contentScale`), never per module | all | §10.1, NFR-09 |
| `BentoGrid` / `BentoItem` / `BentoRow` | Bento layout: 12-column grid (1 column below `lg`) with fixed spans `3·4·5·6·7·8·12`. Items fill their row by default; `sticky` keeps a tile at natural height pinned under the header beside a taller neighbour (used for spotlights). **A sticky item must sit in a `BentoRow` with its hero** — the row bounds the sticky range so the spotlight stops at the hero's bottom edge instead of overlapping the rows below. The pin offset is divided by `--content-scale` so it still clears the unscaled header. Every module route lays out its widgets with this — no ad-hoc grids | all | §10.1, NFR-09 |

## 2. Frontend — common UI primitives (the highest-leverage reuse)

| Component | What it does | Reused by | RSD ref |
|---|---|---|---|
| `WidgetCard` | Standard frame for every module widget (bento tile: 20px radius, soft elevation): optional `eyebrow`, title, inline metric ID & source badges (`MetricTraceabilityBadges`, shown when `MetricIdsToggle` is on), `MetricInfoPopover` info slot, `ExportMenu` actions slot, optional `StatusBadge`; owns loading (`Skeleton`) / `EmptyState` / `ErrorState` so widgets don't repeat them. `variant="hero"` marks the one widget a module leads with (accent top rule + blue wash, larger title); `headline` renders a big-number slot under the header (hidden while loading/error/empty) | all | FR-GEN-07/08/13, §1.1, §10.1 |
| `StatusBadge` | On track / Watch / Off track as **text + icon + colour** (never colour alone); bands from `ref_threshold` | all goal-based (EXE PIP PUR OFF ACC PAR CAP) | FR-GEN-05, NFR-08, App. B |
| `MetricInfoPopover` | On-demand metric ID, plain-language definition, source systems, last refresh | all | FR-GEN-07 |
| `DrilldownPanel` | Opens the underlying opportunity list from any aggregate; keyboard accessible, Escape to close, deep-link to CRM | all CRM-based | FR-GEN-06, NFR-08 |
| `EmptyState` / `ErrorState` | "What's missing / how to fix" states for no-match filters or failed source | all | FR-GEN-13 |
| `Money` | Currency formatting in **$M to one decimal** (+ %, counts, dates helpers) | all | §10.1 |
| `ExportMenu` | Widget → CSV/Excel, view → PDF (PPTX for Exec); honours RLS/restricted gating on output | all | FR-GEN-08, AC-03 |
| `SavedViews` | Save/restore named filter views | all (Could) | FR-GEN-10 |
| `SpotlightCard` | Dark, high-emphasis bento tile for the one thing leadership should act on: eyebrow (`tone` alert ⚠ / ok ✓), headline sentence, 2 big stats, list slot, actions. **Text, badges and buttons only — never chart marks** (the chart palette is validated for the light surface). Owns loading/error states | all | §10.1, FR-GEN-13 |
| `StatusSpotlight` | Generic `SpotlightCard` fed by a module's headline `MetricResult`s: lists Off track then Watch metrics with value, `StatusBadge` and the API's `status_basis`; switches to a ✓ "Status check" listing on-track metrics when nothing is flagged. Counts statuses only — no banding | PUR OFF ACC PAR CAP MKT | FR-GEN-05 |
| `StatusSummary` | Scorecard strip — counts of Off track / Watch / On track across a module's headline metrics, each as text + icon + colour; hidden when no status is known | all goal-based | FR-GEN-05, NFR-08 |
| `ModuleHeadlines` (`HeadlineScorecard`, `HeadlineSpotlight`, `toHeadlines`) | Wires a module-level `useHeadlines()` hook (the same queries the widgets use, deduped by TanStack Query) into the scorecard + spotlight. The hook is only called inside these components so nothing is fetched before the access check passes; disabled restricted-only queries (PUR-06, CAP-03) are ignored for loading | PIP PUR OFF ACC PAR CAP MKT | §9, NFR-05 |
| `ExportViewButton` | Primary "Export view as PDF" header action: calls `window.print()` straight from the click and fires the view-export audit (`/api/exports/view`) without awaiting it, so a slow or failed API never blocks the dialog. Print layout lives in the `@media print` block of `theme/global.css` (white page, no nav/filter bar, no trailing blank page, tiles never split) | all except ADM | FR-GEN-08 |

### 2a. Bento module layout (leadership view) — the pattern every module route follows

```
eyebrow · Title · description                              [Export view as PDF]
[ <Module> scorecard: n Off track · n Watch · n On track ]       ← highlights slot
╔═ BentoRow ═══════════════════════════════════════════════════════════════════════════╗
║┌──────────── hero widget (span 8, variant="hero") ─────┐ ┌ spotlight (span 4, sticky) ┐║
║└───────────────────────────────────────────────────────┘ └────────────────────────────┘║
╚══════════════════════════════════════════════════════════════════════════════════════╝
┌──── widget (span 6) ────┐ ┌──── widget (span 6) ────┐   (or 4·4·4 for short tiles)
┌──────────── long table / register (span 12) ──────────┐
```

| Module | Hero (`variant="hero"`) | Spotlight | Scorecard |
|---|---|---|---|
| EXE | Bookings runway (+ `headline`: booked TCV, plan pace, FY target) | `AttentionSpotlight` — EXE-10 flagged deals, TCV at risk, top 3, *Review flagged deals* | north-star KPIs EXE-01..06 |
| PIP | Stage funnel | `PipelineSpotlight` — deals past review line (PIP-02), open TCV/count, WoW change, conversion (Pipeline has no thresholds, so no status) | PIP-01..07 (hidden: no statuses) |
| PUR | Win rate by quarter | `StatusSpotlight` | PUR-01..05 (+PUR-06 restricted) |
| OFF | Pipeline and wins by offering | `StatusSpotlight` | OFF-01..05 |
| ACC | Practice penetration | `StatusSpotlight` | ACC-01..04 |
| PAR | Pipeline by partner | `StatusSpotlight` | PAR-01..03 |
| CAP | Architect load | `StatusSpotlight` | CAP-01,02,04 (+CAP-03 restricted) |
| MKT | Thought leadership | `StatusSpotlight` | MKT-01..04 |
| ADM | — (segmented tab bar in a tile) | — | — |

Rules: one hero per module; a sticky spotlight lives in a `BentoRow` with its hero; spotlights carry no chart marks; status still text + icon + colour;
anything a spotlight says must be a value or status the API already returned (no UI-side metric logic).

## 3. Frontend — chart / visualization primitives (wrap Recharts; follow the `dataviz` skill)

Build these generic chart wrappers once with the shared palette/tokens, then feed module data.

| Primitive | What it does | Reused by | Example widgets |
|---|---|---|---|
| `GoalBarChart` | Bars vs target/goal marker, current period marked QTD | EXE PUR PAR CAP ACC | Bookings by quarter (EXE-08), win rate (PUR-01) |
| `StackedSplitChart` | Two/three-way stacked split with labels | EXE OFF PAR | Pipeline by vertical qualified/Identify (EXE-09), AI-led split (OFF-03), sourced/influenced (PAR-01) |
| `FunnelChart` | Ordered stages with counts/TCV + conversion % | PIP MKT | Stage funnel (PIP-01), workshop funnel (MKT-02) |
| `Heatmap` | 2-D grid, count + value per cell, threshold cells distinguished + labelled (**built in Step 1** for EXE-10: vertical × reason) | PIP EXE | Pipeline ageing (PIP-02), deals needing attention (EXE-10) |
| `MatrixGrid` | Entity × category cells with tri-state (Sold/Open/Not addressed) | ACC | Account penetration (ACC-01) |
| `DistributionHistogram` | Counts across configurable bands | PIP CAP | Deal size (PIP-05), quality scores (CAP-04) |
| `ProgressToTarget` | Progress bar vs required/target with status | PAR CAP EXE | Certifications (PAR-03), coverage (EXE-02) |
| `Sparkline` | Compact N-quarter trend inside a KPI card | EXE | KPI strip trends (EXE-01..06) |
| `KpiCard` / `KpiStrip` | Value + goal + `StatusBadge` + `Sparkline` tile and row; a 4px status-coloured rule across the top echoes the badge (which still carries text + icon) so a leader can scan the strip for red/amber; lifts on hover when drillable | EXE (+ reusable for any module summary) | North-star KPIs (FR-EXE-02) |
| `RunwayChart` | Stacked booked/commit/best-case + target + pace markers | EXE | Bookings runway (EXE-07) |

## 4. Frontend — data grid

| Component | What it does | Reused by | RSD ref |
|---|---|---|---|
| `DataRegister` (TanStack Table) | Sortable, searchable, server-paginated, exportable table with row highlighting (e.g. ageing). Root carries the `data-register` class: in print it drops the scroll clip, shrinks to 9.5px, wraps between words, hides sort arrows and keeps rows whole so every column fits A4 (scoped to registers so charts/heatmaps keep their size) | PIP (opportunity register), OFF (asset register), ACC (plan health) + every `DrilldownPanel` | FR-PIP-05, FR-GEN-06, FR-GEN-08 |

## 5. Frontend — state & data access

| Module | What it does | Reused by | Notes |
|---|---|---|---|
| `state/filters.ts` (Zustand) | Global filter state → feeds every query key | all | Persist for session |
| `state/role.ts` (Zustand) | Active role → RLS scope + restricted visibility | all | Set by login (`useAuthStore.setAuth`); shown by `PersonaBadge` |
| `state/metricIds.ts` (Zustand) | Global `"Show metric IDs and sources"` toggle state → shows/hides inline metric ID & source chips | all | Persist for session (`gtm-metric-ids`), drives `MetricIdsToggle` |
| `api/client.ts` | Typed fetch wrapper, error normalization, auth header | all | |
| `hooks/use<Module>Data.ts` + TanStack Query | Caching, refetch-on-filter-change pattern | all | One per module, same shape |
| `theme/tokens.ts` | Accessible palette + typography (Moment placeholder) + `bento` chrome tokens (nav, spotlight gradient/ink/rows, hero wash, header glass, radii, `contentScale` module density), mirrored as CSS custom properties in `theme/global.css` | all | Single source for chart + UI colour; chart colours unchanged by the bento theme |

## 6. Backend — semantic layer building blocks (the authoritative reuse)

| Module | What it does | Reused by | RSD ref |
|---|---|---|---|
| `semantic/filters.py` | Apply period (FYTD / quarter / current QTD / custom) + vertical/practice/platform consistently to any dataset | all | FR-GEN-02 |
| `semantic/targets.py` | Match filtered results to the target slice; pro-rate the parent target by pipeline share when none exists at that grain; **label pro-rated** | all goal-based (EXE OFF ACC PAR CAP) | FR-GEN-04 |
| `semantic/status.py` | Threshold banding → On track/Watch/Off track from `ref_threshold`; admin-editable, no code change | all goal-based | FR-GEN-05, App. B |
| `semantic/rls.py` | Row-level scope by role/practice/account; restricted-metric gating (PUR-06, CAP-03) incl. exports/alerts | all | §9, NFR-05, AC-03 |
| `semantic/definitions.py` | Metric registry (id → name, definition, source IDs, owner) → feeds `MetricInfoPopover` and `ref_metric_definition` | all | FR-GEN-07, §10.2 |
| `semantic/helpers.py` | Weighted pipeline, plan pace, coverage, deal cycle, days-in-stage, FX→USD, fiscal-calendar/quarter utilities | all | §1.5, §5, §7.3 |
| Metric-module pattern `metrics/<mod>.py` | Consistent "one function per metric ID returning value+status+breakdown" contract | all | §5 |

## 7. Backend — data platform building blocks

| Module | What it does | Reused by | RSD ref |
|---|---|---|---|
| Raw→Conformed→Marts pattern | Landed per-source extract → keys matched/currency/reference applied → curated marts | all | §7.1 |
| Shared dimensions | `dim_date`, `dim_account`, `dim_offering`, `dim_practice`, `dim_platform`, `dim_vertical`, `dim_partner`, `dim_person` | all | §7.2, §6.4 |
| `SnapshotBuilder` | Weekly snapshot of open opportunities (Mon 00:00 IST, 3-yr retention) for trend/movement | EXE PIP | FR-GEN-11, §7.3 |
| `MatchingQueue` | Enforce CRM Opportunity ID master key; route unmatched bid/pricing/timesheet/validation rows | PUR OFF CAP | §6.4, DQ-04 |
| `generator.py` utilities | Seeded synthetic extract generation (deals, accounts, targets, pursuits, assets, campaigns…) | all | prototype data |
| `scheduler.py` (APScheduler) | Simulate per-source cadence (daily/nightly/weekly/monthly/on-change) | all | §6.2, NFR-02 |
| `elt_run_log` | Run/failure logging; alert hook within 30 min | all | NFR-12 |

## 8. Backend — API building blocks

| Module | What it does | Reused by | RSD ref |
|---|---|---|---|
| `FilterParams` query model | Shared Pydantic query params (period, vertical, practice, platform, account, …) | all routes | FR-GEN-02 |
| `/api/opportunities` drill-down | Filtered, sortable opportunity list behind every aggregate | all | FR-GEN-06 |
| `/api/reference` | Filter options, thresholds, metric metadata | all | FR-GEN-07, FR-ADM-02/03 |
| `/api/health` | Per-source freshness timestamps | all | FR-GEN-09, NFR-02 |
| `/api/exports` | CSV/Excel/PDF export honoring RLS | all | FR-GEN-08 |
| `require_role` dependency | Route/field gating for restricted metrics + admin | PUR CAP ADM | §9, AC-03 |
| `audit` middleware | Write restricted access / target-threshold changes / exports to `audit_log` | all | NFR-07 |

## 9. Cross-cutting capabilities ("skills" the app provides)

| Capability | What it provides | Spans | RSD ref |
|---|---|---|---|
| **Accessibility kit** | Radix primitives, focus trap, keyboard nav, visible focus, status-not-colour-alone | all | NFR-08, AC-07 |
| **Metric traceability** | Every widget → metric ID → definition → source, end-to-end | all | FR-GEN-07, §1.1 |
| **Freshness & staleness** | Per-source freshness surfaced in UI + banners | all | FR-GEN-09, NFR-02 |
| **DQ engine** | Rules DQ-01..09 → `dq_finding` by owner; completeness gate (≥95%, 2 wks) | all (console in ADM) | §6.6, FR-ADM-04, AC-05 |
| **Audit & governance** | `audit_log`, metric change-control workflow, versioned thresholds/targets | all (ADM) | NFR-07, §10.2, FR-ADM-01/02 |
| **Alerts & digest engine** | Rule evaluation (coverage drop, ≥$5M slip, unvalidated AI-led in Propose) + Teams/email digest | EXE OFF CAP (ADM) | FR-ALR-01/02 |
| **Reconciliation harness** | Metric result vs direct raw-zone query within 0.5% (3 cycles); Finance month-end | all | AC-01 |
| **Role-matrix test suite** | Every role × module/endpoint/export verifies RLS + restricted gating | all | AC-03 |

## 10. Reuse summary — build these first (foundation tier)

Order of build so modules can compose them immediately:
1. **Theme/tokens + AppShell + NavRail + FilterBar + BentoGrid** (shell everything renders in).
2. **Common primitives:** `WidgetCard`, `StatusBadge`, `MetricInfoPopover`, `MetricIdsToggle`,
   `DrilldownPanel`, `EmptyState`/`ErrorState`, `Money`, `ExportMenu`, `DataFreshnessIndicator`, `RoleSwitcher`,
   plus the bento highlight set: `SpotlightCard`, `StatusSpotlight`, `StatusSummary`, `ModuleHeadlines`, `ExportViewButton`.
3. **Semantic foundation:** `filters.py`, `status.py`, `rls.py`, `targets.py`, `definitions.py`,
   `helpers.py` + the metric-module contract.
4. **Data platform:** raw→conformed→marts + shared dimensions + `generator.py` + `SnapshotBuilder`
   + `scheduler.py`.
5. **API foundation:** `FilterParams`, `/opportunities`, `/reference`, `/health`, `/exports`,
   `require_role`, `audit` middleware.
6. **Chart primitives** (§3) + `DataRegister`.
7. **Minimal reference/admin seed:** thresholds, targets, catalogues — so `status.py` and
   `targets.py` work from day one.

**Cross-cutting capabilities (§9) are staged across the roadmap**, not built with the foundation
(see `docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md`): `audit` middleware ships with the API tier;
reconciliation + role-matrix harnesses start with Executive (Step 1) and are gated in Step 8; the
DQ engine lands with Administration (Step 4); alerts/digest come last (Step 7).

Only after this foundation exist should each module's ~5 widgets + one `metrics/<mod>.py` be built —
each is then thin composition over the reusable layer above. This is why every module plan's
"project structure additions" is short: the heavy lifting is shared here.

---

### Claude Code skill
This catalog is packaged as the project skill `.claude/skills/moment-gtm-reusable-components/SKILL.md`
(invoke with `/moment-gtm-reusable-components`, or Claude loads it automatically when building these
components), so reusable components are generated to the same contract every time.
