---
name: moment-gtm-reusable-components
description: Build or extend the Moment GTM Dashboard's shared foundation layer — frontend shell, UI primitives, chart wrappers, data grid, state/data access, backend semantic layer, data platform, API building blocks and cross-cutting capabilities — to one consistent contract. Use whenever implementing, scaffolding or modifying any reusable component (NavRail, FilterBar, StatusBadge, MetricInfoPopover, MetricIdsToggle, DrilldownPanel, KpiCard, GoalBarChart, DataRegister, semantic/filters.py, status.py, rls.py, targets.py, FilterParams, require_role, audit middleware, DQ engine, etc.), or when building a module widget (Executive, Pipeline, Pursuits & Wins, Offerings, Accounts, Partners, Solutions Capacity, Market Signals, Administration) that should compose these components instead of re-implementing them.
---

# Moment GTM Dashboard — Reusable Components Skill

Source catalog: `docs/claude/Moment_GTM_Dashboard_Reusable_Components_and_Skills.md`, derived from
`docs/requirements/Moment_GTM_Dashboard_RSD_v0.9_Summary.md` and the 9 module plans. When this skill and the catalog
differ, the catalog wins. Read the catalog row for a component (and its RSD ref) before building it.

Module codes: `EXE PIP PUR OFF ACC PAR CAP MKT ADM`.

## Golden rules (apply to every component)

1. **Check before you build.** Search the codebase for an existing component or module from the
   catalog. Extend it; don't fork it. Module code must compose shared components and must not
   re-implement them.
2. **Foundation before modules.** Follow the build order below. A module adds only its ~5 widgets
   plus one `metrics/<mod>.py`. If a widget needs something generic, add it to the shared layer first.
3. **Status is never colour alone.** Always show text + icon + colour (`StatusBadge`). Bands come
   from `ref_threshold`, never hard-coded (FR-GEN-05, NFR-08).
4. **Money is `$M` to one decimal.** Always format through `Money` and its helpers (§10.1).
5. **Every number is traceable.** Each widget carries a metric ID that resolves through
   `semantic/definitions.py` to `MetricInfoPopover` (`FR-GEN-07`) and inline metric ID / source chips
   when the header `MetricIdsToggle` (`"Show metric IDs and sources"`, RSD §1.1) is switched on.
6. **RLS everywhere, including outputs.** Every query, drill-down, export and alert goes through
   `semantic/rls.py`. Restricted metrics (PUR-06, CAP-03) are also gated in exports (AC-03).
7. **Filters are global and consistent.** Frontend reads them from `state/filters.ts`. Backend
   applies them only through `semantic/filters.py` and the `FilterParams` model (FR-GEN-02).
8. **Pro-rated targets are labelled.** If no target exists at a grain, `semantic/targets.py`
   pro-rates the parent target by pipeline share and marks the result as pro-rated (FR-GEN-04).
9. **Accessible by default.** Use Radix primitives, keyboard navigation, visible focus, focus trap
   in panels and Escape to close (NFR-08, AC-07). Layout must be responsive from 390px to desktop.
10. **Charts follow the `dataviz` skill.** Invoke it before writing chart code. Take all colours
    from `theme/tokens.ts`.
11. **Every data widget has states.** Each widget handles loading, `EmptyState` (what's missing
    and how to fix it) and `ErrorState` (FR-GEN-13). Wrap widgets in `WidgetCard`, which provides
    these states.
12. **Bento layout for leadership.** Module routes lay out widgets only with `BentoGrid`/`BentoItem`
    and follow the module pattern: `eyebrow` + title, scorecard in `highlights`, one
    `variant="hero"` widget (span 8) beside a spotlight (span 4, `sticky`) — both inside a `BentoRow`
    so the sticky spotlight can't overlap the rows below — then 6/6 or 4/4/4 rows,
    long tables at 12. Spotlights (`SpotlightCard`) carry text, badges and actions only — never
    chart marks — and only say what the API already returned. Chrome colours come from
    `tokens.bento` / the matching CSS variables, never literals. Text size/density comes from
    `ModuleLayout`'s `--content-scale`; don't shrink fonts or add `zoom` inside a module or widget.

## Tech stack conventions

- **Frontend:** React + TypeScript, Recharts (chart primitives), TanStack Table (`DataRegister`),
  TanStack Query (data hooks), Zustand (`state/`), Radix UI (accessibility).
- **Backend:** Python, Pydantic query models, API routes under `/api/*`, APScheduler (`scheduler.py`).
- **Data:** raw → conformed → marts, plus shared `dim_*` dimensions.

## Build order (foundation tier)

1. `theme/tokens.ts` (+ `bento` chrome tokens), `AppShell`/`ModuleLayout`, `NavRail`, `FilterBar`, `BentoGrid`
2. Primitives: `WidgetCard`, `StatusBadge`, `MetricInfoPopover`, `MetricIdsToggle`, `DrilldownPanel`,
   `EmptyState`/`ErrorState`, `Money`, `ExportMenu`, `DataFreshnessIndicator`, `RoleSwitcher`,
   bento highlight set: `SpotlightCard`, `StatusSpotlight`, `StatusSummary`, `ModuleHeadlines`,
   `ExportViewButton`
3. Semantic: `filters.py`, `status.py`, `rls.py`, `targets.py`, `definitions.py`, `helpers.py`,
   metric-module contract
4. Data platform: raw→conformed→marts, shared dims, `generator.py`, `SnapshotBuilder`, `scheduler.py`
5. API: `FilterParams`, `/api/opportunities`, `/api/reference`, `/api/health`, `/api/exports`,
   `require_role`, `audit` middleware
6. Chart primitives and `DataRegister`
7. Minimal reference/admin seed (thresholds, targets, catalogues) so `status.py` and `targets.py`
   work from day one

Cross-cutting capabilities are staged across the roadmap, not built with the foundation (see
`docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md`): `audit` middleware ships with the API tier;
reconciliation and role-matrix harnesses start with the Executive module and are gated in
hardening; the DQ engine lands with Administration; alerts/digest come last with Market Signals.
Stub them if an earlier tier needs them.

If a requested component depends on an unbuilt earlier tier, say so and build or stub the
dependency first.

## Component catalog (quick reference)

### Frontend — shell (wraps every route)
| Component | Contract | RSD |
|---|---|---|
| `NavRail` | Dark-navy left nav with module icons; active module pill (`aria-current`); sticky on desktop | FR-GEN-01 |
| `FilterBar` | Period, vertical, practice, platform + account, client partner, deal source, geography, custom range; persists for the session | FR-GEN-02/03 |
| `DataFreshnessIndicator` | Per-source freshness; staleness banner when past SLA | FR-GEN-09, NFR-02 |
| `MetricIdsToggle` | Header `"Show metric IDs and sources"` toggle showing/hiding inline metric ID chips and source badges across all widgets | §1.1, FR-GEN-07 |
| `PersonaBadge` | Read-only signed-in persona + RLS scope (one persona per login) | §9, NFR-04/05 |
| `RoleSwitcher` | Demo-only persona dropdown, gated by `VITE_ENABLE_PERSONA_SWITCHER=true`; off by default | §9, NFR-04/05 |
| `AppShell` / `ModuleLayout` | Sticky glass header; title, `eyebrow`, one-line description, actions, `highlights` slot (scorecard), responsive grid; root `.module-content` renders module content at `--content-scale` (0.8 from `lg` up, 1 below; chrome stays 100%, print resets) — set density only there, never per module | §10.1, NFR-09 |
| `BentoGrid` / `BentoItem` / `BentoRow` | 12-col bento grid, spans 3·4·5·6·7·8·12; `sticky` pins a natural-height tile beside a taller one and must sit in a `BentoRow` with it (pin offset ÷ `--content-scale`) | §10.1, NFR-09 |

### Frontend — primitives
| Component | Contract | RSD |
|---|---|---|
| `WidgetCard` | Standard widget frame (bento tile): optional `eyebrow`, title, inline metric ID & source chips (`MetricTraceabilityBadges`, controlled by `MetricIdsToggle`), `MetricInfoPopover` info slot, `ExportMenu` actions slot, optional `StatusBadge`; owns loading/empty/error states; `variant="hero"` (module lead tile) + `headline` big-number slot | FR-GEN-07/08/13, §1.1, §10.1 |
| `StatusBadge` | On track / Watch / Off track shown as text + icon + colour | FR-GEN-05, NFR-08 |
| `MetricInfoPopover` | Metric ID, plain definition, sources, last refresh | FR-GEN-07 |
| `DrilldownPanel` | Opportunity list behind any aggregate; keyboard accessible, Esc closes, CRM deep link | FR-GEN-06 |
| `EmptyState` / `ErrorState` | What's missing and how to fix it | FR-GEN-13 |
| `Money` | `$M` to 1 dp; plus %, count and date helpers | §10.1 |
| `ExportMenu` | Widget → CSV/Excel; view → PDF (PPTX for EXE); RLS-gated | FR-GEN-08, AC-03 |
| `SavedViews` | Save and restore named filter views (Could) | FR-GEN-10 |
| `SpotlightCard` | Dark leadership call-to-action tile: eyebrow (`tone` alert/ok), headline, 2 stats, list, actions; no chart marks; owns loading/error | §10.1, FR-GEN-13 |
| `StatusSpotlight` | `SpotlightCard` listing a module's Off track → Watch metrics with value + badge + `status_basis`; ✓ status check when all clear | FR-GEN-05 |
| `StatusSummary` | Scorecard strip: count of Off track / Watch / On track, each text + icon + colour | FR-GEN-05, NFR-08 |
| `ModuleHeadlines` | `HeadlineScorecard` / `HeadlineSpotlight` / `toHeadlines` — wire a module `useHeadlines()` hook (deduped widget queries, called only after the access check) | §9 |
| `ExportViewButton` | Primary "Export view as PDF" header action: prints straight from the click, fires the audit log without awaiting it (never `await` before `window.print()`); print layout in `theme/global.css` `@media print` | FR-GEN-08 |

### Frontend — chart primitives (generic Recharts wrappers, data-in only)
`GoalBarChart` (bars vs goal, QTD marked) · `StackedSplitChart` · `FunnelChart` (counts/TCV +
conversion %) · `Heatmap` (count + value, threshold cells labelled) · `MatrixGrid` (Sold / Open /
Not addressed) · `DistributionHistogram` (configurable bands) · `ProgressToTarget` · `Sparkline` ·
`KpiCard` / `KpiStrip` (value + goal + `StatusBadge` + `Sparkline`; 4px status rule on top) · `RunwayChart` (booked/commit/
best-case + target + pace).

### Frontend — grid, state, data
`DataRegister` (TanStack Table: sort, search, server pagination, export, row highlight; `data-register`
class drives its print-fit rules, so keep it on the root) ·
`state/filters.ts` · `state/role.ts` · `state/metricIds.ts` · `api/client.ts` (typed fetch, error
normalisation, auth header) · `hooks/use<Module>Data.ts` (TanStack Query, query key includes
filters + role) · `theme/tokens.ts`.

### Backend — semantic layer
`semantic/filters.py` · `semantic/targets.py` · `semantic/status.py` · `semantic/rls.py` ·
`semantic/definitions.py` · `semantic/helpers.py` (weighted pipeline, plan pace, coverage, deal
cycle, days-in-stage, FX→USD, fiscal calendar) · `metrics/<mod>.py`.

### Backend — data platform
Raw→Conformed→Marts · `dim_date`, `dim_account`, `dim_offering`, `dim_practice`, `dim_platform`,
`dim_vertical`, `dim_partner`, `dim_person` · `SnapshotBuilder` (weekly, Mon 00:00 IST, 3-yr
retention) · `MatchingQueue` (CRM Opportunity ID master key; unmatched rows routed, DQ-04) ·
`generator.py` (seeded synthetic data) · `scheduler.py` · `elt_run_log` (alert within 30 min).

### Backend — API
`FilterParams` · `/api/opportunities` · `/api/reference` · `/api/health` · `/api/exports` ·
`require_role` · `audit` middleware → `audit_log` (restricted access, target/threshold changes,
exports).

### Cross-cutting
Accessibility kit · metric traceability · freshness/staleness · DQ engine (DQ-01..09 → `dq_finding`;
completeness gate ≥95% for 2 weeks) · audit & governance (versioned thresholds/targets) · alerts &
digest (coverage drop, ≥$5M slip, unvalidated AI-led in Propose; Teams/email) · reconciliation
harness (within 0.5% of raw over 3 cycles) · role-matrix test suite (role × module/endpoint/export).

## Core contracts (templates)

Adapt names to the existing code. If the code already defines one of these contracts, follow the
code.

### Metric-module contract — `metrics/<mod>.py`
One function per metric ID. Each returns value, status and breakdown.
```python
from pydantic import BaseModel
from semantic.filters import apply_filters
from semantic.rls import scope_for
from semantic.targets import target_for
from semantic.status import band

class MetricResult(BaseModel):
    metric_id: str            # e.g. "PIP-01" — must exist in semantic/definitions.py
    value: float | None
    target: float | None
    target_prorated: bool     # FR-GEN-04: label pro-rated targets
    status: str | None        # "on_track" | "watch" | "off_track" from ref_threshold
    breakdown: list[dict]     # rows that feed the chart primitive
    as_of: str                # source freshness timestamp

def pip_01(params: FilterParams, user: User) -> MetricResult:
    df = apply_filters(scope_for(user, load_mart("fct_opportunity")), params)
    value = ...
    target, prorated = target_for("PIP-01", params, df)
    return MetricResult(metric_id="PIP-01", value=value, target=target,
                        target_prorated=prorated, status=band("PIP-01", value, target),
                        breakdown=..., as_of=freshness("crm"))
```

### Shared query params — `FilterParams`
```python
class FilterParams(BaseModel):
    period: Literal["fytd", "quarter", "qtd", "custom"] = "fytd"
    start: date | None = None; end: date | None = None
    vertical: list[str] = []; practice: list[str] = []; platform: list[str] = []
    account: list[str] = []; client_partner: list[str] = []
    deal_source: list[str] = []; geography: list[str] = []
```
Every route takes `params: FilterParams = Depends()` plus the current user. Restricted routes add
`Depends(require_role(...))`.

### Frontend data hook — `hooks/use<Module>Data.ts`
```ts
export function usePipelineData() {
  const filters = useFilters();          // state/filters.ts
  const role = useRole();                // state/role.ts
  return useQuery({
    queryKey: ["pipeline", filters, role],
    queryFn: () => api.get<MetricResult[]>("/api/pipeline", { params: filters }),
  });
}
```

### Module route pattern (bento)
```tsx
const useHeadlines = () => toHeadlines([useWinRate(), useLossReasons(), /* … */]);

<ModuleGate moduleKey="pursuits" eyebrow="Win / loss" title="Pursuits & Wins" description="…"
            highlights={<HeadlineScorecard label="Pursuits scorecard" useHeadlines={useHeadlines} />}
            actions={<ExportViewButton module="pursuits" />}>
  <BentoGrid>
    <BentoRow>
      <BentoItem span={8}><WinRateTrend /></BentoItem>        {/* WidgetCard variant="hero" */}
      <BentoItem span={4} sticky><HeadlineSpotlight useHeadlines={useHeadlines} /></BentoItem>
    </BentoRow>
    <BentoItem span={6}><LossReasons /></BentoItem>
    <BentoItem span={6}><SourceMix /></BentoItem>
  </BentoGrid>
</ModuleGate>
```

### Widget composition pattern
```tsx
<WidgetCard title="Stage funnel" metricId="PIP-01" info={<MetricInfoPopover id="PIP-01" />}
            actions={<ExportMenu widgetId="PIP-01" />}>
  {q.isLoading ? <Skeleton /> : q.isError ? <ErrorState error={q.error} />
   : !data.breakdown.length ? <EmptyState reason="no-match-filters" />
   : <FunnelChart data={data.breakdown} onSelect={openDrilldown} />}
  <StatusBadge status={data.status} />
</WidgetCard>
<DrilldownPanel open={...} filters={...} onClose={...} />   {/* backed by /api/opportunities */}
```

## Definition of done for a reusable component

- [ ] It matches its catalog row (behaviour and RSD ref) and lives in the shared layer, not a module folder
- [ ] It has no hard-coded thresholds, colours or currency formats (uses `ref_threshold`, `tokens.ts` / bento CSS variables and `Money`)
- [ ] Module routes use `BentoGrid` and the bento module pattern (one hero, spotlight without chart marks, scorecard)
- [ ] It respects RLS and restricted gating, including in exports and alerts
- [ ] It is accessible: keyboard operable, visible focus, status not shown by colour alone
- [ ] It handles loading, empty and error states
- [ ] Any metric it exposes is registered in `semantic/definitions.py`
- [ ] Tests cover it, including a role-matrix case for anything RLS-sensitive
- [ ] The catalog doc is updated if the contract changed
