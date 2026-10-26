"""Extract from source connectors and land records in the RAW zone.

Field mapping from each source's native shape to raw columns lives here, so a real API
client only has to return the same native payload.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from datetime import date

import duckdb


def _insert(conn: duckdb.DuckDBPyConnection, table: str, rows: list[tuple]) -> int:
    """Bulk-land rows via a temporary NDJSON file (executemany is slow at extract volumes)."""
    if not rows:
        return 0
    schema = conn.execute(f"DESCRIBE {table}").fetchall()
    cols = [c[0] for c in schema]
    fd, path = tempfile.mkstemp(suffix=".ndjson")
    try:
        with os.fdopen(fd, "w", encoding="utf8") as fh:
            for row in rows:
                fh.write(json.dumps(dict(zip(cols, row)), default=str) + "\n")
        columns = "{" + ", ".join(f"'{c}': '{t}'" for c, t, *_ in schema) + "}"
        conn.execute(
            f"INSERT INTO {table} SELECT * FROM read_json(?, format = 'newline_delimited', "
            f"columns = {columns})",
            [path],
        )
    finally:
        os.unlink(path)
    return len(rows)


def load_crm(conn, payload: dict[str, list[dict]], d: date) -> int:
    n = _insert(
        conn,
        "raw_crm_account",
        [
            (
                a["Id"],
                a["Name"],
                a["Industry"],
                a["BillingRegion__c"],
                a["Strategic__c"],
                a["Client_Partner_UPN__c"],
                d,
            )
            for a in payload["Account"]
        ],
    )
    n += _insert(
        conn,
        "raw_crm_opportunity",
        [
            (
                o["Id"],
                o["Name"],
                o["AccountId"],
                o["StageName"],
                o["Amount"],
                o["CurrencyIsoCode"],
                o["Probability"],
                o["CreatedDate"],
                o["CloseDate"],
                o["IsClosed"],
                o["IsWon"],
                o["Offering__c"],
                o["Lead_Practice__c"],
                o["Primary_Platform__c"],
                o["LeadSource"],
                o["AI_Led__c"],
                o["Validation_ID__c"],
                o["Partner__c"],
                o["Partner_Role__c"],
                o["CampaignId"],
                o["Workshop_Originated__c"],
                o["OwnerUPN"],
                o.get("Loss_Reason__c"),
                d,
            )
            for o in payload["Opportunity"]
        ],
    )
    n += _insert(
        conn,
        "raw_crm_opportunity_history",
        [
            (h["OpportunityId"], h["StageName"], h["CreatedDate"], h["Seq"], d)
            for h in payload["OpportunityHistory"]
        ],
    )
    n += _insert(
        conn,
        "raw_crm_opportunity_line_item",
        [
            (li["Id"], li["OpportunityId"], li["Practice__c"], li["TotalPrice"], li["CurrencyIsoCode"], d)
            for li in payload["OpportunityLineItem"]
        ],
    )
    n += _insert(conn, "raw_crm_user", [(u["upn"], u["name"], u["title"], d) for u in payload["User"]])
    n += _insert(
        conn,
        "raw_crm_opportunity_team",
        [(t["Opportunity_Id"], t["Resource_Id"], t["Role"], d) for t in payload.get("OpportunityTeam", [])],
    )
    n += _insert(
        conn,
        "raw_crm_workshop",
        [
            (
                w["Workshop_Id"],
                w["Workshop_Title"],
                w["Account_Id"],
                w["Practice"],
                w["Platform"],
                w["Vertical"],
                w["Geography"],
                w["Facilitator_UPN"],
                w["Workshop_Date"],
                w["Opportunity_Id"],
                w["Opportunity_Created_Date"],
                w["Days_To_Opportunity"],
                w["Converted_Within_90d"],
                w["Is_Qualified"],
                w["Is_Won"],
                d,
            )
            for w in payload.get("Workshop", [])
        ],
    )
    return n


def load_planning(conn, payload: dict[str, list[dict]], d: date) -> int:
    n = _insert(
        conn,
        "raw_planning_target",
        [
            (t["version"], t["fiscal_year"], t["quarter"], t["practice"], t["amount_usd"], t["loaded_at"], d)
            for t in payload["BookingsTarget"]
        ],
    )
    return n + _insert(
        conn,
        "raw_build_plan",
        [(p["fiscal_year"], p["quarter"], p["planned_releases"], d) for p in payload.get("BuildPlan", [])],
    )


def load_finance(conn, payload: dict[str, list[dict]], d: date) -> int:
    month = d.isoformat()[:7]
    n = _insert(
        conn,
        "raw_finance_contract",
        [
            (c["contract_id"], c["crm_opportunity_id"], c["booked_month"], c["amount_usd"], month)
            for c in payload["Contract"]
        ],
    )
    n += _insert(
        conn,
        "raw_booking_history",
        [
            (b["Account_Id"], b["Booked_Month"], b["Amount_USD"], month)
            for b in payload.get("BookingHistory", [])
        ],
    )
    n += _insert(
        conn,
        "raw_finance_cost_rate",
        [(c["Role"], c["Rate_USD_Hour"], month) for c in payload.get("CostRate", [])],
    )
    return n + _insert(
        conn,
        "raw_finance_project_financials",
        [
            (p["Opportunity_Id"], p["Delivery_Margin_Pct"], p["As_Of_Month"], month)
            for p in payload.get("ProjectFinancials", [])
        ],
    )


def load_identity(conn, payload: dict[str, list[dict]], d: date) -> int:
    n = _insert(
        conn,
        "raw_identity_user",
        [(u["id"], u["userPrincipalName"], u["displayName"], u["jobTitle"], d) for u in payload["users"]],
    )
    n += _insert(
        conn,
        "raw_identity_group",
        [(g["id"], g["displayName"], g["role"], g["scope_value"], d) for g in payload["groups"]],
    )
    n += _insert(
        conn, "raw_identity_group_membership", [(m["groupId"], m["userId"], d) for m in payload["members"]]
    )
    return n


def load_catalogue(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_ref_offering",
        [(o["offering_id"], o["name"], o["family"], d) for o in payload["OfferingCatalogue"]],
    )


def load_bid(conn, payload: dict[str, list[dict]], d: date) -> int:
    n = _insert(
        conn,
        "raw_bid_pursuit",
        [
            (
                b["Pursuit_Id"],
                b["CRM_Opportunity_Id"],
                b["RFP_Received"],
                b["RFP_Submitted"],
                b["Decision"],
                b["SLA_Target_Days"],
                b["Orals_Reached"],
                b["Gate_Score"],
                d,
            )
            for b in payload["Pursuit"]
        ],
    )
    return (
        n
        + _insert(
            conn,
            "raw_bid_proposal_asset",
            [
                (a["Pursuit_Id"], a["CRM_Opportunity_Id"], a["Asset_Id"], a["Used_On"], d)
                for a in payload.get("ProposalAsset", [])
            ],
        )
        + _insert(
            conn,
            "raw_bid_quality_review",
            [
                (q["Pursuit_Id"], q["CRM_Opportunity_Id"], q["Quality_Score"], q["Reviewed_On"], d)
                for q in payload.get("QualityReview", [])
            ],
        )
    )


def load_validation(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_validation_record",
        [
            (r["Validation_Id"], r["CRM_Opportunity_Id"], r["Status"], r["Reviewed_On"], d)
            for r in payload["ValidationRecord"]
        ],
    )


def load_kb(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_kb_asset",
        [
            (
                a["Asset_Id"],
                a["Title"],
                a["Asset_Type"],
                a["Offering"],
                a["Practice"],
                a["Platform"],
                a["Vertical"],
                a["Last_Refreshed"],
                d,
            )
            for a in payload["KbAsset"]
        ],
    )


def load_assets(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_asset_build",
        [
            (
                b["Build_Id"],
                b["Asset_Id"],
                b["Asset_Type"],
                b["Name"],
                b["Practice"],
                b["Platform"],
                b["Vertical"],
                b["Status"],
                b["Target_Quarter"],
                b["Start_Date"],
                b["Released_Date"],
                d,
            )
            for b in payload["AssetBuild"]
        ],
    )


def load_account_plan(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_account_plan",
        [
            (p["Account_Id"], p["Plan_Status"], p["Last_Review_Date"], p["Whitespace_Targets"], d)
            for p in payload["AccountPlan"]
        ],
    )


def load_partner(conn, payload: dict[str, list[dict]], d: date) -> int:
    n = _insert(
        conn,
        "raw_partner_deal_registration",
        [
            (r["Registration_Id"], r["CRM_Opportunity_Id"], r["Partner"], r["Co_Sell"], r["Registered_On"], d)
            for r in payload["DealRegistration"]
        ],
    )
    n += _insert(
        conn,
        "raw_partner_certification",
        [
            (c["Partner"], c["Certification"], c["Holder"], c["Certified_On"], c["Expires_On"], d)
            for c in payload["Certification"]
        ],
    )
    return n + _insert(
        conn,
        "raw_partner_tier",
        [(t["Partner"], t["Tier"], t["Required_Certifications"], d) for t in payload["Tier"]],
    )


def load_lms(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_lms_learning_record",
        [
            (r["Learner"], r["Partner"], r["Course"], r["Status"], r["Updated_On"], d)
            for r in payload["LearningRecord"]
        ],
    )


def load_pricing(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_pricing_version",
        [(p["Opportunity_Id"], p["Version"], p["Bid_Margin_Pct"], d) for p in payload["PricingVersion"]],
    )


def load_resource(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn, "raw_resource", [(r["Resource_Id"], r["Name"], r["Role"], d) for r in payload["Resource"]]
    )


def load_timesheet(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_timesheet_entry",
        [
            (t["Entry_Id"], t["Opportunity_Id"], t["Resource_Id"], t["Week_Start"], t["Hours"], d)
            for t in payload["TimesheetEntry"]
        ],
    )


def load_mktg(conn, payload: dict[str, list[dict]], d: date) -> int:
    n = _insert(
        conn,
        "raw_mktg_campaign",
        [
            (
                c["Campaign_Id"],
                c["Campaign_Name"],
                c["Channel"],
                c["Practice"],
                c["Platform"],
                c["Start_Date"],
                c["End_Date"],
                c["Budget_USD"],
                c["Status"],
                d,
            )
            for c in payload["Campaign"]
        ],
    )
    return n + _insert(
        conn,
        "raw_mktg_campaign_member",
        [
            (
                m["Member_Id"],
                m["Campaign_Id"],
                m["Account_Id"],
                m["Opportunity_Id"],
                m["Primary_Source"],
                m["Responded_Date"],
                m["Attended"],
                m["Attributed_TCV_USD"],
                d,
            )
            for m in payload["CampaignMember"]
        ],
    )


def load_web(conn, payload: dict[str, list[dict]], d: date) -> int:
    n = _insert(
        conn,
        "raw_web_content_asset",
        [
            (
                a["Asset_Id"],
                a["Title"],
                a["Asset_Type"],
                a["Practice"],
                a["Platform"],
                a["Published_Date"],
                a["Published_Quarter"],
                a["Author_Practice"],
                a["URL_Slug"],
                d,
            )
            for a in payload["ContentAsset"]
        ],
    )
    return n + _insert(
        conn,
        "raw_web_engagement_metric",
        [
            (
                m["Metric_Id"],
                m["Asset_Id"],
                m["Period_Quarter"],
                m["Downloads"],
                m["Engaged_Visits"],
                m["Avg_Dwell_Seconds"],
                m["Social_Shares"],
                d,
            )
            for m in payload["EngagementMetric"]
        ],
    )


def load_analyst(conn, payload: dict[str, list[dict]], d: date) -> int:
    return _insert(
        conn,
        "raw_analyst_evaluation",
        [
            (
                e["Eval_Id"],
                e["Firm"],
                e["Report_Series"],
                e["Report_Title"],
                e["Practice"],
                e["Platform"],
                e["Published_Date"],
                e["Current_Placement"],
                e["Prior_Placement"],
                e["Direction"],
                e["Direction_Icon"],
                e["Score_Delta"],
                e["Lead_Analyst"],
                e["Summary_Note"],
                d,
            )
            for e in payload["AnalystEvaluation"]
        ],
    )


LOADERS: dict[str, Callable[..., int]] = {
    "pricing": load_pricing,
    "resource": load_resource,
    "timesheet": load_timesheet,
    "bid": load_bid,
    "crm": load_crm,
    "planning": load_planning,
    "finance": load_finance,
    "identity": load_identity,
    "catalogue": load_catalogue,
    "validation": load_validation,
    "kb": load_kb,
    "assets": load_assets,
    "account_plan": load_account_plan,
    "partner": load_partner,
    "lms": load_lms,
    "mktg": load_mktg,
    "web": load_web,
    "analyst": load_analyst,
}
