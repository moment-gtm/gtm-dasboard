# Moment GTM Dashboard — Administration & Governance Module (9th): Prototype Implementation Plan

> Companion to the Shared doc for stack, architecture, project structure, global UI/governance and
> roles. · RSD §4.10 (Alerts), §4.11 (Administration), §6.6 (DQ), §10.2 (Governance).

## 1. Context & scope
The Administration module is the control plane for the whole dashboard: targets, goals/thresholds,
reference data, the data-quality console, alerts, and the governance/change-control process. It is
the 9th module and underpins every metric's correctness and the go-live gate (AC-05). Scope =
FR-ADM-01..04 + FR-ALR-01..03 + DQ-01..09 + §10.2 governance.

## 2. Functional requirements

| Requirement | Capability | Widget / screen | Endpoint |
|---|---|---|---|
| FR-ADM-01 targets load/version (audit trail) | Target CRUD + versions | TargetManager | `POST/GET /api/admin/targets` |
| FR-ADM-02 goals/thresholds/buckets/bands/stage prob | Reference config | ThresholdManager | `GET/PUT /api/admin/thresholds` |
| FR-ADM-03 reference data (catalogue, taxonomy, verticals, platforms, accounts, roster) | Reference CRUD | ReferenceDataManager | `GET/PUT /api/admin/reference/{set}` |
| FR-ADM-04 data quality console | DQ findings by owner + export | DqConsole | `GET /api/admin/dq` |
| FR-ALR-01 weekly digest (email/Teams) | KPI changes, newly stalled, over-capacity | DigestConfig | `POST /api/alerts/digest` |
| FR-ALR-02 threshold alerts | coverage drop; ≥$5M slip; unvalidated AI-led in Propose | AlertRules | `GET/POST /api/alerts/rules` |
| FR-ALR-03 subscriptions | user-managed | AlertSubscriptions | `GET/PUT /api/alerts/subscriptions` |

Priorities: FR-ADM-01/02/03/04 **Must**; FR-ALR-01/02 **Should**; FR-ALR-03 **Could**. Go-live gate
(DQ): ≥95% mandatory-field completeness for qualified opportunities over two consecutive weeks (AC-05).

## 3. External APIs & MCP servers (data retrieval)

| RSD source | Feeds | Real integration | MCP available? | Prototype stand-in |
|---|---|---|---|---|
| SRC-02 Planning | FR-ADM-01 targets (interim) | Governed Excel on SharePoint via **Microsoft Graph**, or Anaplan/SAP BPC API | **Microsoft 365 MCP** (SharePoint) | `raw_planning_target` |
| SRC-16 Entra ID | roles/RLS, subscriptions | **Microsoft Graph** / SCIM | **Microsoft 365 MCP** | `raw_identity_*` |
| Reference Lists | FR-ADM-03 catalogue/taxonomy | SharePoint Lists via **Microsoft Graph** | **Microsoft 365 MCP** | `ref_*` tables |
| All sources | FR-ADM-04 DQ | the raw/conformed zones of every module | — | `dq_finding` |
| Teams/Email | FR-ALR-01 digest | **Microsoft Graph** (Teams/Outlook) | **Microsoft 365 MCP** | logged/mock sender |

MCP note: **Microsoft 365 MCP** is the primary integration for this module — Entra identity,
SharePoint reference/targets, and Teams/Outlook delivery for the weekly digest.

## 4. Data-store & extract schema (module-specific)
- `fact_target` + `target_version` (versioned, audit trail; FR-ADM-01).
- `ref_threshold`, `ref_bucket`, `ref_size_band`, `ref_stage_probability` (FR-ADM-02) — all
  version-controlled (NFR-11).
- `ref_offering`, `ref_practice`, `ref_vertical`, `ref_platform`, `ref_strategic_account`,
  `ref_architect_roster` (FR-ADM-03).
- `dq_finding` (rule ID DQ-01..09, record, owner, status) feeding the console; `completeness_metric`
  (go-live gate).
- `audit_log` (NFR-07: target/threshold/reference changes, restricted-metric access, exports —
  retained 12 months); `alert_rule`, `alert_subscription`, `digest_run`.
- `ref_metric_definition` (metric registry → FR-GEN-07) edited here under change control.

## 5. Roles / personas with access (RSD §9)

| Role | Administration access |
|---|---|
| Sales Operations (administrator) | **Yes** — targets, thresholds, reference data, DQ console (data steward) |
| GTM Lead | Yes (+ assesses metric changes) |
| Moment leadership, Finance, Practice lead, Client partner, Solutions, Alliance, Marketing | **No** (consumers only) |

All admin writes require the admin role and are logged to `audit_log`.

## 6. UI requirements (module-specific; global rules in Shared doc §6)
- Target manager: edit by quarter/practice/vertical(/account); version list with who/when; every
  change confirmed and audited.
- Threshold manager: edit goals and On track/Watch/Off track bands (Appendix B) without code change
  (FR-GEN-05); changes take effect in the semantic layer.
- DQ console: findings grouped by owner, filterable, exportable; shows completeness vs 95% gate.
- Alert rules/subscriptions screens; digest preview. All screens keyboard accessible (NFR-08).

## 7. Governance & change control (RSD §10.2)
- Every metric has a named owner (RSD §5); add/change requests are **logged, assessed by GTM Lead +
  Sales Ops, released in a monthly change window**. The module provides the request log + approval
  workflow and writes the metric registry.
- Goals/thresholds reviewed at FY start and after any re-plan.
- Sales Ops runs a weekly DQ review via the console. This is the home of the governance
  requirements referenced across all 9 module plans.

## 8. Project structure additions
- Backend: `api/routes/admin.py`, `api/routes/alerts.py`, `schemas/admin.py`; `platform/` holds the
  versioned reference tables; API middleware writes `audit_log`; `semantic/status.py` reads
  thresholds from `ref_threshold` so admin edits are live.
- Frontend: `routes/Admin.tsx`; `components/widgets/admin/` (TargetManager, ThresholdManager,
  ReferenceDataManager, DqConsole, AlertRules, AlertSubscriptions, DigestConfig);
  `hooks/useAdminData.ts`; `state/role.ts` gates the route to admins.

## 9. Task splitup
1. Versioned `fact_target`/`target_version` + audit trail; threshold/reference tables editable.
2. DQ engine implementing DQ-01..09 over the raw/conformed zones → `dq_finding`; completeness metric.
   Built as a shared cross-cutting capability via the `moment-gtm-reusable-components` skill.
3. Admin APIs (targets, thresholds, reference, DQ) with `require_role` gating; reuse the `audit`
   middleware from the Step 0 API foundation (extend its events, don't re-implement).
4. Alerts: rule evaluation (coverage drop, ≥$5M slip, unvalidated AI-led in Propose), weekly digest
   builder (prototype: render + log/mock Teams/email send), subscriptions. Shared capability
   (skill): alerts read metrics from `semantic/metrics/*` and are RLS-gated via `semantic/rls.py`.
   Built in roadmap Step 7, after the metrics it consumes exist.
5. Frontend admin screens (compose shared `DataRegister`, `StatusBadge`, Radix dialogs per the skill);
   wire threshold edits to live status recomputation.
6. Tests: `test_admin.py` (versioning, audit), `test_dq.py` (each DQ rule), `test_alerts.py`
   (rule firing); role test that only admins can write (AC-03); accessibility pass (AC-07).

## 10. Verification
- Editing a threshold changes a metric's status without redeploy (reads `ref_threshold`).
- Target versioning keeps history; every write appears in `audit_log` (NFR-07).
- DQ console lists seeded rule violations by owner and reports completeness vs the 95% gate (AC-05).
- Alert rules fire on seeded trigger conditions; digest renders with dashboard links (FR-ALR-01/02).
- Non-admin roles cannot reach admin endpoints (AC-03).
