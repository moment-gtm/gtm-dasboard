"""Excel data loader for Moment GTM Dashboard (All Modules).

Loads user-edited data exclusively from Moment_GTM_Dashboard_Master_Data_Template.xlsx
to replace synthetic mock data.
"""

from __future__ import annotations

import os
from pathlib import Path
import openpyxl

def _resolve_master_excel_path() -> Path:
    candidates = [
        # data/templates/ relative to backend/app/data (3 levels up -> dashboard/data/templates/)
        Path(__file__).resolve().parents[3] / "data" / "templates" / "Moment_GTM_Dashboard_Master_Data_Template.xlsx",
        # Explicit workspace dashboard/data/templates/ path
        Path(r"C:\Users\299454\OneDrive - Cognizant\LTIN144644_Backup\Moment-GTM\Workspace\dashboard\data\templates\Moment_GTM_Dashboard_Master_Data_Template.xlsx"),
        # Legacy 4-level relative path (in case nested)
        Path(__file__).resolve().parents[4] / "data" / "templates" / "Moment_GTM_Dashboard_Master_Data_Template.xlsx" if len(Path(__file__).resolve().parents) > 4 else Path("."),
        # Legacy workspace path fallback
        Path(r"C:\Users\299454\OneDrive - Cognizant\LTIN144644_Backup\Moment-GTM\Workspace\Moment_GTM_Dashboard\data\templates\Moment_GTM_Dashboard_Master_Data_Template.xlsx"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


MASTER_EXCEL_PATH = _resolve_master_excel_path()


def _read_sheet_rows(ws) -> list[dict]:
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 4:
        return []
    headers = [str(c).strip() for c in rows[3] if c is not None]
    data = []
    for r in rows[4:]:
        if not any(r):
            continue
        row_dict = {headers[i]: r[i] for i in range(len(headers)) if i < len(r)}
        data.append(row_dict)
    return data


def load_from_excel(excel_path: str | Path | None = None) -> dict[str, list[dict]] | None:
    if os.environ.get("GTM_DISABLE_EXCEL", "").lower() in ("1", "true", "yes"):
        return None

    path = Path(excel_path) if excel_path else _resolve_master_excel_path()

    if not path.exists() or path.stat().st_size == 0:
        return None

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as e:
        print(f"Error loading Excel workbook {path}: {e}")
        return None

    result: dict[str, list[dict]] = {}

    # 1. Accounts
    if "Accounts" in wb.sheetnames:
        acc_raw = _read_sheet_rows(wb["Accounts"])
        acc_list = []
        for row_dict in acc_raw:
            acc_defaults = {
                "Industry": "Banking",
                "BillingRegion__c": "Americas",
                "Strategic__c": False,
                "Client_Partner_UPN__c": "john.doe@cognizant.com",
            }
            for k, v in acc_defaults.items():
                if k not in row_dict or row_dict[k] is None:
                    row_dict[k] = v
            row_dict["Strategic__c"] = bool(row_dict.get("Strategic__c", False))
            acc_list.append(row_dict)
        result["Account"] = acc_list

    # 2. Opportunities
    if "Opportunities" in wb.sheetnames:
        opp_raw = _read_sheet_rows(wb["Opportunities"])
        opp_list = []
        for row_dict in opp_raw:
            stage = str(row_dict.get("StageName", ""))
            row_dict["IsClosed"] = stage in ("Closed Won", "Closed Lost", "No Bid", "Client Cancelled")
            row_dict["IsWon"] = stage == "Closed Won"

            opp_defaults = {
                "CurrencyIsoCode": "USD",
                "Probability": 0.8 if stage == "Negotiate" else (1.0 if stage == "Closed Won" else 0.4),
                "Offering__c": "Pulse Insights",
                "Lead_Practice__c": "DxP",
                "Primary_Platform__c": "Adobe",
                "LeadSource": "Client RFP",
                "AI_Led__c": False,
                "Validation_ID__c": None,
                "Partner__c": None,
                "Partner_Role__c": None,
                "CampaignId": None,
                "Workshop_Originated__c": False,
                "OwnerUPN": "john.doe@cognizant.com",
                "Loss_Reason__c": None,
            }
            for k, v in opp_defaults.items():
                if k not in row_dict or row_dict[k] is None:
                    row_dict[k] = v

            row_dict["AI_Led__c"] = bool(row_dict.get("AI_Led__c", False))
            row_dict["Workshop_Originated__c"] = bool(row_dict.get("Workshop_Originated__c", False))
            opp_list.append(row_dict)
        result["Opportunity"] = opp_list

    # 3. Opportunity Line Items
    if "Opportunity_Line_Items" in wb.sheetnames:
        li_raw = _read_sheet_rows(wb["Opportunity_Line_Items"])
        li_list = []
        for r in li_raw:
            li_defaults = {
                "Practice__c": "DxP",
                "TotalPrice": 500000.0,
                "CurrencyIsoCode": "USD",
            }
            for k, v in li_defaults.items():
                if k not in r or r[k] is None:
                    r[k] = v
            li_list.append(r)
        result["OpportunityLineItem"] = li_list

    # 4. Stage_History
    if "Stage_History" in wb.sheetnames:
        hist_raw = _read_sheet_rows(wb["Stage_History"])
        result["OpportunityHistory"] = hist_raw

    # 5. Bookings_Targets
    if "Bookings_Targets" in wb.sheetnames:
        tgt_raw = _read_sheet_rows(wb["Bookings_Targets"])
        tgt_list = []
        for r in tgt_raw:
            r["loaded_at"] = "2026-10-23T00:00:00"
            r["fiscal_year"] = int(r.get("fiscal_year", 2025))
            q_val = str(r.get("quarter", "1"))
            if "1" in q_val:
                r["quarter"] = 1
            elif "2" in q_val:
                r["quarter"] = 2
            elif "3" in q_val:
                r["quarter"] = 3
            elif "4" in q_val:
                r["quarter"] = 4
            else:
                r["quarter"] = 1
            tgt_list.append(r)
        result["BookingsTarget"] = tgt_list

    # 6. Offerings
    if "Offerings" in wb.sheetnames:
        off_raw = _read_sheet_rows(wb["Offerings"])
        result["OfferingCatalogue"] = off_raw

    # 7. Bid_Pursuits
    if "Bid_Pursuits" in wb.sheetnames:
        bid_raw = _read_sheet_rows(wb["Bid_Pursuits"])
        pursuit_list = []
        quality_list = []
        for r in bid_raw:
            p_dict = {
                "Pursuit_Id": str(r.get("Pursuit_Id", "")),
                "CRM_Opportunity_Id": str(r.get("CRM_Opportunity_Id", "")),
                "RFP_Received": str(r.get("RFP_Received", "2024-08-01")),
                "RFP_Submitted": str(r.get("RFP_Submitted", "2024-08-20")),
                "Decision": str(r.get("Decision", "Pending")),
                "SLA_Target_Days": int(r.get("SLA_Target_Days", 21)),
                "Orals_Reached": bool(r.get("Orals_Reached", True)),
                "Gate_Score": int(r.get("Gate_Score", 80)),
            }
            pursuit_list.append(p_dict)
            if "Quality_Score" in r and r["Quality_Score"] is not None:
                quality_list.append({
                    "Pursuit_Id": p_dict["Pursuit_Id"],
                    "CRM_Opportunity_Id": p_dict["CRM_Opportunity_Id"],
                    "Quality_Score": float(r["Quality_Score"]),
                    "Reviewed_On": p_dict["RFP_Submitted"],
                })
        result["Pursuit"] = pursuit_list
        if quality_list:
            result["QualityReview"] = quality_list

    # 8. Financials_&_Pricing
    if "Financials_&_Pricing" in wb.sheetnames:
        fin_raw = _read_sheet_rows(wb["Financials_&_Pricing"])
        fin_list = []
        pricing_list = []
        contract_list = []
        for idx, r in enumerate(fin_raw, start=1):
            opp_id = str(r.get("Opportunity_Id", f"OPP-{idx}"))
            month = str(r.get("As_Of_Month", "2024-11"))
            deliv_margin = float(r.get("Delivery_Margin_Pct", 0.38))
            fin_list.append({
                "Opportunity_Id": opp_id,
                "Delivery_Margin_Pct": deliv_margin,
                "As_Of_Month": month,
            })
            pricing_list.append({
                "Opportunity_Id": opp_id,
                "Version": "v1",
                "Bid_Margin_Pct": float(r.get("Approved_Margin_Pct", r.get("Target_Margin_Pct", 0.40))),
            })
            contract_list.append({
                "contract_id": f"CTR-{idx:03d}",
                "crm_opportunity_id": opp_id,
                "booked_month": month,
                "amount_usd": 2500000.0,
            })
        result["ProjectFinancials"] = fin_list
        result["PricingVersion"] = pricing_list
        result["Contract"] = contract_list

    # 9. AI_Validation
    if "AI_Validation" in wb.sheetnames:
        val_raw = _read_sheet_rows(wb["AI_Validation"])
        val_list = []
        for idx, r in enumerate(val_raw, start=1):
            val_id = str(r.get("Validation_ID", f"VAL-2024-{idx:03d}"))
            # Match opportunity with validation id if available
            opp_id = f"OPP-{100+idx}"
            if "Opportunity" in result:
                for opp in result["Opportunity"]:
                    if opp.get("Validation_ID__c") == val_id:
                        opp_id = opp["Id"]
                        break
            val_list.append({
                "Validation_Id": val_id,
                "CRM_Opportunity_Id": opp_id,
                "Status": str(r.get("Status", "Approved")),
                "Reviewed_On": str(r.get("Approved_Date", "2024-09-01")),
            })
        result["ValidationRecord"] = val_list

    # 10. Assets_&_Knowledge
    if "Assets_&_Knowledge" in wb.sheetnames:
        kb_raw = _read_sheet_rows(wb["Assets_&_Knowledge"])
        kb_list = []
        asset_builds = []
        proposal_assets = []
        for idx, r in enumerate(kb_raw, start=1):
            asset_id = str(r.get("Asset_Id", f"AST-{idx:03d}"))
            kb_list.append({
                "Asset_Id": asset_id,
                "Title": str(r.get("Name", "Asset Name")),
                "Asset_Type": str(r.get("Asset_Type", "Solution Accelerator")),
                "Offering": str(r.get("Offering_Id", "Pulse Insights")),
                "Practice": "DxP",
                "Platform": "Adobe",
                "Vertical": "Cross-Industry",
                "Last_Refreshed": "2024-10-01",
            })
            asset_builds.append({
                "Build_Id": f"BLD-{idx:03d}",
                "Asset_Id": asset_id,
                "Asset_Type": str(r.get("Asset_Type", "Solution Accelerator")),
                "Name": str(r.get("Name", "Asset Name")),
                "Practice": "DxP",
                "Platform": "Adobe",
                "Vertical": "Cross-Industry",
                "Status": "Released",
                "Target_Quarter": "2024-Q3",
                "Start_Date": "2024-06-01",
                "Released_Date": "2024-09-15",
            })
            proposal_assets.append({
                "Pursuit_Id": f"PUR-{idx:03d}",
                "CRM_Opportunity_Id": f"OPP-{100+idx}",
                "Asset_Id": asset_id,
                "Used_On": "2024-09-20",
            })
        result["KbAsset"] = kb_list
        result["AssetBuild"] = asset_builds
        result["ProposalAsset"] = proposal_assets

    # 11. Account_Plans
    if "Account_Plans" in wb.sheetnames:
        ap_raw = _read_sheet_rows(wb["Account_Plans"])
        ap_list = []
        for r in ap_raw:
            ap_list.append({
                "Account_Id": str(r.get("Account_Id", "")),
                "Plan_Status": str(r.get("Plan_Status", "Approved")),
                "Last_Review_Date": str(r.get("Last_Review_Date", "2024-10-01")),
                "Whitespace_Targets": 3,
            })
        result["AccountPlan"] = ap_list

    # 12. Partner_Ecosystem
    if "Partner_Ecosystem" in wb.sheetnames:
        par_raw = _read_sheet_rows(wb["Partner_Ecosystem"])
        tier_list = []
        reg_list = []
        cert_list = []
        for idx, r in enumerate(par_raw, start=1):
            partner_name = str(r.get("Partner", "Adobe"))
            certs = int(r.get("Total_Certifications", 100))
            tier_list.append({
                "Partner": partner_name,
                "Tier": str(r.get("Tier", "Platinum")),
                "Required_Certifications": int(certs * 0.8),
            })
            reg_list.append({
                "Registration_Id": f"REG-{idx:03d}",
                "CRM_Opportunity_Id": f"OPP-{100+idx}",
                "Partner": partner_name,
                "Co_Sell": True,
                "Registered_On": "2024-08-01",
            })
            for c_i in range(1, 4):
                cert_list.append({
                    "Partner": partner_name,
                    "Certification": f"{partner_name} Certified Specialist {c_i}",
                    "Holder": f"architect{c_i}@{partner_name.lower()}.com",
                    "Certified_On": "2024-01-15",
                    "Expires_On": "2025-01-15",
                })
        result["Tier"] = tier_list
        result["DealRegistration"] = reg_list
        result["Certification"] = cert_list

    # 13. Capacity_&_Resources
    if "Capacity_&_Resources" in wb.sheetnames:
        cap_raw = _read_sheet_rows(wb["Capacity_&_Resources"])
        res_list = []
        cost_list = []
        ts_list = []
        for idx, r in enumerate(cap_raw, start=1):
            res_id = str(r.get("Resource_Id", f"RES-{idx:03d}"))
            role = str(r.get("Role", "Solution Architect"))
            cost = float(r.get("Hourly_Cost_USD", 180.0))
            hours = float(r.get("Weekly_Hours_Allocated", 40.0))
            res_list.append({
                "Resource_Id": res_id,
                "Name": str(r.get("Name", "Architect")),
                "Role": role,
            })
            cost_list.append({
                "Role": role,
                "Rate_USD_Hour": cost,
            })
            ts_list.append({
                "Entry_Id": f"TS-{idx:03d}",
                "Opportunity_Id": f"OPP-{100+idx}",
                "Resource_Id": res_id,
                "Week_Start": "2024-10-07",
                "Hours": hours,
            })
        result["Resource"] = res_list
        result["CostRate"] = cost_list
        result["TimesheetEntry"] = ts_list

    # 14. Market_Signals_&_Events
    if "Market_Signals_&_Events" in wb.sheetnames:
        mkt_raw = _read_sheet_rows(wb["Market_Signals_&_Events"])
        ws_list = []
        for idx, r in enumerate(mkt_raw, start=1):
            conv = bool(r.get("Converted_To_Deal", True))
            ws_list.append({
                "Workshop_Id": str(r.get("Workshop_Id", f"WS-{idx:03d}")),
                "Workshop_Title": str(r.get("Workshop_Title", "Innovation Workshop")),
                "Account_Id": str(r.get("Account_Id", f"ACC-{idx:03d}")),
                "Practice": str(r.get("Practice", "DxP")),
                "Platform": "Adobe",
                "Vertical": "Banking",
                "Geography": "Americas",
                "Facilitator_UPN": "gtm.lead@cognizant.com",
                "Workshop_Date": str(r.get("Workshop_Date", "2024-07-15")),
                "Opportunity_Id": str(r.get("Opportunity_Id", "")) if conv else None,
                "Opportunity_Created_Date": str(r.get("Workshop_Date", "2024-07-15")) if conv else None,
                "Days_To_Opportunity": int(r.get("Days_To_Opportunity", 30)) if conv and r.get("Days_To_Opportunity") is not None else None,
                "Converted_Within_90d": conv,
                "Is_Qualified": conv,
                "Is_Won": conv,
            })
        result["Workshop"] = ws_list

    # Header-only sheets are treated as absent so connectors fall back to synthetic data.
    cleaned = {k: v for k, v in result.items() if v}
    return cleaned if cleaned else None


if __name__ == "__main__":
    data = load_from_excel()
    if data:
        print("Excel data loaded successfully!")
        for k, v in data.items():
            print(f"  - {k}: {len(v)} records")
    else:
        print("Excel file not found or empty.")
