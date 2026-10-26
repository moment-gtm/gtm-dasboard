# Moment GTM Dashboard — Full Prototype (Steps 0–8 Complete)

Built per `../docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md`: the shared foundation (Step 0), all **eight analytical modules** plus **Administration & Alerts** (Steps 1–7, 44 registered metrics across `EXE-01..10`, `PIP-01..07`, `PUR-01..06`, `OFF-01..05`, `ACC-01..04`, `PAR-01..03`, `CAP-01..04`, `MKT-01..04`, `ADM-01`, `FR-ALR-01..03`), and full **Step 8 Hardening** (`AC-01..AC-07`).

External source APIs are not available yet, so **all data is synthetic** (seeded, fictional) and
served through **mock connectors** that return each real API's payload shape (Salesforce, Anaplan,
SAP OData, Microsoft Graph). Swapping a mock connector for a real client is the only change needed
to go live — nothing downstream changes.

## Run locally (Windows / PowerShell)

```powershell
# 1. Backend — FastAPI semantic layer on :8000
cd backend
python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
# 2. Frontend — React on :5173 (proxies /api and /mock to :8000)
cd ..\frontend; npm install; npm run dev
```
Open <http://localhost:5173>. API docs: <http://127.0.0.1:8000/docs>.
`docker-compose up` is provided but was not verified (Docker isn't installed on the build machine).

Configuration (env vars, see `backend/app/config.py`): `GTM_DEMO_TODAY` (default `2026-08-14`, mid
FY26 Q3, so plan pace/QTD stay stable), `GTM_SEED`, `GTM_MOCK_FAIL_SOURCES=planning` (simulate a
failed source → error states + staleness banner), `GTM_MOCK_STALE_SOURCES=crm` (simulate staleness).

## Personas (RSD §4 / §9) — switch with the Persona menu (Microsoft Entra ID SSO)

| Persona Name | UPN / Work Email | Role | Entra Security Group | Executive access | Data scope (RLS, `semantic/rls.py`) |
|---|---|---|---|---|---|
| Jordan Avery | `jordan.avery@moment.example` | GTM Lead (business owner) | `GTM-Dashboard-GTMLead` | Yes (+ admin) | All data |
| Sam Okafor | `sam.okafor@moment.example` | Moment leadership | `GTM-Dashboard-Leadership` | Yes | All data (read-only) |
| Lena Kovacs | `lena.kovacs@moment.example` | Finance business partner | `GTM-Dashboard-Finance` | Yes | All data + PUR-06/CAP-03 restricted metrics |
| Ravi Iyer | `ravi.iyer@moment.example` | Practice lead (DxP) | `GTM-Dashboard-PracticeLead-DxP` | Yes | Own practice in full; other practices shown only as aggregates |
| Asha Menon | `asha.menon@moment.example` | Client partner / account lead | `GTM-Dashboard-ClientPartner` | Yes | Assigned accounts only (targets pro-rated, labelled) |
| Noah Berg | `noah.berg@moment.example` | Alliance manager (Adobe) | `GTM-Dashboard-Alliance-Adobe` | Yes | Adobe partner-tagged opportunities |
| Mia Chen | `mia.chen@moment.example` | Field Marketing | `GTM-Dashboard-Marketing` | Yes | Campaign- or workshop-linked opportunities |
| Omar Haddad | `omar.haddad@moment.example` | Sales Operations (admin) | `GTM-Dashboard-SalesOps` | Yes (+ admin) | All data (restricted PUR-06 blocked per RLS) |
| Kai Watanabe | `kai.watanabe@moment.example` | Solutions lead & architect | `GTM-Dashboard-Solutions` | **No** (403 per RSD) | Technical capacity, staffing & SLA performance |
| Balaji Parthasarathy | `balaji.parthasarathy@moment.example` | GTM Lead | `GTM-Dashboard-GTMLead` | Yes (+ admin) | All data |
| Bindya Somaraj | `bindya.somaraj@moment.example` | GTM Lead | `GTM-Dashboard-GTMLead` | Yes (+ admin) | All data |
| Deepak Narayanan | `deepak.narayanan@moment.example` | Moment leadership | `GTM-Dashboard-Leadership` | Yes | All data (read-only) |

Identity is resolved from Microsoft Entra ID token claims and DuckDB extracts (users, groups, memberships -> `raw_identity_*`).
Restricted metrics (PUR-06 and CAP-03) are strictly enforced per RSD RLS rules.

## Mock source APIs (`/mock/*`, same data the ELT loads)

| Real source | Mock endpoint |
|---|---|
| SRC-01 Salesforce | `GET /mock/salesforce/services/data/v60.0/sobjects/{Opportunity\|Account\|OpportunityHistory\|OpportunityLineItem\|User}/records` |
| SRC-02 Anaplan | `GET /mock/anaplan/2/0/workspaces/moment/models/gtm-plan/exports/bookings-target` |
| SRC-04 SAP S/4HANA | `GET /mock/sap/opu/odata/sap/ZGTM_CONTRACT_SRV/Contracts` |
| SRC-10 Adobe Marketo / Journey Optimizer | `GET /mock/adobe/marketo/rest/v1/campaigns.json` |
| SRC-11 Adobe AEM + CJA | `GET /mock/adobe/aem/api/content/thought-leadership.json`, `/mock/adobe/cja/v1/engagement/content` |
| SRC-15 Analyst Relations tracker (SharePoint) | `GET /mock/graph/v1.0/sites/moment/lists/analyst-evaluations/items` |
| SRC-16 Microsoft Graph | `GET /mock/graph/v1.0/users`, `/groups`, `/groups/{id}/members` |
| Offering catalogue (SharePoint) | `GET /mock/graph/v1.0/sites/moment/lists/offering-catalogue/items` |

## Dashboard API (`/api/*`)
`/api/executive/{runway,kpis,bookings-by-quarter,pipeline-by-vertical,deals-attention}` ·
`/api/pipeline/{funnel,ageing,by-practice,by-platform,size-distribution,register,stage-movement}` ·
`/api/pursuits/{win-rate,loss-reasons,source-mix,bid-discipline,orals-conversion}` · `/api/pursuits/margin` (PUR-06, restricted) ·
`/api/capacity/{architect-load,rfp-turnaround,quality-scores}` · `/api/capacity/cost-of-sale` (CAP-03, restricted: GTM Lead, Leadership, Finance; others get 403 and the denial is audited) ·
`/api/offerings/{by-offering,attach-rate,ai-validation,asset-reuse,asset-build}` ·
`/api/accounts/{penetration,whitespace,expansion,plan-health}` · `/api/accounts/{id}/opportunities` ·
`/api/partners/{pipeline,co-sell,certifications}` ·
`/api/market/{thought-leadership,workshop-funnel,campaign-sourced,campaign-pipeline,analyst-positioning}` ·
`/api/alerts/{rules,subscriptions,digest,digest/schedule}` (FR-ALR-01..03: threshold rules, user channel opt-in/out, RLS-scoped weekly digest) ·
`/api/admin/{targets,thresholds,reference,dq,dq/completeness,dq/findings,dq/export,change-requests,audit}`
(GTM Lead + Sales Ops only; edits persist in `var/admin.duckdb` via `GTM_ADMIN_DB`) ·
`/api/opportunities` (drill-down, paging/sort/search, RLS) · `/api/reference/{filters,metrics,thresholds,roles}` ·
`/api/me` · `/api/health` (per-source freshness) · `/api/dq/summary` · `/api/exports/{widget,opportunities}` (CSV/XLSX,
audited) · `POST /api/exports/view` (PDF via print, audited). Global filters on every data endpoint:
`period=fytd|quarter|qtd|custom`, `quarter`, `start`, `end`, `vertical`, `practice`, `platform`, `account`,
`client_partner`, `deal_source`, `geography` (repeat for multi-select). Role: `Authorization: Bearer <token>` (from `/api/auth/entra/login`); the `X-Mock-Role` header is a mock-mode fallback for tests/scripts only (`GTM_ALLOW_MOCK_IDENTITY`, ignored when a valid token is sent).
Header includes a global **"Show metric IDs and sources"** toggle (`MetricIdsToggle` / `state/metricIds.ts`) that shows or hides inline metric ID chips (`EXE-02`, `PIP-01`, …) and source badges (`SRC-01 · SRC-02`, …) across all widgets and KPI cards at once (`FR-GEN-07`), alongside each widget's on-demand `MetricInfoPopover`.

## Tests

| Suite | Command | Covers |
|---|---|---|
| Backend (447 tests) | `cd backend; .\.venv\Scripts\python -m pytest -q` | EXE-01..10, PIP-01..07, PUR-01..06, OFF-01..05, ACC-01..04, PAR-01..03, CAP-01..04, MKT-01..04, ADM-01, FR-ALR-01..03 (incl. digest ↔ `DigestConfig` contract), filters, FR-GEN-04 pro-rating, status bands, **AC-01** reconciliation of all 44 metrics vs raw payload across 3 ELT refresh cycles (incl. SRC-04 Finance month-end and CRM ↔ SRC-10 campaign attribution), **AC-03** role matrix (106 tests across 9 personas × 9 modules/restricted metrics/exports/drill-down/alerts), **AC-05** 50-user concurrency P90 gate, API, audit, source-failure states |
| Frontend unit (12 tests) | `cd frontend; npm test` | format helpers, StatusBadge, global `MetricIdsToggle` (`Show metric IDs and sources`) across `KpiCard` & `WidgetCard`, bento `StatusSummary` scorecard + `StatusSpotlight` ordering/all-clear |
| E2E UAT (124 tests) | `cd e2e; npm install; npx playwright install chromium; npx playwright test` (both servers running) | **AC-02** FR-EXE-01..05, **FR-PIP-01..06** (`pipeline.spec.ts`), **FR-PUR-01..05** (`pursuits.spec.ts`), **FR-OFF-01..05** (`offerings.spec.ts`), **FR-ACC-01..05** (`accounts.spec.ts`), **FR-PAR-01..03** (`partners.spec.ts`), **FR-CAP-01..04 + restricted gating** (`capacity.spec.ts`), **FR-MKT-01..04** (`market_signals.spec.ts`), **FR-ADM-01..04 + FR-ALR-01..03** (`admin.spec.ts`), **cross-module UAT + 390px mobile overflow** (`hardening.spec.ts`), FR-GEN-02/04/05/06/07 (incl. global `"Show metric IDs and sources"` toggle), personas, **AC-07** axe-core WCAG 2.1 AA |
| Load (AC-04/05) | `k6 run load/k6/all_modules.js` (and `load/k6/executive.js`) | 50 VUs across all 8 analytical modules & 9 personas, P90 < 3s views / P90 < 2s filters |
| Screenshots | `cd e2e; node screenshot.mjs <outDir>` | all 9 modules at desktop (1440px) + mobile (390px) |

Lint/format: `ruff check app tests` + `black app tests` (backend), `npm run lint` + `npm run format` (frontend).

## Claude Code tooling for this project
- **Hooks** (`../.claude/settings.json`, logic in `../.claude/hooks/gtm_hooks.py`): SessionStart conventions;
  PreToolUse skill reminders + metric-ID registry check + block on hand-editing `*.duckdb` / `backend/var/`;
  PostToolUse ruff+black / prettier+eslint; Stop runs backend pytest when backend code changed.
  Git pre-commit hooks wait until Git is installed.
- **MCP servers** (`../.mcp.json`): `playwright` (browser UAT) and `gtm-duckdb` (read-only SQL over
  `backend/var/gtm_snapshot.duckdb`, written after each ELT run). Approve them when Claude Code starts.
  The **Microsoft 365** connector (Entra ID, SharePoint targets/catalogue) needs authorising via `/mcp`;
  until then the mock connectors stand in. There is no Salesforce MCP — CRM goes through its REST API.

See `docs/architecture.md` and `docs/metric-mapping.md`.
