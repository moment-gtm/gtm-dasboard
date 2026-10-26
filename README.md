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

### 2. Start Prototype Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start Prototype Frontend
```powershell
cd frontend
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** to view the dashboard.

### 4. Authenticate & Log In (Microsoft Entra ID SSO)
The application includes an enterprise Microsoft Entra ID login portal (`/login`) compliant with **RSD Requirement NFR-04** (SSO via Entra ID) and **NFR-05** (RLS via Entra Group Membership).

Users authenticate via the **Sign In with Corporate Work Account (UPN)** section by entering their corporate work email / UPN (password is optional in mock mode). The platform maps the following **12 certified Entra personas** to their respective security groups and RLS data scopes:

| Persona Name | Corporate UPN / Email | Role | Entra Security Group | RLS Scope & Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Jordan Avery** | `jordan.avery@moment.example` | **GTM Lead** | `GTM-Dashboard-GTMLead` | Full Enterprise visibility across all 8 modules + Admin Console |
| **Sam Okafor** | `sam.okafor@moment.example` | **Moment Leadership** | `GTM-Dashboard-Leadership` | Executive scorecard, Strategic Pipeline & Offering portfolio |
| **Lena Kovacs** | `lena.kovacs@moment.example` | **Finance** | `GTM-Dashboard-Finance` | Full financial visibility, P&L, PUR-06 Margin & CAP-03 Net Retention |
| **Ravi Iyer** | `ravi.iyer@moment.example` | **Practice Lead** | `GTM-Dashboard-PracticeLead-DxP` | Digital Experience Practice (DxP deals, capacity & targets) |
| **Asha Menon** | `asha.menon@moment.example` | **Client Partner** | `GTM-Dashboard-ClientPartner` | Strategic enterprise accounts & Tier-1 client pursuits |
| **Noah Berg** | `noah.berg@moment.example` | **Alliance Manager** | `GTM-Dashboard-Alliance-Adobe` | Adobe ecosystem, co-sell pipeline & partner-sourced revenue |
| **Mia Chen** | `mia.chen@moment.example` | **Field Marketing** | `GTM-Dashboard-Marketing` | Campaign attribution, executive roundtables & demand gen |
| **Omar Haddad** | `omar.haddad@moment.example` | **Sales Operations** | `GTM-Dashboard-SalesOps` | Pipeline hygiene, Stage 3+ pursuits, quota targets & data audit |
| **Kai Watanabe** | `kai.watanabe@moment.example` | **Solutions Lead** | `GTM-Dashboard-Solutions` | Technical validation, solution staffing, utilization & SLAs |
| **Balaji Parthasarathy** | `balaji.parthasarathy@moment.example` | **GTM Lead** | `GTM-Dashboard-GTMLead` | Full Enterprise visibility across all 8 modules + Admin Console |
| **Bindya Somaraj** | `bindya.somaraj@moment.example` | **GTM Lead** | `GTM-Dashboard-GTMLead` | Full Enterprise visibility across all 8 modules + Admin Console |
| **Deepak Narayanan** | `deepak.narayanan@moment.example` | **Moment Leadership** | `GTM-Dashboard-Leadership` | Executive scorecard, Strategic Pipeline & Offering portfolio |

*(Tip: In Mock Entra mode, sign in using any corporate UPN from the table above, e.g. `jordan.avery@moment.example`. Each login is bound to a single persona (password required; shown read-only in the header). To evaluate another role, sign out and sign in as that persona. In production Azure Entra mode, sign-in redirects to `login.microsoftonline.com` via MSAL.)*

---

## Documentation Index
- **[Data Input & Screen Flow Guide](./docs/guides/Moment_GTM_Dashboard_Data_Input_and_Screen_Flow_Guide.md)**
- **[System Architecture Overview](./docs/architecture/Backend_Architecture_Overview.md)**
- **[Shared Component & Skill Catalog](./docs/claude/Moment_GTM_Dashboard_Reusable_Components_and_Skills.md)**
- **[Implementation Roadmap](./docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md)**
- **[RSD Requirements Specification](./docs/requirements/Moment_GTM_Dashboard_RSD_v0.9_Summary.md)**
