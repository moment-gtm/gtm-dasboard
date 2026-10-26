-- RAW zone: one table per source object, landed as extracted (Shared doc §4).
-- Column names are normalised to snake_case; values are untouched (original currency etc.).

CREATE TABLE raw_crm_account (
    account_id VARCHAR, name VARCHAR, industry VARCHAR, billing_region VARCHAR,
    strategic BOOLEAN, client_partner_upn VARCHAR, extract_date DATE
);
CREATE TABLE raw_crm_opportunity (
    opportunity_id VARCHAR, name VARCHAR, account_id VARCHAR, stage VARCHAR,
    amount DOUBLE, currency VARCHAR, rep_probability_pct INTEGER,
    created_date DATE, close_date DATE, is_closed BOOLEAN, is_won BOOLEAN,
    offering VARCHAR, lead_practice VARCHAR, primary_platform VARCHAR, lead_source VARCHAR,
    ai_led BOOLEAN, validation_id VARCHAR, partner VARCHAR, partner_role VARCHAR,
    campaign_id VARCHAR, workshop_originated BOOLEAN, owner_upn VARCHAR, loss_reason VARCHAR,
    extract_date DATE
);
CREATE TABLE raw_crm_opportunity_history (
    opportunity_id VARCHAR, stage VARCHAR, entered_date DATE, seq INTEGER, extract_date DATE
);
CREATE TABLE raw_crm_opportunity_line_item (
    line_item_id VARCHAR, opportunity_id VARCHAR, practice VARCHAR, amount DOUBLE,
    currency VARCHAR, extract_date DATE
);
CREATE TABLE raw_crm_user (upn VARCHAR, name VARCHAR, title VARCHAR, extract_date DATE);

CREATE TABLE raw_planning_target (
    target_version VARCHAR, fiscal_year INTEGER, quarter INTEGER, practice VARCHAR,
    amount_usd DOUBLE, loaded_at TIMESTAMP, extract_date DATE
);

CREATE TABLE raw_bid_pursuit (
    pursuit_id VARCHAR, opportunity_id VARCHAR, rfp_received DATE, rfp_submitted DATE,
    decision VARCHAR, sla_target_days INTEGER, orals_reached BOOLEAN, gate_score INTEGER,
    extract_date DATE
);

CREATE TABLE raw_finance_contract (
    contract_id VARCHAR, crm_opportunity_id VARCHAR, booked_month VARCHAR, amount_usd DOUBLE,
    extract_month VARCHAR
);

CREATE TABLE raw_identity_user (
    user_id VARCHAR, upn VARCHAR, display_name VARCHAR, job_title VARCHAR, extract_date DATE
);
CREATE TABLE raw_identity_group (
    group_id VARCHAR, display_name VARCHAR, role VARCHAR, scope_value VARCHAR, extract_date DATE
);
CREATE TABLE raw_identity_group_membership (group_id VARCHAR, user_id VARCHAR, extract_date DATE);

CREATE TABLE raw_ref_offering (
    offering_id VARCHAR, name VARCHAR, family VARCHAR, extract_date DATE
);

-- Step 5 sources: Offerings (SRC-12/13/17 + SRC-03/02 additions), Accounts (SRC-14, SRC-04), Partners (SRC-08/09).
CREATE TABLE raw_validation_record (
    validation_id VARCHAR, opportunity_id VARCHAR, status VARCHAR, reviewed_on DATE, extract_date DATE
);
CREATE TABLE raw_kb_asset (
    asset_id VARCHAR, title VARCHAR, asset_type VARCHAR, offering VARCHAR, practice VARCHAR,
    platform VARCHAR, vertical VARCHAR, last_refreshed DATE, extract_date DATE
);
CREATE TABLE raw_asset_build (
    build_id VARCHAR, asset_id VARCHAR, asset_type VARCHAR, name VARCHAR, practice VARCHAR,
    platform VARCHAR, vertical VARCHAR, status VARCHAR, target_quarter VARCHAR,
    start_date DATE, released_date DATE, extract_date DATE
);
CREATE TABLE raw_bid_proposal_asset (
    pursuit_id VARCHAR, opportunity_id VARCHAR, asset_id VARCHAR, used_on DATE, extract_date DATE
);
CREATE TABLE raw_build_plan (
    fiscal_year INTEGER, quarter INTEGER, planned_releases INTEGER, extract_date DATE
);
CREATE TABLE raw_account_plan (
    account_id VARCHAR, plan_status VARCHAR, last_review_date DATE, whitespace_targets INTEGER,
    extract_date DATE
);
CREATE TABLE raw_booking_history (
    account_id VARCHAR, booked_month VARCHAR, amount_usd DOUBLE, extract_month VARCHAR
);
CREATE TABLE raw_partner_deal_registration (
    registration_id VARCHAR, opportunity_id VARCHAR, partner VARCHAR, co_sell BOOLEAN,
    registered_on DATE, extract_date DATE
);
CREATE TABLE raw_partner_certification (
    partner VARCHAR, certification VARCHAR, holder VARCHAR, certified_on DATE, expires_on DATE,
    extract_date DATE
);
CREATE TABLE raw_partner_tier (
    partner VARCHAR, tier VARCHAR, required_certifications INTEGER, extract_date DATE
);
CREATE TABLE raw_lms_learning_record (
    learner VARCHAR, partner VARCHAR, course VARCHAR, status VARCHAR, updated_on DATE, extract_date DATE
);

-- Step 6 sources: Solutions Capacity (SRC-06/07, SRC-04 cost rates, SRC-03 quality, CRM opportunity team) and PUR-06 (SRC-05).
CREATE TABLE raw_resource (resource_id VARCHAR, name VARCHAR, role VARCHAR, extract_date DATE);
CREATE TABLE raw_crm_opportunity_team (
    opportunity_id VARCHAR, resource_id VARCHAR, role VARCHAR, extract_date DATE
);
CREATE TABLE raw_timesheet_entry (
    entry_id VARCHAR, opportunity_id VARCHAR, resource_id VARCHAR, week_start DATE, hours DOUBLE,
    extract_date DATE
);
CREATE TABLE raw_finance_cost_rate (role VARCHAR, rate_usd_hour DOUBLE, extract_month VARCHAR);
CREATE TABLE raw_finance_project_financials (
    opportunity_id VARCHAR, delivery_margin_pct DOUBLE, as_of_month VARCHAR, extract_month VARCHAR
);
CREATE TABLE raw_pricing_version (
    opportunity_id VARCHAR, version VARCHAR, bid_margin_pct DOUBLE, extract_date DATE
);
CREATE TABLE raw_bid_quality_review (
    pursuit_id VARCHAR, opportunity_id VARCHAR, quality_score DOUBLE, reviewed_on DATE, extract_date DATE
);

-- Step 7 sources: Market Signals (SRC-01 workshops, SRC-10 marketing automation, SRC-11 web analytics, SRC-15 analyst relations).
CREATE TABLE raw_crm_workshop (
    workshop_id VARCHAR, workshop_title VARCHAR, account_id VARCHAR, practice VARCHAR,
    platform VARCHAR, vertical VARCHAR, geography VARCHAR, facilitator_upn VARCHAR,
    workshop_date DATE, opportunity_id VARCHAR, opportunity_created_date DATE,
    days_to_opportunity INTEGER, converted_within_90d BOOLEAN, is_qualified BOOLEAN,
    is_won BOOLEAN, extract_date DATE
);
CREATE TABLE raw_mktg_campaign (
    campaign_id VARCHAR, campaign_name VARCHAR, channel VARCHAR, practice VARCHAR,
    platform VARCHAR, start_date DATE, end_date DATE, budget_usd DOUBLE,
    status VARCHAR, extract_date DATE
);
CREATE TABLE raw_mktg_campaign_member (
    member_id VARCHAR, campaign_id VARCHAR, account_id VARCHAR, opportunity_id VARCHAR,
    primary_source BOOLEAN, responded_date DATE, attended BOOLEAN, attributed_tcv_usd DOUBLE,
    extract_date DATE
);
CREATE TABLE raw_web_content_asset (
    asset_id VARCHAR, title VARCHAR, asset_type VARCHAR, practice VARCHAR,
    platform VARCHAR, published_date DATE, published_quarter VARCHAR,
    author_practice VARCHAR, url_slug VARCHAR, extract_date DATE
);
CREATE TABLE raw_web_engagement_metric (
    metric_id VARCHAR, asset_id VARCHAR, period_quarter VARCHAR, downloads INTEGER,
    engaged_visits INTEGER, avg_dwell_seconds INTEGER, social_shares INTEGER,
    extract_date DATE
);
CREATE TABLE raw_analyst_evaluation (
    eval_id VARCHAR, firm VARCHAR, report_series VARCHAR, report_title VARCHAR,
    practice VARCHAR, platform VARCHAR, published_date DATE, current_placement VARCHAR,
    prior_placement VARCHAR, direction VARCHAR, direction_icon VARCHAR, score_delta DOUBLE,
    lead_analyst VARCHAR, summary_note VARCHAR, extract_date DATE
);

