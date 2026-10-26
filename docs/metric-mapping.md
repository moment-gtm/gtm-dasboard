# Metric Traceability Matrix — All Modules (`FR-GEN-07`)

Every metric in the Moment GTM Dashboard is registered in `backend/app/semantic/definitions.py` (44 metrics across 9 modules) and served by `/api/reference/metrics` to both:
- the global **"Show metric IDs and sources"** header toggle (`MetricIdsToggle` / `state/metricIds.ts`), which reveals inline metric ID chips (`data-testid="metric-id-chip"`) and source badges (`data-testid="metric-sources-chip"`) across all `WidgetCard`s and `KpiCard`s at once, and
- every widget's on-demand info popover (`MetricInfoPopover`).

Status bands (RSD Appendix B) live in `ref_threshold` (`backend/app/data/reference_data.py` seed; editable at runtime via `/api/admin/thresholds`).

## 1. Executive Summary (`FR-EXE-01..05`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `EXE-01` | Bookings vs target | `exe.exe_01` | `/api/executive/kpis` | `NorthStarKpis` (`KpiCard`) | `None` (all booked in period) | `SRC-01`, `SRC-02` | GTM Lead with Finance |
| `EXE-02` | Pipeline coverage | `exe.exe_02` / `coverage_at` | `/api/executive/kpis` | `NorthStarKpis` | `None` (qualified in window) | `SRC-01`, `SRC-02` | Sales Operations |
| `EXE-03` | Win rate | `exe.exe_03` | `/api/executive/kpis` | `NorthStarKpis` | `won`, `lost` | `SRC-01` | GTM Lead |
| `EXE-04` | New pipeline created | `exe.exe_04` | `/api/executive/kpis` | `NorthStarKpis` | `None` (created in period) | `SRC-01`, `SRC-02` | GTM Lead |
| `EXE-05` | Offering-led share | `exe.exe_05` | `/api/executive/kpis` | `NorthStarKpis` | `Offering-led`, `Capability-led`, `Untagged` | `SRC-01`, `REF-OFF` | Offering portfolio lead |
| `EXE-06` | Average deal cycle | `exe.exe_06` | `/api/executive/kpis` | `NorthStarKpis` | `None` (won in period) | `SRC-01` | Sales Operations |
| `EXE-07` | Bookings runway | `exe.exe_07` | `/api/executive/runway` | `BookingsRunway` (`RunwayChart`) | `booked`, `commit`, `best_case` | `SRC-01`, `SRC-02` | GTM Lead |
| `EXE-08` | Bookings by quarter | `exe.exe_08` | `/api/executive/bookings-by-quarter` | `BookingsByQuarter` (`GoalBarChart`) | `<quarter>` (e.g. `2026-Q2`) | `SRC-01`, `SRC-02` | GTM Lead |
| `EXE-09` | Open pipeline by vertical | `exe.exe_09` | `/api/executive/pipeline-by-vertical` | `PipelineByVertical` (`StackedSplitChart`) | `<vertical>\|qualified`, `<vertical>\|identify` | `SRC-01` | Sales Operations |
| `EXE-10` | Deals needing attention | `exe.exe_10` | `/api/executive/deals-attention` | `DealsNeedingAttention` (`DataRegister`) | `Stalled`, `Ageing`, `Past close date` | `SRC-01` | Client partners |

## 2. Pipeline (`FR-PIP-01..06`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `PIP-01` | Stage funnel & conversion | `pip.pip_01` | `/api/pipeline/funnel` | `StageFunnel` (`FunnelChart`) | `<stage>` (`Identify`..`Closed Won`) | `SRC-01` | Sales Operations |
| `PIP-02` | Deal ageing by stage | `pip.pip_02` | `/api/pipeline/ageing` | `StageAgeingMatrix` (`Heatmap`) | `<stage>\|<bucket>` (e.g. `Propose\|61-90`) | `SRC-01` | Sales Operations |
| `PIP-03` | Pipeline by practice | `pip.pip_03` | `/api/pipeline/by-practice` | `PipelineByPractice` (`StackedSplitChart`) | `<practice>[|<stage>]` | `SRC-01` | Practice leads |
| `PIP-04` | Pipeline by platform | `pip.pip_04` | `/api/pipeline/by-platform` | `PipelineByPlatform` (`StackedSplitChart`) | `<platform>\|partner`, `<platform>\|solo` | `SRC-01`, `SRC-08` | Alliance & Platform leads |
| `PIP-05` | Deal size distribution | `pip.pip_05` | `/api/pipeline/size-distribution` | `DealSizeDistribution` | `<band>[|<vertical>]` (e.g. `2.5-5\|BFSI`) | `SRC-01` | Sales Operations |
| `PIP-06` | Opportunity register | `pip.pip_06` | `/api/pipeline/register` | `OpportunityRegister` (`DataRegister`) | `None` (all open deals) | `SRC-01` | Sales Operations |
| `PIP-07` | Week-over-week stage movement | `pip.pip_07` | `/api/pipeline/stage-movement` | `StageMovement` (`MovementBridge`) | `new`, `progressed`, `slipped`, `won`, `lost`, `value_change` | `SRC-01` | Sales Operations |

## 3. Pursuits & Wins (`FR-PUR-01..05`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `PUR-01` | Win rate by dimension | `pur.pur_01` | `/api/pursuits/win-rate` | `WinRateByDimension` | `<dim>\|<key>[|<won\|lost>]` | `SRC-01` | GTM Lead |
| `PUR-02` | Loss reasons breakdown | `pur.pur_02` | `/api/pursuits/loss-reasons` | `LossReasonBreakdown` | `<reason>[|<dim>\|<key>]` | `SRC-01` | Sales Operations |
| `PUR-03` | Proactive vs RFP vs expansion mix | `pur.pur_03` | `/api/pursuits/source-mix` | `ProactiveVsRfpMix` | `<source>[|<open\|won\|lost>]` | `SRC-01` | GTM Lead |
| `PUR-04` | Bid / no-bid discipline | `pur.pur_04` | `/api/pursuits/bid-discipline` | `BidNoBidDiscipline` | `<quarter>\|<pursued\|no_bid\|won\|lost>` | `SRC-01`, `SRC-03` | Bid Desk & Solutions Lead |
| `PUR-05` | Orals conversion rate | `pur.pur_05` | `/api/pursuits/orals-conversion` | `OralsConversion` | `<quarter>[|<won\|lost>]` | `SRC-01`, `SRC-03` | Solutions Lead |
| `PUR-06` | Margin at bid vs delivery (**Restricted**) | `pur.pur_06` | `/api/pursuits/margin` | `MarginAtBidVsDelivery` | `<quarter>`, `<practice>` (GTM Lead / Leadership / Finance only) | `SRC-01`, `SRC-04`, `SRC-05` | Finance Business Partner |

## 4. Offerings (`FR-OFF-01..05`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `OFF-01` | Pipeline & bookings by offering | `off.off_01` | `/api/offerings/by-offering` | `PipelineByOffering` | `<offering>[|<open\|won>]` | `SRC-01`, `REF-OFF` | Offering portfolio lead |
| `OFF-02` | Multi-practice attach rate | `off.off_02` | `/api/offerings/attach-rate` | `CrossPracticeAttach` | `1`, `2`, `3+`, `multi`, `<p1>+<p2>` | `SRC-01` | Practice leads |
| `OFF-03` | AI-led & validation status | `off.off_03` | `/api/offerings/ai-validation` | `AiValidationStatus` | `Validated`, `Pending`, `Unvalidated`, `not_validated` | `SRC-01`, `SRC-13` | AI Validation Board |
| `OFF-04` | Knowledge & accelerator reuse | `off.off_04` | `/api/offerings/asset-reuse` | `AssetReuseTable` | — (asset register) | `SRC-03`, `SRC-12` | Knowledge Management |
| `OFF-05` | Asset build tracker | `off.off_05` | `/api/offerings/asset-build` | `AssetBuildTracker` | — (asset build register) | `SRC-03`, `SRC-17` | Offering portfolio lead |

## 5. Accounts (`FR-ACC-01..05`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `ACC-01` | Account × practice penetration | `acc.acc_01` | `/api/accounts/penetration` | `PenetrationMatrix` (`Heatmap`) | `<account_id>[|<practice>]` (plus `/api/accounts/{id}/opportunities`) | `SRC-01` | Client partners |
| `ACC-02` | Whitespace opportunity | `acc.acc_02` | `/api/accounts/whitespace` | `WhitespaceView` | `<practice>` | `SRC-01` | Client partners |
| `ACC-03` | Expansion vs new-logo bookings | `acc.acc_03` | `/api/accounts/expansion` | `ExpansionVsNewLogo` | `<quarter>[|<expansion\|new_logo>]` | `SRC-01`, `SRC-04` | GTM Lead & Client partners |
| `ACC-04` | Account-plan coverage & currency | `acc.acc_04` | `/api/accounts/plan-health` | `AccountPlanHealth` | — (account plan register) | `SRC-01`, `SRC-14` | Sales Operations |

## 6. Partners (`FR-PAR-01..03`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `PAR-01` | Partner-sourced & co-sell pipeline | `par.par_01` | `/api/partners/pipeline` | `PartnerPipeline` | `<partner>[|<stage\|partner_role>]` | `SRC-01`, `SRC-08` | Alliance managers |
| `PAR-02` | Co-sell win rate vs solo | `par.par_02` | `/api/partners/co-sell` | `CoSellWinRate` | `<partner>\|<co_sell\|solo>`, `Direct\|solo` | `SRC-01`, `SRC-08` | Alliance managers |
| `PAR-03` | Partner certification progress | `par.par_03` | `/api/partners/certifications` | `CertProgress` (`GoalBarChart`) | — (certification tracker) | `SRC-08`, `SRC-09` | Alliance managers |

## 7. Solutions & Capacity (`FR-CAP-01..04`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `CAP-01` | Solution architect workload | `cap.cap_01` | `/api/capacity/architect-load` | `ArchitectWorkload` | `<resource_id>`, `over_capacity` | `SRC-01`, `SRC-06` | Solutions Lead |
| `CAP-02` | RFP response turnaround vs SLA | `cap.cap_02` | `/api/capacity/rfp-turnaround` | `RfpTurnaroundSla` | `<quarter>[|<on_time\|breached>]` | `SRC-01`, `SRC-03` | Bid Desk & Solutions Lead |
| `CAP-03` | Pursuit effort / cost of sale (**Restricted**) | `cap.cap_03` | `/api/capacity/cost-of-sale` | `CostOfSale` | `<quarter>`, `<band>` (GTM Lead / Leadership / Finance only) | `SRC-01`, `SRC-04`, `SRC-06`, `SRC-07` | Finance & Solutions Lead |
| `CAP-04` | Proposal quality review scores | `cap.cap_04` | `/api/capacity/quality-scores` | `ProposalQualityScores` | `<quarter>`, `<practice>`, `won`, `lost` | `SRC-01`, `SRC-03` | Solutions Lead |

## 8. Market Signals (`FR-MKT-01..04`)

| Metric | Name | Semantic function | Endpoint | Widget | Drill segments (`/api/opportunities`) | Sources | Owner |
|---|---|---|---|---|---|---|---|
| `MKT-01` | Thought-leadership output & engagement | `mkt.mkt_01` | `/api/market/thought-leadership` | `ThoughtLeadership` | — (content register) | `SRC-11` | Marketing |
| `MKT-02` | Discovery workshop funnel | `mkt.mkt_02` | `/api/market/workshop-funnel` | `WorkshopFunnel` (`FunnelChart`) | `workshops`, `created`, `qualified`, `won` | `SRC-01` | Solutions Lead & Marketing |
| `MKT-03` | Campaign-sourced pipeline | `mkt.mkt_03` | `/api/market/campaign-sourced` (`/campaign-pipeline`) | `CampaignPipeline` | `<quarter>`, `<campaign_id>` | `SRC-01`, `SRC-10` | Marketing |
| `MKT-04` | Analyst positioning | `mkt.mkt_04` | `/api/market/analyst-positioning` | `AnalystPositioning` | — (analyst evaluation tracker) | `SRC-15` | Analyst Relations |

## 9. Administration & Data Quality (`FR-ADM-01..04`, `DQ-01..09`)

| Metric / Rule | Name | Semantic function / Module | Endpoint | Widget | Sources | Owner |
|---|---|---|---|---|---|---|
| `ADM-01` | Mandatory-field completeness | `adm.adm_01` / `dq.py` | `/api/admin/dq`, `/api/admin/dq/completeness` | `DataQualityConsole` | `SRC-01` | Sales Operations |
| `DQ-01..DQ-09` | Automated data quality rules (completeness, close date, duplicates, orphan accounts, negative TCV, FX, stage prob, AI validation, stale refresh) | `semantic/dq.py` | `/api/admin/dq/findings`, `/api/admin/dq/export` | `DataQualityConsole` | `SRC-01..SRC-17` | Sales Operations |

## 10. Alerts & Weekly Digest (`FR-ALR-01..03`)

| Requirement | Capability | Service / Endpoint | Widget | Underlying metrics |
|---|---|---|---|---|
| `FR-ALR-01` | Weekly digest (Email & Teams, RLS-scoped) | `alerts.build_digest` / `send_digest` · `/api/alerts/digest` | `DigestConfig` | `EXE-01..06`, `EXE-10`, `CAP-01` |
| `FR-ALR-02` | Threshold alert rules (`coverage_drop`, `large_deal_slip`, `unvalidated_ai_propose`) | `alerts.evaluate_rules` · `/api/alerts/rules` | `AlertRules` | `EXE-02`, `EXE-10`, `OFF-03` (+ custom rules) |
| `FR-ALR-03` | User-managed channel subscriptions (Email & Teams) | `alerts.subscriptions_payload` · `/api/alerts/subscriptions` | `AlertSubscriptions` | All alert rules + `weekly_digest` |
