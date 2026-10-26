"""Build master data Excel template covering all dashboard modules:
1. Executive Summary (EXE-01..10)
2. Pipeline (PIP-01..07)
3. Pursuits & Wins (PUR-01..06)
4. Offerings (OFF-01..05)
5. Accounts (ACC-01..04)
6. Partners (PAR-01..03)
7. Solutions & Capacity (CAP-01..04)
8. Market Signals (MKT-01..04)
"""

import openpyxl
from pathlib import Path
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

font_title = Font(name="Calibri", size=16, bold=True, color="1F497D")
font_subtitle = Font(name="Calibri", size=11, italic=True, color="595959")
font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)
align_left = Alignment(horizontal="left", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")
align_center = Alignment(horizontal="center", vertical="center")

border_thin = Side(border_style="thin", color="D9D9D9")
box_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

def format_sheet(ws, title, subtitle, headers, data, num_fmts=None):
    ws.views.sheetView[0].showGridLines = True
    ws.cell(row=1, column=1, value=title).font = font_title
    ws.cell(row=2, column=1, value=subtitle).font = font_subtitle
    
    # Headers
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_header
        cell.border = box_border
    
    # Data
    for row_idx, row_data in enumerate(data, start=5):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = box_border
            fmt = num_fmts.get(col_idx) if num_fmts else None
            if fmt:
                cell.number_format = fmt
                cell.alignment = align_right
            elif isinstance(val, (int, float)) and not isinstance(val, bool):
                cell.alignment = align_right
            elif isinstance(val, bool):
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    # Auto column width
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 42)


# --- 1. Sheet: 00_Overview_&_Directory ---
ws_ov = wb.active
ws_ov.title = "00_Overview_&_Directory"
ws_ov.views.sheetView[0].showGridLines = True
ws_ov.cell(row=1, column=1, value="Moment GTM Dashboard — Master Data Mapping Directory").font = font_title
ws_ov.cell(row=2, column=1, value="Cross-reference directory of all 8 business modules, metric IDs, and corresponding Excel data worksheets.").font = font_subtitle

overview_headers = ["Module Name", "Route / Tab", "Metric IDs Covered", "Primary Excel Worksheets Used", "Key Business Focus / Leadership Purpose"]
overview_data = [
    ["Executive Summary", "/executive", "EXE-01 to EXE-10", "Accounts, Opportunities, Bookings_Targets, Stage_History, Offerings", "High-level health: Bookings runway, 6 north-star KPIs, quarterly pacing, vertical mix, and high-value deals needing attention."],
    ["Pipeline & Conversion", "/pipeline", "PIP-01 to PIP-07", "Opportunities, Stage_History", "Pipeline dynamics: Stage progression funnel, ageing distribution, practice/platform cuts, deal size tiers, and weekly velocity."],
    ["Pursuits & Wins", "/pursuits", "PUR-01 to PUR-06", "Opportunities, Bid_Pursuits, Financials_&_Pricing", "Sales execution: Win rates, loss reason analysis, source-based effectiveness, bid gate discipline, orals conversion, and margin erosion."],
    ["Offerings Portfolio", "/offerings", "OFF-01 to OFF-05", "Opportunities, Offerings, AI_Validation, Assets_&_Knowledge", "Productised GTM: Offering attach rates, multi-practice deals, AI-led validation split, and asset reuse acceleration."],
    ["Account Penetration", "/accounts", "ACC-01 to ACC-04", "Accounts, Opportunities, Opportunity_Line_Items, Account_Plans", "Client portfolio: 8-practice penetration heatmaps, whitespace pursuit, new-logo vs expansion mix, and account plan governance."],
    ["Partner Ecosystem", "/partners", "PAR-01 to PAR-03", "Opportunities, Partner_Ecosystem", "Alliances: Pipeline by hyper-scaler/ISV (Adobe, Salesforce, Microsoft, Google), co-sell vs resell performance, and technical certifications."],
    ["Solutions & Capacity", "/capacity", "CAP-01 to CAP-04", "Opportunities, Bid_Pursuits, Capacity_&_Resources", "Operational capacity: Solution architect deal allocations, RFP SLA turnaround velocity, cost of sale ratios, and proposal quality scores."],
    ["Market Signals & Demand", "/market-signals", "MKT-01 to MKT-04", "Market_Signals_&_Events, Opportunities", "Inbound demand: Thought leadership content reach, discovery workshop to deal conversion, campaign ROI, and analyst quadrant positioning."]
]

for col_idx, h in enumerate(overview_headers, start=1):
    cell = ws_ov.cell(row=4, column=col_idx, value=h)
    cell.font = font_header
    cell.fill = fill_header
    cell.alignment = align_header
    cell.border = box_border

for r_idx, row in enumerate(overview_data, start=5):
    for c_idx, val in enumerate(row, start=1):
        cell = ws_ov.cell(row=r_idx, column=c_idx, value=val)
        cell.border = box_border
        cell.alignment = align_left

for col in ws_ov.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws_ov.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45)


# --- 2. Sheet: Accounts ---
ws_acc = wb.create_sheet(title="Accounts")
acc_headers = ["Id", "Name", "Industry", "BillingRegion__c", "Strategic__c", "Client_Partner_UPN__c"]
acc_data = [
    ["ACC-001", "Global Bank Corp", "Banking", "Americas", True, "john.doe@cognizant.com"],
    ["ACC-002", "Apex Retailers Ltd", "Retail", "Americas", True, "jane.smith@cognizant.com"],
    ["ACC-003", "BioHealth Pharma", "Pharmaceuticals", "EMEA", False, "alex.jones@cognizant.com"],
    ["ACC-004", "TechCom Global", "Telecommunications", "APAC", True, "sam.wilson@cognizant.com"],
    ["ACC-005", "AutoMotors Inc", "Automotive", "Americas", False, "john.doe@cognizant.com"]
]
format_sheet(ws_acc, "Account Master Data", "Source: SRC-01 CRM. Feeds Executive (EXE-09), Accounts (ACC-01..04), and Pipeline views.", acc_headers, acc_data)


# --- 3. Sheet: Opportunities ---
ws_opp = wb.create_sheet(title="Opportunities")
opp_headers = [
    "Id", "Name", "AccountId", "StageName", "Amount", "CurrencyIsoCode", "Probability",
    "CreatedDate", "CloseDate", "Offering__c", "Lead_Practice__c", "Primary_Platform__c",
    "LeadSource", "OwnerUPN", "Loss_Reason__c", "AI_Led__c", "Validation_ID__c",
    "Partner__c", "Partner_Role__c", "CampaignId", "Workshop_Originated__c"
]
opp_data = [
    ["OPP-101", "Global Bank - Pulse Insights Rollout", "ACC-001", "Negotiate", 4500000.0, "USD", 0.80, "2024-08-15", "2025-03-30", "Pulse Insights", "DxP", "Adobe", "Client RFP", "john.doe@cognizant.com", None, True, "VAL-2024-001", "Adobe", "Co-sell", "CAMP-101", False],
    ["OPP-102", "Apex Retail - Agentic Commerce Portal", "ACC-002", "Closed Won", 2800000.0, "USD", 1.00, "2024-07-10", "2024-11-20", "Agentic Commerce", "Commerce", "Salesforce", "Proactive", "jane.smith@cognizant.com", None, False, None, "Salesforce", "Co-sell", None, True],
    ["OPP-103", "BioHealth - Content Supply Chain", "ACC-003", "Propose", 3200000.0, "USD", 0.40, "2024-09-01", "2025-04-15", "Content Supply Chain", "Content Ops", "Adobe", "Partner-sourced", "alex.jones@cognizant.com", None, False, None, "Adobe", "Sourced", "CAMP-102", False],
    ["OPP-104", "TechCom - Marketing OS Integration", "ACC-004", "Closed Lost", 1500000.0, "USD", 0.00, "2024-08-01", "2024-10-15", "Marketing OS", "Marketing", "Sitecore", "Campaign / Marketing", "sam.wilson@cognizant.com", "Price / commercial terms", False, None, None, None, "CAMP-103", False],
    ["OPP-105", "AutoMotors - DX Modernisation", "ACC-005", "Qualify", 2100000.0, "USD", 0.25, "2024-09-10", "2025-05-30", "DX Modernisation", "Strategy", "Platform-agnostic", "Account expansion", "john.doe@cognizant.com", None, True, "VAL-2024-002", "Microsoft", "Co-sell", None, True]
]
format_sheet(
    ws_opp,
    "Opportunities Pipeline & Closed Deals",
    "Source: SRC-01 CRM. Core entity feeding Executive, Pipeline (PIP-01..07), Pursuits, and Partners.",
    opp_headers,
    opp_data,
    num_fmts={5: "$#,##0.00", 7: "0.00%"}
)


# --- 4. Sheet: Opportunity_Line_Items ---
ws_li = wb.create_sheet(title="Opportunity_Line_Items")
li_headers = ["Id", "OpportunityId", "Practice__c", "TotalPrice", "CurrencyIsoCode"]
li_data = [
    ["LI-101-1", "OPP-101", "DxP", 3000000.0, "USD"],
    ["LI-101-2", "OPP-101", "Strategy", 1500000.0, "USD"],
    ["LI-102-1", "OPP-102", "Commerce", 2000000.0, "USD"],
    ["LI-102-2", "OPP-102", "Design", 800000.0, "USD"],
    ["LI-103-1", "OPP-103", "Content Ops", 2200000.0, "USD"],
    ["LI-103-2", "OPP-103", "Marketing", 1000000.0, "USD"],
    ["LI-105-1", "OPP-105", "Strategy", 1200000.0, "USD"],
    ["LI-105-2", "OPP-105", "DxP", 900000.0, "USD"]
]
format_sheet(ws_li, "Opportunity Multi-Practice Line Items", "Feeds OFF-02 (Practices per deal & attach rates) and ACC-01 (Practice penetration matrix).", li_headers, li_data, num_fmts={4: "$#,##0.00"})


# --- 5. Sheet: Stage_History ---
ws_hist = wb.create_sheet(title="Stage_History")
hist_headers = ["OpportunityId", "StageName", "CreatedDate", "Seq"]
hist_data = [
    ["OPP-101", "Identify", "2024-08-15", 1],
    ["OPP-101", "Qualify", "2024-09-01", 2],
    ["OPP-101", "Propose", "2024-10-10", 3],
    ["OPP-101", "Negotiate", "2024-12-01", 4],
    ["OPP-102", "Identify", "2024-07-10", 1],
    ["OPP-102", "Qualify", "2024-08-01", 2],
    ["OPP-102", "Propose", "2024-09-01", 3],
    ["OPP-102", "Closed Won", "2024-11-20", 4]
]
format_sheet(ws_hist, "Opportunity Stage History", "Feeds PIP-01 Stage Funnel, PIP-02 Pipeline Ageing, and EXE-10 Deals Needing Attention.", hist_headers, hist_data)


# --- 6. Sheet: Bookings_Targets ---
ws_tgt = wb.create_sheet(title="Bookings_Targets")
tgt_headers = ["version", "fiscal_year", "quarter", "practice", "amount_usd"]
tgt_data = [
    ["FY25-v1", 2025, 1, "Strategy", 12000000.0],
    ["FY25-v1", 2025, 1, "Design", 8000000.0],
    ["FY25-v1", 2025, 1, "DxP", 15000000.0],
    ["FY25-v1", 2025, 1, "Commerce", 10000000.0],
    ["FY25-v1", 2025, 2, "Strategy", 13000000.0],
    ["FY25-v1", 2025, 2, "Design", 9000000.0],
    ["FY25-v1", 2025, 2, "DxP", 16000000.0],
    ["FY25-v1", 2025, 2, "Commerce", 11000000.0]
]
format_sheet(ws_tgt, "Bookings Targets", "Source: SRC-02 Anaplan Planning. Feeds EXE-01, EXE-02, EXE-04, EXE-07, and EXE-08.", tgt_headers, tgt_data, num_fmts={5: "$#,##0.00"})


# --- 7. Sheet: Offerings ---
ws_off = wb.create_sheet(title="Offerings")
off_headers = ["offering_id", "name", "family"]
off_data = [
    ["OFF-PULSE-INS", "Pulse Insights", "Pulse suite"],
    ["OFF-PULSE-EXP", "Pulse Experience", "Pulse suite"],
    ["OFF-MKT-OS", "Marketing OS", "Marketing OS"],
    ["OFF-AGC", "Agentic Commerce", "Commerce"],
    ["OFF-CSC", "Content Supply Chain", "Content"],
    ["OFF-DXM", "DX Modernisation", "Platforms"]
]
format_sheet(ws_off, "Offering Catalogue", "Source: SharePoint / Offering Catalogue. Feeds EXE-05 and OFF-01..05.", off_headers, off_data)


# --- 8. Sheet: Bid_Pursuits ---
ws_bid = wb.create_sheet(title="Bid_Pursuits")
bid_headers = ["Pursuit_Id", "CRM_Opportunity_Id", "RFP_Received", "RFP_Submitted", "Decision", "SLA_Target_Days", "Orals_Reached", "Gate_Score", "Quality_Score"]
bid_data = [
    ["PUR-001", "OPP-101", "2024-09-01", "2024-09-20", "Pending", 21, True, 85, 4.5],
    ["PUR-002", "OPP-102", "2024-07-15", "2024-08-01", "Won", 20, True, 92, 4.8],
    ["PUR-003", "OPP-103", "2024-09-10", "2024-10-05", "Pending", 25, False, 78, 4.0],
    ["PUR-004", "OPP-104", "2024-08-10", "2024-09-15", "Lost", 21, False, 65, 3.2],
    ["PUR-005", "OPP-105", "2024-09-15", "2024-10-02", "Pending", 20, True, 88, 4.6]
]
format_sheet(ws_bid, "Bid Pursuits & Proposal Quality", "Source: SRC-03 Bid Tool. Feeds PUR-04 (Bid Discipline), PUR-05 (Orals Conversion), CAP-02 (RFP SLA), and CAP-04 (Quality Score).", bid_headers, bid_data)


# --- 9. Sheet: Financials_&_Pricing ---
ws_fin = wb.create_sheet(title="Financials_&_Pricing")
fin_headers = ["Opportunity_Id", "Target_Margin_Pct", "Approved_Margin_Pct", "Delivery_Margin_Pct", "As_Of_Month"]
fin_data = [
    ["OPP-101", 0.42, 0.40, 0.38, "2024-11"],
    ["OPP-102", 0.45, 0.43, 0.44, "2024-10"],
    ["OPP-103", 0.38, 0.36, 0.35, "2024-11"],
    ["OPP-104", 0.40, 0.35, 0.30, "2024-09"],
    ["OPP-105", 0.44, 0.42, 0.41, "2024-11"]
]
format_sheet(ws_fin, "Deal Financials & Delivery Margin", "Source: SRC-04 Finance & SRC-05 Pricing. Feeds PUR-06 (Margin at bid vs delivery).", fin_headers, fin_data, num_fmts={2: "0.0%", 3: "0.0%", 4: "0.0%"})


# --- 10. Sheet: AI_Validation ---
ws_val = wb.create_sheet(title="AI_Validation")
val_headers = ["Validation_ID", "Status", "Reviewer", "Approved_Date", "Risk_Level"]
val_data = [
    ["VAL-2024-001", "Approved", "ai.governance@cognizant.com", "2024-08-25", "Low"],
    ["VAL-2024-002", "Approved", "ai.governance@cognizant.com", "2024-09-20", "Medium"],
    ["VAL-2024-003", "Pending", "ai.governance@cognizant.com", "2024-10-01", "Low"]
]
format_sheet(ws_val, "AI Governance & Validation Register", "Source: SRC-13 SharePoint AI Register. Feeds OFF-03 (AI-led validation split).", val_headers, val_data)


# --- 11. Sheet: Assets_&_Knowledge ---
ws_kb = wb.create_sheet(title="Assets_&_Knowledge")
kb_headers = ["Asset_Id", "Name", "Asset_Type", "Offering_Id", "Downloads", "Reuse_Count"]
kb_data = [
    ["AST-001", "Pulse Banking Accelerator", "Solution Accelerator", "OFF-PULSE-INS", 45, 12],
    ["AST-002", "Agentic Checkout Blueprint", "Architecture Blueprint", "OFF-AGC", 38, 9],
    ["AST-003", "Omnichannel Content Pipeline Demo", "Interactive Demo", "OFF-CSC", 52, 14],
    ["AST-004", "Modern Marketing Reference Stack", "Presentation Deck", "OFF-MKT-OS", 28, 6]
]
format_sheet(ws_kb, "Reusable Knowledge & Solution Assets", "Source: SRC-12 Knowledge & SRC-17 Workfront. Feeds OFF-04 (Asset reuse) and OFF-05 (Demos & accelerators).", kb_headers, kb_data)


# --- 12. Sheet: Account_Plans ---
ws_ap = wb.create_sheet(title="Account_Plans")
ap_headers = ["Account_Id", "Plan_Status", "Health_Score", "Last_Review_Date", "Exec_Sponsor_UPN"]
ap_data = [
    ["ACC-001", "Approved", 90.0, "2024-10-15", "sponsor.exec1@cognizant.com"],
    ["ACC-002", "Approved", 85.0, "2024-09-20", "sponsor.exec2@cognizant.com"],
    ["ACC-003", "Draft", 60.0, "2024-08-10", "sponsor.exec1@cognizant.com"],
    ["ACC-004", "Approved", 88.0, "2024-10-05", "sponsor.exec3@cognizant.com"],
    ["ACC-005", "Needs Review", 55.0, "2024-07-30", "sponsor.exec2@cognizant.com"]
]
format_sheet(ws_ap, "Account Plans & Governance", "Source: SRC-14 Account Plans. Feeds ACC-04 (Account-plan health).", ap_headers, ap_data)


# --- 13. Sheet: Partner_Ecosystem ---
ws_par = wb.create_sheet(title="Partner_Ecosystem")
par_headers = ["Partner", "Tier", "Total_Certifications", "Pipeline_Contribution_USD", "Deal_Registrations_Count"]
par_data = [
    ["Adobe", "Platinum", 450, 48000000.0, 32],
    ["Salesforce", "Summit", 620, 55000000.0, 41],
    ["Microsoft", "Gold", 800, 62000000.0, 48],
    ["Google Cloud", "Premier", 310, 24000000.0, 18]
]
format_sheet(ws_par, "Partner Alliances & Certifications", "Source: SRC-08 Partner Portal & SRC-09 LMS. Feeds PAR-01, PAR-02, and PAR-03.", par_headers, par_data, num_fmts={4: "$#,##0.00"})


# --- 14. Sheet: Capacity_&_Resources ---
ws_cap = wb.create_sheet(title="Capacity_&_Resources")
cap_headers = ["Resource_Id", "Name", "Role", "Active_Deals_Count", "Weekly_Hours_Allocated", "Hourly_Cost_USD"]
cap_data = [
    ["RES-001", "Alex Vance", "Lead Solution Architect", 4, 38.0, 185.0],
    ["RES-002", "Maya Lin", "Principal Enterprise Architect", 5, 44.0, 210.0],
    ["RES-003", "David Kim", "Technical Architect", 3, 32.0, 160.0],
    ["RES-004", "Sarah Connor", "Solutions Lead", 6, 48.0, 195.0]
]
format_sheet(ws_cap, "Solution Architect & Presales Capacity", "Source: SRC-06 Resource & SRC-07 Timesheets. Feeds CAP-01 (Architect Load) and CAP-03 (Cost of Sale).", cap_headers, cap_data, num_fmts={6: "$#,##0.00"})


# --- 15. Sheet: Market_Signals_&_Events ---
ws_mkt = wb.create_sheet(title="Market_Signals_&_Events")
mkt_headers = ["Workshop_Id", "Workshop_Title", "Account_Id", "Practice", "Workshop_Date", "Converted_To_Deal", "Opportunity_Id", "Days_To_Opportunity"]
mkt_data = [
    ["WS-001", "Generative CX Visioning Workshop", "ACC-001", "DxP", "2024-07-15", True, "OPP-101", 31],
    ["WS-002", "Agentic Commerce Innovation Lab", "ACC-002", "Commerce", "2024-06-20", True, "OPP-102", 20],
    ["WS-003", "Modern Content Supply Chain Immersion", "ACC-003", "Content Ops", "2024-08-05", True, "OPP-103", 27],
    ["WS-004", "Enterprise Marketing Architecture Roundtable", "ACC-004", "Marketing", "2024-07-02", False, None, None]
]
format_sheet(ws_mkt, "Discovery Workshops & Events", "Source: SRC-01 Workshop & SRC-10 Marketing. Feeds MKT-02 Discovery workshop conversion and MKT-03 Campaign pipeline.", mkt_headers, mkt_data)


# Save master workbook into data/templates/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
master_path = PROJECT_ROOT / "data" / "templates" / "Moment_GTM_Dashboard_Master_Data_Template.xlsx"
master_path.parent.mkdir(parents=True, exist_ok=True)
wb.save(str(master_path))
print(f"Master Excel Template successfully generated at: {master_path}")
