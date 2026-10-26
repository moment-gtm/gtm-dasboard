-- CONFORMED zone: keys matched, currency -> USD at plan FX, reference data applied.
-- Runs after raw_* and ref_* tables are loaded. `ref_run_context.as_of_date` is "today".

CREATE TABLE dim_date AS
SELECT
    CAST(d AS DATE) AS date_key,
    year(d) AS fiscal_year,                        -- FY = calendar year (RSD 7.3)
    quarter(d) AS fiscal_quarter,
    printf('%d-Q%d', year(d), quarter(d)) AS quarter_key,
    printf('FY%02d Q%d', year(d) % 100, quarter(d)) AS quarter_label
FROM range(TIMESTAMP '2024-01-01', TIMESTAMP '2028-01-01', INTERVAL 1 DAY) t(d);

CREATE TABLE dim_person AS
SELECT DISTINCT u.upn, u.display_name AS name, u.job_title AS title
FROM raw_identity_user u;

CREATE TABLE dim_account AS
SELECT
    a.account_id, a.name, a.industry,
    coalesce(m.vertical, 'Unmapped') AS vertical,
    a.billing_region AS geography,
    a.strategic, a.client_partner_upn
FROM raw_crm_account a
LEFT JOIN ref_industry_vertical m ON m.industry = a.industry;

CREATE TABLE fact_stage_history AS
SELECT
    opportunity_id, stage, entered_date, seq,
    lead(entered_date) OVER (PARTITION BY opportunity_id ORDER BY seq) AS exited_date
FROM raw_crm_opportunity_history;

CREATE TABLE fact_opportunity AS
WITH cur_stage AS (
    SELECT opportunity_id, max(entered_date) AS stage_entered
    FROM fact_stage_history GROUP BY opportunity_id
)
SELECT
    o.opportunity_id, o.name, o.account_id, a.name AS account_name, a.vertical, a.geography,
    a.client_partner_upn, a.strategic,
    o.stage,
    CASE WHEN NOT o.is_closed THEN 'open'
         WHEN o.is_won THEN 'won'
         WHEN o.stage = 'Closed Lost' THEN 'lost'
         WHEN o.stage = 'No Bid' THEN 'no_bid'
         ELSE 'cancelled' END AS stage_group,
    round(o.amount * fx.rate_to_usd, 2) AS tcv_usd,          -- DQ-06 plan FX
    o.currency AS original_currency, o.amount AS original_amount,
    sp.probability AS std_probability,                        -- DQ-07 standard table
    o.rep_probability_pct / 100.0 AS rep_probability,
    CASE WHEN NOT o.is_closed THEN round(o.amount * fx.rate_to_usd * sp.probability, 2)
         ELSE 0 END AS weighted_tcv,
    o.created_date, o.close_date,
    cd.quarter_key AS created_quarter, xd.quarter_key AS close_quarter,
    o.offering,
    CASE WHEN o.offering IS NULL OR o.offering = '' THEN 'Untagged'       -- DQ-01
         WHEN o.offering = 'Capability-led' THEN 'Capability-led'
         ELSE 'Offering-led' END AS offering_class,
    o.lead_practice, o.primary_platform, o.lead_source,
    o.partner, o.partner_role, o.campaign_id, o.workshop_originated,
    o.ai_led, o.validation_id, o.loss_reason,
    o.owner_upn, coalesce(p.name, o.owner_upn) AS owner_name,
    cs.stage_entered AS stage_entered_date,
    CASE WHEN NOT o.is_closed THEN date_diff('day', cs.stage_entered, ctx.as_of_date) END
        AS days_in_stage,
    (NOT o.is_closed AND o.close_date < ctx.as_of_date) AS past_dated   -- DQ-02
FROM raw_crm_opportunity o
JOIN dim_account a USING (account_id)
JOIN ref_fx_rate fx ON fx.currency = o.currency
JOIN ref_stage_probability sp ON sp.stage = o.stage
LEFT JOIN cur_stage cs USING (opportunity_id)
LEFT JOIN dim_person p ON p.upn = o.owner_upn
JOIN dim_date cd ON cd.date_key = o.created_date
JOIN dim_date xd ON xd.date_key = o.close_date
CROSS JOIN ref_run_context ctx;

-- Bid-tool pursuits matched to CRM on the opportunity master key; unmatched rows stay raw (DQ-04).
CREATE TABLE fact_pursuit AS
SELECT b.pursuit_id, b.opportunity_id, b.rfp_received, b.rfp_submitted, b.decision,
       b.sla_target_days, b.orals_reached, b.gate_score,
       CASE WHEN b.rfp_submitted IS NULL THEN NULL
            ELSE b.rfp_submitted <= b.rfp_received + b.sla_target_days END AS submitted_on_time
FROM raw_bid_pursuit b
JOIN raw_crm_opportunity o USING (opportunity_id);

CREATE TABLE bridge_opportunity_practice AS
SELECT li.opportunity_id, li.practice, round(li.amount * fx.rate_to_usd, 2) AS amount_usd,
       li.practice = o.lead_practice AS is_lead
FROM raw_crm_opportunity_line_item li
JOIN raw_crm_opportunity o USING (opportunity_id)
JOIN ref_fx_rate fx ON fx.currency = li.currency;

-- Latest planning version per fiscal year (versioned targets, FR-ADM-01).
CREATE TABLE fact_target AS
SELECT t.target_version, t.fiscal_year, t.quarter AS fiscal_quarter,
       printf('%d-Q%d', t.fiscal_year, t.quarter) AS quarter_key, t.practice, t.amount_usd
FROM raw_planning_target t
WHERE t.target_version = (
    SELECT arg_max(t2.target_version, t2.loaded_at) FROM raw_planning_target t2
    WHERE t2.fiscal_year = t.fiscal_year
);

CREATE TABLE ref_offering AS
SELECT offering_id, name, family FROM raw_ref_offering;

-- Step 5: Offerings, Accounts and Partners facts. Opportunity-keyed rows match CRM on the master key.
CREATE TABLE fact_validation AS
SELECT v.validation_id, v.opportunity_id, v.status, v.reviewed_on
FROM raw_validation_record v
JOIN raw_crm_opportunity o USING (opportunity_id);

CREATE TABLE fact_asset AS
SELECT asset_id, title, asset_type, offering, practice, platform, vertical, last_refreshed
FROM raw_kb_asset;

CREATE TABLE fact_asset_usage AS
SELECT a.pursuit_id, a.opportunity_id, a.asset_id, a.used_on
FROM raw_bid_proposal_asset a
JOIN raw_crm_opportunity o USING (opportunity_id);

-- Build items missing Asset ID or type are kept but flagged; released counts exclude them (DQ-09).
CREATE TABLE fact_asset_build AS
SELECT build_id, asset_id, asset_type, name, practice, platform, vertical, status, target_quarter,
       start_date, released_date,
       (asset_id IS NOT NULL AND asset_type IS NOT NULL) AS complete,
       CASE WHEN status = 'Released' AND start_date IS NOT NULL AND released_date IS NOT NULL
            THEN date_diff('day', start_date, released_date) / 7.0 END AS build_weeks
FROM raw_asset_build;

CREATE TABLE dim_build_plan AS
SELECT fiscal_year, quarter AS fiscal_quarter, printf('%d-Q%d', fiscal_year, quarter) AS quarter_key,
       planned_releases
FROM raw_build_plan;

CREATE TABLE dim_account_plan AS
SELECT p.account_id, p.plan_status, p.last_review_date, p.whitespace_targets
FROM raw_account_plan p
JOIN dim_account a USING (account_id);

CREATE TABLE fact_account_booking_history AS
SELECT h.account_id, CAST(h.booked_month || '-01' AS DATE) AS booked_on, h.amount_usd
FROM raw_booking_history h
JOIN dim_account a USING (account_id);

CREATE TABLE fact_partner_engagement AS
SELECT o.opportunity_id, o.partner, coalesce(o.partner_role, 'Influenced') AS partner_role,
       coalesce(r.co_sell, FALSE) AS co_sell, r.registration_id IS NOT NULL AS registered
FROM raw_crm_opportunity o
LEFT JOIN raw_partner_deal_registration r
       ON r.opportunity_id = o.opportunity_id AND r.partner = o.partner
WHERE o.partner IS NOT NULL AND o.partner <> '';

CREATE TABLE fact_certification AS
SELECT c.partner, c.certification, c.holder, c.certified_on, c.expires_on,
       c.expires_on >= ctx.as_of_date AS active
FROM raw_partner_certification c
CROSS JOIN ref_run_context ctx;

-- Step 6: Solutions Capacity and margin facts. Rows keyed on an opportunity match CRM on the master key.
CREATE TABLE dim_resource AS
SELECT resource_id, name, role FROM raw_resource;

CREATE TABLE fact_opportunity_team AS
SELECT t.opportunity_id, t.resource_id, t.role
FROM raw_crm_opportunity_team t
JOIN raw_crm_opportunity o USING (opportunity_id)
JOIN dim_resource r USING (resource_id);

-- Pursuit effort priced at the finance cost rate of the person's role (CAP-03).
CREATE TABLE fact_pursuit_effort AS
SELECT s.opportunity_id,
       sum(s.hours) AS hours,
       sum(s.hours * c.rate_usd_hour) AS cost_usd
FROM raw_timesheet_entry s
JOIN raw_crm_opportunity o USING (opportunity_id)
JOIN dim_resource r USING (resource_id)
JOIN raw_finance_cost_rate c ON c.role = r.role
GROUP BY s.opportunity_id;

CREATE TABLE fact_bid_quality AS
SELECT q.pursuit_id, q.opportunity_id, q.quality_score, q.reviewed_on
FROM raw_bid_quality_review q
JOIN raw_crm_opportunity o USING (opportunity_id);

-- Margin priced at bid vs margin realised in delivery (PUR-06); delivery is NULL until project financials exist.
CREATE TABLE fact_margin AS
SELECT p.opportunity_id, p.bid_margin_pct / 100.0 AS bid_margin, f.delivery_margin_pct / 100.0 AS delivery_margin
FROM raw_pricing_version p
JOIN raw_crm_opportunity o USING (opportunity_id)
LEFT JOIN raw_finance_project_financials f USING (opportunity_id);

-- Step 7: Market Signals facts and dimensions (MKT-01..04).
CREATE TABLE dim_campaign AS
SELECT campaign_id, campaign_name, channel, practice, platform, start_date, end_date, budget_usd, status
FROM raw_mktg_campaign;

CREATE TABLE fact_campaign_member AS
SELECT m.member_id, m.campaign_id, c.campaign_name, c.channel, m.account_id, m.opportunity_id,
       m.primary_source, m.responded_date, m.attended, m.attributed_tcv_usd
FROM raw_mktg_campaign_member m
JOIN dim_campaign c USING (campaign_id);

CREATE TABLE fact_workshop AS
SELECT w.workshop_id, w.workshop_title, w.account_id, a.name AS account_name,
       w.practice, w.practice AS lead_practice,
       w.platform, w.platform AS primary_platform,
       w.vertical, w.geography, a.client_partner_upn,
       coalesce(f.lead_source, 'Executive / Relationship') AS lead_source,
       f.partner, f.campaign_id, TRUE AS workshop_originated,
       w.facilitator_upn, w.workshop_date, d.quarter_key AS workshop_quarter,
       w.opportunity_id, w.opportunity_created_date, w.days_to_opportunity,
       w.converted_within_90d, w.is_qualified, w.is_won,
       coalesce(f.tcv_usd, 0.0) AS opportunity_tcv_usd
FROM raw_crm_workshop w
JOIN dim_account a USING (account_id)
JOIN dim_date d ON d.date_key = w.workshop_date
LEFT JOIN fact_opportunity f USING (opportunity_id);

CREATE TABLE fact_content_engagement AS
SELECT a.asset_id, a.title, a.asset_type, a.practice, a.platform, a.published_date,
       a.published_quarter, a.author_practice, a.url_slug,
       coalesce(e.downloads, 0) AS downloads,
       coalesce(e.engaged_visits, 0) AS engaged_visits,
       coalesce(e.avg_dwell_seconds, 0) AS avg_dwell_seconds,
       coalesce(e.social_shares, 0) AS social_shares
FROM raw_web_content_asset a
LEFT JOIN raw_web_engagement_metric e USING (asset_id);

CREATE TABLE fact_analyst_eval AS
SELECT eval_id, firm, report_series, report_title, practice, platform, published_date,
       current_placement, prior_placement, direction, direction_icon, score_delta,
       lead_analyst, summary_note
FROM raw_analyst_evaluation;

