# Moment GTM Dashboard — Recommended Hooks (Advisory)

> **Purpose:** hooks worth adding to this project, derived by scanning all prototype plans + the
> reusable-components/skills catalog. Each entry lists the trigger, the command, the rationale, and
> the RSD/NFR/AC requirement it enforces. · Date: 2026-10-14 · Updated: 2026-10-22
>
> **Status (2026-10-22):** the **Claude Code hooks in §A are active**, implemented in
> `.claude/hooks/gtm_hooks.py` and wired in `.claude/settings.json` as subcommands `session-start`
> (conventions), `pre-edit` (skill reminders, metric-ID check, block on generated artifacts),
> `post-edit` (ruff/black · eslint/prettier on the edited file) and `stop` (`pytest -q` when backend
> files changed since the last green run); `ci-gate` (reconciliation + RLS + API suites) is a
> manual subcommand, not wired to an event. **Git hooks (§B) are not enabled** — Git is not installed on this
> workstation. §C lifecycle hooks are built as application code.

**Why hooks help here:** the plans repeat the same gates across all 9 modules — lint/format,
metric reconciliation (AC-01), UAT (AC-02), RLS/role tests (AC-03), load (AC-04), accessibility
(AC-07, NFR-08), the "load `dataviz` before chart code" rule, metric traceability (FR-GEN-07), and
protection of generated DuckDB/synthetic artifacts. Hooks let these run automatically instead of
by memory.

---

## A. Claude Code hooks (`.claude/settings.json`) — automate during Claude Code sessions

| Event / matcher | Command (illustrative) | Rationale | Enforces |
|---|---|---|---|
| **PostToolUse** · Edit/Write on `backend/**/*.py` | `ruff check --fix "$FILE" && black "$FILE"` | Keep Python lint/format clean per edit | Tooling, NFR-11 |
| **PostToolUse** · Edit/Write on `frontend/**/*.{ts,tsx}` | `eslint --fix "$FILE" && prettier -w "$FILE"` | Keep TS lint/format clean per edit | Tooling, NFR-11 |
| **PreToolUse** · Write/Edit on `**/widgets/**` or `**/*Chart*.tsx` | echo reminder + non-zero exit to block: "Load the `dataviz` skill before writing chart code" | Every module's widget tasks say to use the dataviz skill first | Skills catalog §3, §10.1 |
| **PreToolUse** · Write/Edit on `**/components/{layout,common,charts,data}/**`, `**/widgets/**`, `semantic/*.py` | echo reminder (warn, don't block): "Load the `moment-gtm-reusable-components` skill — extend shared components, don't fork" | Project skill now packages the catalog; keeps modules composing the shared layer | Skills catalog §10, `SKILL.md` |
| **PreToolUse** · Write/Edit on `backend/app/platform/**`, `**/*.duckdb`, `data/synthetic/**` | block with message "Generated data-platform artifact — regenerate via ELT, don't hand-edit" | Protect raw→conformed→marts + synthetic store | §7.1, data integrity |
| **PreToolUse** · Write/Edit on `semantic/metrics/*.py` | warn if the touched metric ID is missing from `definitions.py` | Every metric must carry ID/definition/source | FR-GEN-07, §10.2 |
| **Stop** (end of a change) | `cd backend && pytest -q` | Fast metric/API suite before handing back | AC-01/02 |
| **SessionStart** | print conventions (layer boundaries, metric-ID rule, RLS in semantic layer, **bento leadership UI pattern**) | Keep contributors on the architecture and the leadership UI | Shared doc §2, catalog §2a |
| **PreToolUse** · Write/Edit on `frontend/src/routes/**` | echo reminder (warn): "Module route: follow the bento module pattern — `BentoGrid`, eyebrow + `HeadlineScorecard`, one `variant="hero"` widget + sticky spotlight **inside a `BentoRow`**, `ExportViewButton`; headline hooks only inside `ModuleHeadlines` (after the access check)" | Keeps every module on one leadership layout; prevents the sticky-spotlight overlap regression | Catalog §2a, NFR-09 |

**Example `.claude/settings.json` fragment (illustrative — the live config is in `.claude/settings.json`):**
```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [{ "type": "command",
          "command": "f=\"$CLAUDE_FILE_PATH\"; case \"$f\" in *.py) ruff check --fix \"$f\" && black \"$f\";; *.ts|*.tsx) npx eslint --fix \"$f\" && npx prettier -w \"$f\";; esac" }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "cd backend && pytest -q || true" }] }
    ]
  }
}
```
> Note: exact env var names/schema should be confirmed against the installed Claude Code version
> when you enable these (the `update-config` skill handles the correct format).

---

## B. Git hooks (team-wide, editor-agnostic) — `pre-commit` or husky + lint-staged

| Stage / files | Command | Rationale | Enforces |
|---|---|---|---|
| pre-commit · `*.py` | ruff, black | Format/lint gate for all contributors | NFR-11 |
| pre-commit · `*.ts,*.tsx` | eslint, prettier | Same for frontend | NFR-11 |
| pre-commit · all | trailing-whitespace, end-of-file-fixer, large-file guard | Hygiene | — |
| pre-commit · deny-list | block committing `*.duckdb`, `data/synthetic/*`, `.env` | Don't commit generated data/secrets | §6/§7, NFR-06 |
| pre-commit · `semantic/metrics/*.py` | custom check: each new metric ID present in `ref_metric_definition`/`definitions.py` | Metric traceability | FR-GEN-07 |
| pre-push | `pytest -q` (backend) + `vitest run` (frontend unit) | Block pushing red tests | AC-01/02 |
| CI (not a local hook, but same intent) | Playwright UAT, role-matrix RLS tests, k6 load, axe-core | Full acceptance gates | AC-02/03/04/07 |

**Example `.pre-commit-config.yaml` (illustrative):**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks: [{ id: ruff, args: [--fix] }]
  - repo: https://github.com/psf/black
    hooks: [{ id: black }]
  - repo: local
    hooks:
      - id: metric-id-traceability
        name: metric ID must be registered
        entry: python scripts/check_metric_ids.py
        language: system
        files: ^backend/app/semantic/metrics/.*\.py$
      - id: no-duckdb
        name: do not commit generated data
        entry: bash -c 'git diff --cached --name-only | grep -E "\.duckdb$|data/synthetic/" && exit 1 || exit 0'
        language: system
```

---

## C. Application lifecycle hooks (code inside the app — already implied by the plans)

These are "hooks" in the framework sense; the module plans specify them as code. Spec to build:

**Backend (FastAPI):**
- **Lifespan startup hook** — bootstrap DuckDB, run `generator.py` seed into the raw zone, build
  conformed/marts, start the **APScheduler** cadence jobs (daily/nightly/weekly/monthly/on-change
  per §6.2). Shutdown hook — flush/close. *(Shared doc §3 `platform/scheduler.py`; NFR-02/12.)*
- **Audit middleware hook** — on every restricted-metric read, target/threshold change and export,
  write to `audit_log`. *(NFR-07, AC-03.)*
- **RLS dependency hook** — FastAPI dependency injecting the role-scope filter from `semantic/rls.py`
  into every query. *(§9, NFR-05.)*
- **`require_role` route hook** — gate restricted endpoints (PUR-06, CAP-03) and admin routes. *(AC-03.)*
- **ELT run-log hook** — wrap each ELT job to log success/failure + alert on failure within 30 min.
  *(NFR-12.)*

**Frontend (React):**
- **`use<Module>Data` TanStack Query hooks** — one per module; `queryKey` includes the active
  filters (`state/filters.ts`) and role (`state/role.ts`) so widgets refetch on change. *(FR-GEN-02.)*
- **`useFilters` / `useRole` hooks** — read/update the Zustand stores. *(§10.1, §9.)*
- **`useMetricMeta` hook** — fetch `/reference/metrics` for the `MetricInfoPopover`. *(FR-GEN-07.)*
- **`useFreshness` hook** — poll `/health`, drive the staleness banner. *(FR-GEN-09, NFR-02.)*

---

## Recommended minimal starting set (when you decide to enable)
1. **git pre-commit:** ruff + black + eslint + prettier + the `no-duckdb` and `metric-id` checks
   (durable, team-wide, highest value for least risk).
2. **Claude Code PostToolUse** lint/format + **Stop** `pytest -q` (fast feedback while building with
   Claude Code).
3. **App lifecycle:** the FastAPI lifespan + RLS dependency + audit middleware (these are core
   architecture, not optional).
4. Defer: the `dataviz`/metric-ID *blocking* PreToolUse hooks until the team is comfortable with
   hard blocks — start them as warnings.

## Requirement coverage map
- NFR-11 maintainability → A (lint/format), B (pre-commit/CI)
- NFR-02/12 freshness/observability → C (scheduler, ELT run-log, `useFreshness`)
- NFR-05 / §9 / AC-03 RLS & restricted → C (RLS dependency, `require_role`, audit)
- NFR-07 audit → C (audit middleware), B (no-secrets)
- NFR-08 / AC-07 accessibility → CI axe-core (B)
- AC-01/02/04 reconciliation/UAT/load → A (Stop pytest), B (pre-push), CI
- FR-GEN-07 traceability → A + B (metric-ID checks)
- Skills catalog (dataviz-first) → A (PreToolUse reminder)
- Reusable-components skill (extend, don't fork) → A (PreToolUse reminder)
- Bento module pattern (leadership UI, `BentoRow` for sticky spotlights) → A (SessionStart + PreToolUse reminder on `src/routes/`)
- Doc/code threshold drift (e.g. EXE-10 $2M / 60 / 90 days in the plans vs `ref_threshold` /
  `definitions.py`) → optional advisory check in A (PostToolUse on `*.md` or `definitions.py` edits)

> §A is active (see Status above). To change Claude Code hooks, edit `.claude/hooks/gtm_hooks.py` or
> use the `update-config` skill for `.claude/settings.json`. Git hooks (§B) need Git installed, then
> add the config and run `pre-commit install` (or set up husky).
