# Moment GTM Dashboard — Requirements Specification (RSD) Summary

> **Summary of:** `Moment_GTM_Dashboard_RSD_v0.9.docx` (project root)
> **Source version:** 0.9.1 (draft for review) · **Date:** 12 October 2026
> **Document ID:** GTM-DASH-RSD-001 · **Classification:** Cognizant Internal

---

## 1. Document overview

This RSD specifies the **business, functional, data and non-functional requirements** for the **Cognizant Moment GTM Dashboard**. It is written to be handed to a development team (internal data/BI engineering or a delivery squad) as the basis for design, build, integration and acceptance testing.

- **Owner:** Balaji Parthasarathy, GTM Lead, Moment (business owner / approver).
- **Status:** Draft, open for stakeholder review before baselining at v1.0.
- **Companion artifact:** `Moment_DX_GTM_Dashboard_Mockup.html` — an interactive mockup with *synthetic/fictional* data that defines layout, interactions and widget behaviour.
- **Metric-ID traceability:** every metric carries a **stable metric ID** (e.g. `EXE-02`, `PIP-01`). The same IDs appear in the mockup when "Show metric IDs and sources" is toggled, so developers, testers and business owners can trace any widget back to its definition, calculation and source.
- **v0.9.1 change:** added metric **OFF-05** (demos, accelerators & solutions developed), requirement **FR-OFF-05**, source **SRC-17**, and related definitions/thresholds.

**Pending sign-offs (TBD):** Head of Moment (sponsor), Sales Operations, Finance, Enterprise IT/Data platform, Information Security, Practice leads.

---

## 2. Business context & objectives

**Problem:** GTM performance data is scattered across CRM, bid-management tools, Finance, partner portals and spreadsheets. Reviews rely on manually assembled decks that are slow to produce, quickly stale, and skewed toward **lagging** measures (bookings) over **leading** indicators (coverage, pipeline ageing, pursuit capacity). Offering/asset investment isn't measured consistently, and AI-led claims aren't tracked against the AI Offering Validation Framework (a governance gap).

**Objectives & success measures:**

| ID | Objective | Success measure |
|----|-----------|-----------------|
| OBJ-01 | Single, trusted view of GTM performance | Weekly review run from the dashboard with no manual deck within 1 quarter of go-live |
| OBJ-02 | Shift attention to leading indicators | Coverage & ageing reviewed weekly; deals stalled >90 days fall 30% within 2 quarters |
| OBJ-03 | Measure offering-led GTM & asset return | ≥95% of qualified opps tagged to an offering / Capability-led; offering-led share reported monthly; assets released at/above plan pace |
| OBJ-04 | Visibility of solutions & pre-sales capacity | No architect over capacity for >2 consecutive weeks |
| OBJ-05 | Govern AI-led positioning | 100% of AI-led opps linked to a validation-register entry |

---

## 3. Scope

**In scope**
- Eight dashboard modules: **Executive summary, Pipeline, Pursuits & wins, Offerings, Accounts, Partners, Solutions capacity, Market signals**.
- **Read-only** integration with source systems via a governed data platform + semantic layer.
- Global filtering, drill-down to opportunity records, export, status thresholds, alerts, and an admin console for targets/thresholds/reference data.
- **Role-based access** with row-level security (RLS) by practice/account; restricted visibility for margin & cost metrics.
- Weekly pipeline snapshots for trend metrics.

**Out of scope**
- Replacing CRM or bid-management tools as systems of record (no write-back).
- Sales compensation / incentive calculations.
- Client-facing reporting.
- Predictive forecasting / ML win-probability scoring (future enhancement, not Phases 1–3).

**Audience:** dev & data engineering, solution/data architects, QA/UAT, Sales Ops, Finance, Enterprise IT, InfoSec, and GTM leadership.

---

## 4. Stakeholders & personas

Nine personas, each with a default view and data scope:

| Persona | Default view | Data scope |
|---------|--------------|------------|
| GTM Lead (business owner) | Executive summary | All, incl. restricted metrics |
| Moment leadership | Executive summary | All, read-only |
| Practice leads | Pipeline (own practice) | Own practice in full; others aggregated |
| Client partners / account leads | Accounts | Assigned accounts |
| Solutions leads & architects | Solutions capacity | All pursuits; no margin/cost |
| Alliance managers | Partners | Partner-tagged opps; certification data |
| Marketing | Market signals | Campaign-/workshop-linked opps |
| Finance business partner | Pursuits & wins | All, incl. margin |
| Sales Operations (admin) | Administration & DQ console | All; admin rights |

---

## 5. Functional requirements (by module)

Priorities use **MoSCoW** (Must / Should / Could). Highlights:

- **Global / cross-module (FR-GEN-01..13):** navigation across 8 modules; persistent global filters (period, vertical, practice, platform) plus additional filters; target comparison (pro-rated when no target at grain); **status as text label + colour (never colour alone)** with admin-configurable thresholds; drill-down to CRM deep links; per-widget metric ID/definition/source/last-refresh; CSV/Excel/PDF export (PPTX of Exec summary = Could); data-freshness indicator + staleness banner; saved filter views (Could); **weekly snapshot capture**; clear empty/error states; mobile/tablet-usable Exec summary.
- **Executive summary (FR-EXE-01..05):** bookings runway (booked + weighted commit/best-case + target + plan pace, with auto narrative); six north-star KPIs with trend sparklines; bookings-by-quarter vs target; open pipeline by vertical (qualified vs Identify); deals-needing-attention list (≥$2M, ageing/stalled).
- **Pipeline (FR-PIP-01..06):** stage funnel + conversion; ageing heatmap (stage × time-in-stage); mix by practice/platform; deal-size distribution; sortable/searchable opportunity register; week-over-week stage movement (needs snapshots).
- **Pursuits & wins (FR-PUR-01..05):** win rate by quarter (count & value, no-bids excluded); loss reasons; source mix & win rate; bid discipline (no-bid rate, pursued-RFP win rate, orals→win); **margin at bid vs delivery (restricted)**.
- **Offerings (FR-OFF-01..05):** pipeline/wins by offering (Capability-led separate); multi-practice attach rate; AI-led validation split (validated / not validated / not AI-led, with unvalidated callout); asset reuse; **demos/accelerators/solutions developed (OFF-05)** — released vs build plan, in-development, reuse share, build time.
- **Accounts (FR-ACC-01..05):** penetration matrix (accounts × 8 practices); whitespace summary; expansion vs new-logo; account-plan status; keyboard-accessible account detail panel.
- **Partners (FR-PAR-01..03):** pipeline by partner (sourced vs influenced); co-sell performance; certification progress vs tier/specialization target.
- **Solutions capacity (FR-CAP-01..04):** active pursuits per architect (healthy/stretched/over-capacity); RFP turnaround & SLA adherence; cost of sale (restricted); pursuit quality scores by outcome.
- **Market signals (FR-MKT-01..04):** thought-leadership output & engagement; workshop funnel; campaign-sourced pipeline; analyst positioning.
- **Alerts (FR-ALR-01..03):** weekly email/Teams digest; threshold alerts (coverage drop, ≥$5M slip, unvalidated AI-led entering Propose); self-managed subscriptions.
- **Administration (FR-ADM-01..04):** load/version targets with audit trail; maintain goals/thresholds/buckets/bands/stage-probability table; maintain reference data (catalogue, taxonomy, verticals, platforms, strategic accounts, architect roster); data quality console.

---

## 6. Metric catalogue

Section 5 is the **authoritative definition** of every metric — the semantic layer must implement these exactly, and any change requires metric-owner approval + a document version bump. All values in **USD at plan rates**; goals/thresholds shown are admin-editable defaults.

| Family | Range | Focus |
|--------|-------|-------|
| EXE | EXE-01 … EXE-10 | Executive KPIs: bookings vs target, coverage, win rate, new pipeline, offering-led share, deal cycle, runway, bookings/quarter, pipeline by vertical, deals needing attention |
| PIP | PIP-01 … PIP-07 | Stage funnel/conversion, ageing, by practice/platform, deal-size, opportunity register, stage movement |
| PUR | PUR-01 … PUR-06 | Win-rate trend, loss reasons, source mix, bid discipline, orals conversion, margin at bid vs delivery (restricted) |
| OFF | OFF-01 … OFF-05 | Pipeline/wins by offering, attach rate, AI-led validation, asset reuse, assets developed |
| ACC | ACC-01 … ACC-04 | Account penetration, whitespace coverage, expansion vs new logo, account-plan health |
| PAR | PAR-01 … PAR-03 | Partner-sourced/influenced pipeline, co-sell performance, certification status |
| CAP | CAP-01 … CAP-04 | Pursuits per architect, RFP turnaround/SLA, cost of sale (restricted), pursuit quality score |
| MKT | MKT-01 … MKT-04 | Thought leadership, workshop conversion, campaign-sourced pipeline, analyst positioning |

**Key definitions:** TCV (primary measure), ACV, bookings, qualified vs weighted pipeline, commit/best-case, plan pace, coverage ratio, offering-led vs capability-led, attach rate, whitespace, demo/accelerator/solution/released asset, partner sourced vs influenced, proactive deal, no-bid, orals, RLS. Fiscal calendar = **Jan–Dec**; FY26 = CY2026.

---

## 7. Source systems & integration

**Principles:** dashboard is **read-only** (no write-back); one system of record per domain (CRM for daily reporting, Finance for monthly reconciliation); all sources load into a governed platform; presentation reads **only** from the semantic layer; incremental loads with a ≥weekly full reconciliation. Product names are indicative — Enterprise IT must confirm each (see OQ-02/03).

**Source inventory (SRC-01 … SRC-17)** with integration phase:
- **SRC-01 CRM** (Salesforce/enterprise CRM) — system of record for pipeline (Phase 1).
- **SRC-02 Planning/targets** (SAP BPC / Anaplan / interim Excel) (Phase 1).
- **SRC-03 Bid & proposal mgmt** (Responsive/Loopio/SharePoint) (Phase 1).
- **SRC-04 Finance ERP** (S/4HANA/Oracle/DW) (Phase 2).
- **SRC-05 Deal pricing tool** (Phase 2) · **SRC-06 Resource mgmt** (Phase 2) · **SRC-07 Timesheets** (Phase 3).
- **SRC-08 Partner portals** (Adobe/Salesforce) (Phase 2) · **SRC-09 LMS** (Phase 2).
- **SRC-10 Marketing automation** (Marketo/SFMC) (Phase 3) · **SRC-11 Web CMS & analytics** (AEM/Adobe Analytics/CJA) (Phase 3).
- **SRC-12 Knowledge repository** (SharePoint/M365) (Phase 2) · **SRC-13 AI validation register** (SharePoint List) (Phase 2).
- **SRC-14 Account planning** (Phase 2) · **SRC-15 Analyst relations tracker** (Phase 3).
- **SRC-16 Identity provider** (Microsoft Entra ID) (Phase 1) · **SRC-17 Asset development tracker** (Workfront/Jira/ADO) (Phase 2).

**Master keys:** **CRM Opportunity ID** is the master key for every deal-level fact — all other systems holding deal data must store it; unmatched records go to a matching queue. Other keys: CRM Account ID, Offering catalogue ID, Practice taxonomy (Strategy, Design, Marketing, Content Ops, DxP, CCM, ECM, Commerce), Entra UPN for people, Partner ID, Knowledge-repo Asset ID, Validation ID.

**CRM field prerequisites (most important dependency):** Sales Ops must implement/enforce before Phase 1 UAT — Offering, lead/participating practices, primary platform, lead-source category, AI-led flag + validation ID, partner & role, solution architect, orals-reached, primary loss reason, no-bid reason.

**Data quality rules (DQ-01 … DQ-09):** handling for untagged opps, past-dated close dates, missing loss reasons, records without a valid CRM Opportunity ID, duplicate/orphan accounts, non-USD amounts, rep vs stage probability, AI-led without validation ID, released build items without Asset ID/type. **Go-live gate:** ≥95% mandatory-field completeness for qualified opportunities across two consecutive weeks.

---

## 8. Data architecture

**Layered reference architecture** (metric logic defined once, reused by every view/export/alert): Sources → Ingestion (connectors/ELT with CDC, retries, alerting) → Data platform (raw / conformed / curated marts + weekly snapshots) → Semantic layer (governed, version-controlled measures with RLS) → Presentation (BI tool or custom web app matching the mockup) → Distribution (email/Teams digest, PDF/Excel export).

- **Platform choice open (OQ-01):** enterprise standard (e.g. Microsoft Fabric / Azure Synapse + Power BI, or Snowflake + Tableau) vs a custom web front end.
- **Core logical entities:** Opportunity, OpportunitySnapshot, StageHistory, OpportunityPractice, Account, Target, Pursuit, Resource, PartnerEngagement, Certification, Asset/AssetUsage, AssetBuild/BuildPlan, ValidationRecord, AccountPlan, ReferenceData.
- **Snapshots/currency/calendar:** snapshot of open opps every **Monday 00:00 IST**, retained 3 years; USD at FY plan exchange rate; fiscal year Jan–Dec; plan-pace elapsed share in calendar days.

---

## 9. Non-functional requirements (NFR-01 … NFR-13)

- **Performance:** module views <3s @ P90 with 50 concurrent users; filter changes <2s.
- **Data freshness:** CRM metrics refreshed by **07:00 IST** each business day; staleness triggers warning banner.
- **Availability:** 99.5% during business hours (07:00–21:00 IST, Mon–Fri).
- **Auth:** SSO via **Microsoft Entra ID**, no local accounts.
- **Authorisation:** role-based + RLS by practice/account enforced in the semantic layer (including exports & alerts).
- **Data protection:** per Cognizant InfoSec/classification policy; no client personal data beyond business contacts; data residency per enterprise policy.
- **Audit:** log restricted-metric access, target/threshold changes, and exports — retained 12 months.
- **Accessibility:** **WCAG 2.1 AA**; status never by colour alone; keyboard-accessible with visible focus.
- **Responsiveness:** Exec summary usable at 390 px; others on tablet.
- **Scalability:** 5 years history / 50,000 opportunities without breaching performance.
- **Maintainability / Observability / Browser support:** version-controlled definitions; pipeline failures alert data team within 30 min; current Edge, Chrome, Safari.

---

## 10. Roles & access

Role matrix governs module visibility, data scope, and access to **restricted metrics (PUR-06 margin, CAP-03 cost of sale)** — only GTM Lead, Moment leadership and Finance business partner see restricted metrics; Sales Ops admin only if granted.

---

## 11. UI & governance

- **UI:** follows the mockup — navigation rail, filter bar, bookings runway as lead Exec element, KPI strip, module panels. Each panel: plain-language title + one-line description + info control (metric ID/definition/source/refresh). Tooltips show exact values; currency in **$M to 1 decimal**. Moment brand palette/typography (mockup palette indicative). Clear empty/error states.
- **Governance & change control:** each metric has a named owner who approves changes; add/change requests logged, assessed by GTM Lead + Sales Ops, released in a **monthly change window**; goals/thresholds reviewed each FY start and after any re-plan; Sales Ops is data steward running a weekly DQ review.

---

## 12. Delivery phasing (indicative)

| Phase | Scope | Sources | Duration |
|-------|-------|---------|----------|
| **Phase 0 — Foundations** | CRM field changes, catalogue/taxonomy agreed, target template, platform decision (OQ-01), access model | n/a | 3–4 wks (can overlap Phase 1) |
| **Phase 1 — MVP** | Exec summary, Pipeline, Pursuits (except PUR-06), global filters, drill-down, admin, DQ console, weekly snapshots | SRC-01, 02, 03, 16 | 8–10 wks |
| **Phase 2 — Portfolio & partners** | Offerings (incl. OFF-05), Accounts, Partners, PUR-06 margin, CAP-01/02, PIP-07 | SRC-04, 05, 06, 08, 09, 12, 13, 14, 17 | 6–8 wks |
| **Phase 3 — Signals & automation** | Market signals, CAP-03/04, alerts/digest, PPTX export | SRC-07, 10, 11, 15 | 6 wks |

---

## 13. Acceptance criteria (AC-01 … AC-07)

- **AC-01:** each in-scope metric reconciles to a direct source query within 0.5% for 3 consecutive cycles; bookings reconcile with Finance at month end.
- **AC-02:** all Must requirements pass UAT scripts derived from this doc + mockup.
- **AC-03:** RLS & restricted-metric access verified per role (incl. exports/alerts).
- **AC-04:** NFR-01 performance met in load test.
- **AC-05:** mandatory-field completeness meets the go-live gate.
- **AC-06:** GTM team runs two consecutive weekly reviews from the dashboard with no manual deck.
- **AC-07:** accessibility review confirms WCAG 2.1 AA.

---

## 14. Assumptions, dependencies & risks

**Assumptions:** CRM is the opportunity system of record (API-accessible); Finance provides targets at ≥quarter/practice grain; enterprise data platform + BI tool available; catalogue/taxonomy owned by GTM.

**Dependencies:** Sales Ops implementing CRM field prerequisites; Enterprise IT approving API access/service accounts/network routes; alliance teams obtaining partner-portal access; AI validation register operational.

**Key risks & mitigations:**
- Incomplete CRM data → mandatory fields, Untagged buckets, DQ console, completeness gate.
- Bid records not linked to CRM IDs → require CRM ID at pursuit creation + matching queue.
- Limited partner-portal APIs → monthly governed export fallback.
- Sensitivity of margin/cost data → restricted roles, aggregation, audit logging, early InfoSec review.
- Metric-definition disagreement → owner sign-off on Section 5 before build.
- Low adoption → embed in weekly cadence, digest, retire parallel reports.

---

## 15. Open questions (OQ-01 … OQ-11)

Must be resolved to baseline v1.0; most are needed by Phase 0:
1. **OQ-01** Presentation platform: enterprise BI tool vs custom web front end.
2. **OQ-02** Which CRM instance is system of record; API availability.
3. **OQ-03** Which bid-management tool; does it store CRM Opportunity ID.
4. **OQ-04** Target grain Finance can provide (practice/vertical/account).
5. **OQ-05** TCV vs ACV as primary bookings measure.
6. **OQ-06** Agreed definition of a proactive deal (Phase 1 design).
7. **OQ-07** Owner/refresh cadence of strategic account list (Phase 2).
8. **OQ-08** Is PUR-06 margin-at-delivery approved given sensitivity (Phase 2).
9. **OQ-09** Standard vs practice/size-varying stage probabilities (Phase 1 design).
10. **OQ-10** Geography/region dimension required at launch (Phase 1 design).
11. **OQ-11** Tool tracking offering-engineering work + build-plan owner (Phase 2).

---

## 16. Appendices

- **Appendix A — Mockup reference:** maps each mockup module to its requirements and metric IDs; most panels calculate live from one generated set of fictional deals. Fixed-sample panels: OFF-04, account plan status, PAR-03, and MKT-01/02/04. Not shown in mockup: PIP-07 stage movement, alerts, admin screens, DQ console, export.
- **Appendix B — Default goals & thresholds:** On track / Watch / Off track bands for key metrics, e.g. Bookings vs pace (≥97% / 85–97% / <85%), Coverage (≥3.0x / 2.5–3.0x / <2.5x), Win rate (≥40% / 32–40% / <32%), Offering-led share (≥60%), Attach rate (≥55%), Assets released vs plan (≥90%), Pursuits per architect (≤3 / 4 / ≥5), Cost of sale (≤2% / 2–2.5% / >2.5%), Days in stage (≤60 / 61–90 Ageing / >90 Stalled).

---

*Summary generated from the source Word document on 2026-10-14. Metric, requirement and source IDs are preserved to keep this summary traceable to the RSD.*
