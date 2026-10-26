# Moment GTM Dashboard

> **Executive Go-to-Market Analytics Platform** delivering unified visibility across Pipeline, Pursuits, Offerings, Accounts, Partners, Solutions Capacity, and Market Signals.

---

## Workspace Directory Structure

| Directory / File | Description |
| :--- | :--- |
| **[`backend/`](./backend/)** | FastAPI REST API + DuckDB analytical engine |
| **[`frontend/`](./frontend/)** | React 18 + TypeScript + Vite + Tailwind UI |
| **[`e2e/`](./e2e/)** | Playwright end-to-end integration test suite |
| **[`load/`](./load/)** | k6 performance and load test scripts |
| **[`data/templates/`](./data/templates/)** | Master Excel data templates & sample datasets for leadership inputs |
| **[`scripts/`](./scripts/)** | Standalone automation scripts (e.g. `build_all_modules_excel_template.py`) |
| **[`docs/`](./docs/)** | Architecture, design specifications, requirements, and guides |
| **[`docs/guides/`](./docs/guides/)** | Data input instructions and screen-flow walk-through guide |
| **[`docs/requirements/`](./docs/requirements/)** | RSD v0.9 specification (`.docx`) and architectural summary (`.md`) |
| **[`.claude/`](./.claude/)** | Claude Code automation hooks and reusable component skills |
| **[`CLAUDE.md`](./CLAUDE.md)** | Claude Code project conventions, commands, and architectural rules |

---

## Quick Start

### 1. Build or Edit Master Data Template
```powershell
python scripts/build_all_modules_excel_template.py
```
This generates `data/templates/Moment_GTM_Dashboard_Master_Data_Template.xlsx` with all 15 sheets ready for custom scenario inputs.

### 2. Start the Frontend-Only Synthetic Demo
```bash
cd frontend
npm ci
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)**. Synthetic responses are bundled in
`frontend/src/mocks/data.json`; the demo runs without a backend or database. Browser-local
mock sessions and admin edits are stored in local browser storage.

To connect the optional FastAPI service instead, build with `VITE_DATA_MODE=api` and follow
the backend steps in [DEPLOYMENT.md](./DEPLOYMENT.md).

The synthetic demo is deployed to GitHub Pages at
**https://moment-gtm.github.io/gtm-dasboard/** from the `main` branch.

### 3. Sign In to the Synthetic Demo
Use any listed persona's email and the demo password format
`Moment#2026$FirstName!GTM` (for example, Jordan Avery: `Moment#2026$Jordan!GTM`).
These credentials simulate personas only and do not authenticate real Entra accounts.

## Documentation Index
- **[Data Input & Screen Flow Guide](./docs/guides/Moment_GTM_Dashboard_Data_Input_and_Screen_Flow_Guide.md)**
- **[System Architecture Overview](./docs/architecture/Backend_Architecture_Overview.md)**
- **[Shared Component & Skill Catalog](./docs/claude/Moment_GTM_Dashboard_Reusable_Components_and_Skills.md)**
- **[Implementation Roadmap](./docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md)**
- **[RSD Requirements Specification](./docs/requirements/Moment_GTM_Dashboard_RSD_v0.9_Summary.md)**
