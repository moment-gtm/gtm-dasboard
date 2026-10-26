# Architecture — Moment GTM Dashboard prototype

```
Mock connectors (connectors/mock.py)      Salesforce · Anaplan · SAP · Graph · SharePoint · Marketo/AJO · AEM/CJA · AR Tracker
        │  extract (APScheduler cadence, platform/scheduler.py)
        ▼
RAW zone          raw_crm_* · raw_planning_target · raw_finance_contract · raw_identity_* · raw_ref_offering
                  raw_marketing_campaign · raw_web_content_asset · raw_web_engagement_metric · raw_analyst_evaluation · ...
        ▼  platform/elt/raw_to_conformed.py + schema_conformed.sql
CONFORMED         dim_date · dim_account (industry→vertical) · dim_person · dim_vertical/practice/platform
                  fact_opportunity (USD @ plan FX, std stage probability, days in stage, DQ flags)
                  fact_stage_history · bridge_opportunity_practice · fact_target (latest version)
                  fact_opportunity_snapshot (weekly, SnapshotBuilder) · fact_campaign · fact_workshop ·
                  fact_content_engagement · fact_analyst_eval · ref_* · dq_finding · elt_run_log
        ▼  schema_marts.sql
MARTS             mart_opportunity · mart_opportunity_snapshot · mart_target
        ▼
SEMANTIC LAYER    filters.py (FilterParams, periods) · rls.py (row + detail scope) · targets.py (FR-GEN-04)
                  status.py (ref_threshold bands) · helpers.py (fiscal calendar, plan pace) ·
                  definitions.py (metric registry) · freshness.py · metrics/{exe,pip,pur,off,acc,par,cap,mkt}.py
        ▼
API (FastAPI)     /api/{executive,pipeline,pursuits,offerings,accounts,partners,capacity,market,admin,alerts}/*
                  /api/opportunities · /api/reference/* · /api/health · /api/exports/*
                  require_module / require_role / guard_restricted · audit middleware → audit_log
        ▼
React SPA         AppShell · NavRail · FilterBar · MetricIdsToggle · RoleSwitcher · DataFreshnessIndicator
                  WidgetCard · StatusBadge · MetricInfoPopover · DrilldownPanel · charts/* · DataRegister
                  BentoGrid · SpotlightCard · StatusSpotlight · StatusSummary · ModuleHeadlines (bento leadership layout)
                  widgets/{executive,pipeline,pursuits,offerings,accounts,partners,capacity,market,admin}/*
```

**Store lifecycle.** Each ELT run builds a fresh in-memory DuckDB and swaps it in atomically
(`platform/db.py`), then writes a read-only file copy to `backend/var/gtm_snapshot.duckdb` for the
DuckDB MCP server. A failing source keeps its last good extract (health = failed, data stale) or,
if it never loaded, leaves its tables empty so widgets show their empty/error states.

**Snapshots.** Production captures open opportunities every Monday 00:00 IST (3-year retention).
The prototype backfills by replaying stage history to each Monday since FY25; close date and TCV
use the current record (the mock CRM has no field history for them).

**RLS.** `rls.scope_for(user)` returns two predicates: `row` (feeds aggregates) and `detail` (rows
that may be listed/exported). A practice lead's aggregates cover every practice, but drill-downs
list only their own practice with an `aggregated_other` count/TCV for the rest.

**Targets (FR-GEN-04).** Planning grain is quarter × practice. A finer filter (vertical, platform,
account, …) or a narrowing row scope pro-rates the parent target by the slice's pipeline share
(open + Closed Won TCV closing in the FY) and labels it pro-rated in the payload and UI. The period
target covers the whole period (full FY for FYTD, full quarter for QTD); plan pace is that target
pro-rated to today in calendar days.

**DQ rules applied** (`dq_finding`, console in Step 4): DQ-01 untagged → Untagged bucket in EXE-05;
DQ-02 past-dated open deals → listed in EXE-10; DQ-06 non-USD → plan FX; DQ-07 rep probability →
standard stage probability for weighted metrics (rep value shown in drill-down).

**Next modules** add `semantic/metrics/<mod>.py`, `api/routes/<mod>.py`, `routes/<Module>.tsx` +
`widgets/<mod>/` and any new raw/conformed tables — no rework of the foundation.
