# Project Scripts & Automation Tools

This directory contains standalone utility scripts, data generation tooling, and operational scripts for the **Moment GTM Dashboard** workspace.

---

## Available Scripts

### `build_all_modules_excel_template.py`
- **Purpose:** Programmatically builds and styles the complete 15-worksheet Master Data Excel Template spanning all 8 GTM dashboard modules.
- **Output:** `data/templates/Moment_GTM_Dashboard_Master_Data_Template.xlsx`
- **Sheets Generated:**
  1. `Accounts` (ACC-01..04)
  2. `Opportunities` (PIP-01..07)
  3. `Opportunity_Line_Items` (EXE-01, PIP-04)
  4. `Stage_History` (PIP-07 Velocity)
  5. `Bookings_Targets` (EXE-01, PUR-01 Quotas)
  6. `Pursuits_&_Bids` (PUR-01..06)
  7. `Finance_Contracts` (EXE-01, Margin)
  8. `Resource_Cost_Rates` (CAP-03 Cost of Sale)
  9. `Project_Financials` (PUR-06 Delivery Margin)
  10. `Offerings_Catalogue` (OFF-01..05)
  11. `Offering_Validations` (OFF-02 Readiness)
  12. `Reusable_Assets_KB` (OFF-05 Reuse)
  13. `Partner_Alliances` (PAR-01..03)
  14. `Presales_Architect_Capacity` (CAP-01, CAP-03)
  15. `Market_Signals_&_Events` (MKT-01..04)

#### Execution
From the project root:
```powershell
python scripts/build_all_modules_excel_template.py
```
*(Requires `openpyxl` installed, available in backend `.venv` or system Python)*
