# Moment GTM Dashboard — Project Memory & Claude Code Guidelines

## Overview
The **Moment GTM Dashboard** is an executive leadership analytics platform providing real-time visibility across 8 core go-to-market modules:
1. Executive Summary (`EXE-01..10`)
2. Pipeline Management (`PIP-01..07`)
3. Pursuits & Win Rates (`PUR-01..06`)
4. Offerings & Solutions (`OFF-01..05`)
5. Accounts & Relationships (`ACC-01..04`)
6. Partner Alliances (`PAR-01..03`)
7. Solutions Capacity & Presales (`CAP-01..04`)
8. Market Signals & Marketing Events (`MKT-01..04`)

---

## Directory Layout

```
dashboard/
├── .claude/                                  # Claude Code project configuration
│   ├── hooks/                                # Lifecycle automation hooks
│   │   └── gtm_hooks.py                      # SessionStart, PreToolUse, PostToolUse, Stop hooks
│   ├── skills/                               # Reusable domain skills
│   │   └── moment-gtm-reusable-components/   # Component catalog, contracts & rules
│   └── settings.json                         # Hook triggers & permissions
├── backend/                                  # FastAPI + DuckDB analytical engine
│   ├── app/
│   │   ├── api/                              # Thin REST API endpoints
│   │   ├── connectors/                       # Source connectors (mock APIs & Excel reader)
│   │   ├── data/                             # Ingestion engines (excel_loader.py)
│   │   ├── platform/                         # DuckDB schema & ELT runners
│   │   └── semantic/                         # Metrics engine, definitions, & RLS
│   └── tests/                                # Pytest test suite (unit, integration, RLS)
├── frontend/                                 # React 18 + TypeScript + Vite + Tailwind UI
│   └── src/
│       ├── components/                       # Shared UI primitives, bento grids, charts
│       ├── routes/                           # 8 Module leadership views
│       └── theme/                            # Bento theme tokens and styling
├── e2e/                                      # Playwright end-to-end tests
├── load/                                     # k6 performance & load testing
├── data/
│   └── templates/                            # Master data templates & input datasets
│       ├── Moment_GTM_Dashboard_Master_Data_Template.xlsx
│       └── README.md
├── docs/                                     # Architectural & functional documentation
│   ├── architecture/                         # System, frontend, backend & schema designs
│   ├── claude/                               # Hook, MCP & skill reference documentation
│   ├── guides/                               # Operational guides (Data input & screen flows)
│   ├── plans/                                # Module-by-module prototype implementation plans
│   └── requirements/                         # RSD requirements (.docx) and summaries (.md)
├── scripts/                                  # Standalone utility & automation scripts
│   ├── build_all_modules_excel_template.py   # Generates data/templates master Excel file
│   └── README.md
├── docker-compose.yml                        # Docker multi-container service orchestration
├── .gitignore
├── .mcp.json
├── CLAUDE.md                                 # Claude Code context and conventions (this file)
└── README.md                                 # Project overview and index
```

---

## Essential Commands

### Backend (Python 3.11+)
From `backend/`:
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run tests
pytest tests -q

# Run development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Rebuild ELT database from Excel / Mock connectors
python -c "from app.platform.elt.run import build_platform; build_platform()"
```

### Frontend (Node.js 18+)
From `frontend/`:
```powershell
npm run dev        # Launch Vite development server (http://localhost:3000)
npm run build      # Production TypeScript compile & Vite bundle
npm run lint       # Run ESLint checks
npm test           # Run Vitest unit tests
```

### Data Template Generation
From project root:
```powershell
python scripts/build_all_modules_excel_template.py
```

---

## Architecture & Code Conventions

### 1. Backend & Data Architecture
- **ELT Layers:** Connectors -> DuckDB RAW (`raw_*`) -> CONFORMED (`fact_*`, `dim_*`) -> MARTS (`mart_*`) -> Semantic Layer (`semantic/`) -> Thin REST routes (`api/`).
- **Metric Definitions:** Every metric ID (`EXE-01`, `PIP-02`, etc.) MUST be registered in `backend/app/semantic/definitions.py` (enforces `FR-GEN-07`).
- **Authentication & Identity (NFR-04/05):** Pluggable Microsoft Entra ID (`mock_entra` default, `entra` for live Azure AD). Tokens issue standard Entra claims (`oid`, `sub`, `upn`, `name`, `email`, `roles`, `groups`). RLS resolves identity via Bearer token UPN claims (`auth_identifier`) with `X-Mock-Role` fallback for tests. Supports 12 certified Entra personas including `balaji.parthasarathy@moment.example` (GTM Lead), `bindya.somaraj@moment.example` (GTM Lead), and `deepak.narayanan@moment.example` (Moment Leadership); legacy bare usernames (`balaji`, `deepak`, `bindya`) are rejected.
  - **One persona per login:** login requires a password; the UI shows the persona read-only (PersonaBadge). Demo-only escape hatches, all off/restricted by default: GTM_ALLOW_PASSWORDLESS_LOGIN, GTM_ENABLE_PERSONA_SWITCHER (+ frontend VITE_ENABLE_PERSONA_SWITCHER), and GTM_ALLOW_MOCK_IDENTITY (X-Mock-Role / ?role= fallback; mock mode only, a valid Bearer token always wins).
- **Row-Level Security (RLS):** Governed by `backend/app/semantic/rls.py` and applied across all queries, drill-downs, alerts, and exports based on Entra security group memberships.
- **Restricted Access:** Persona and margin-restricted data (such as `PUR-06` and `CAP-03`) use `guard_restricted` and audit trails.
- **Never Hand-Edit Generated Data:** `.duckdb` and `backend/var/` files are ELT-managed; modify generators or Excel source instead.

### 2. Frontend UI Architecture
- **Bento Leadership Theme:** Dashboards utilize `BentoGrid` and `BentoItem` layouts with eyebrow titles and `HeadlineScorecard` summaries.
- **Standard Layout:** 1 `variant="hero"` widget + sticky spotlight row, followed by 6/6 or 4/4/4 modular grid rows.
- **Theme Tokens:** All chrome and surface styling must consume CSS variables from `theme/tokens.ts` (Bento leadership palette).
- **Chart Discipline:** Always consult the `dataviz` skill when updating charts; enforce consistent currency formatting (`$#,##0.0M`).

### 3. Claude Code Integration
- **Skills:** Load `.claude/skills/moment-gtm-reusable-components/SKILL.md` before refactoring shared components, widgets, or semantic queries.
- **Hooks:** Monitored via `.claude/hooks/gtm_hooks.py`:
  - `PreToolUse`: Protects DuckDB databases from manual edits; warns on unregistered metric IDs.
  - `PostToolUse`: Runs code formatters (ruff/black, prettier/eslint).
  - `Stop`: Runs backend pytest checks on modified files.
