"""Mock connectors for the Executive-summary sources.

External APIs are not available yet, so each connector serves the seeded synthetic dataset
in the payload shape of the real API it stands in for:

| Connector             | Real integration (production)                         |
|-----------------------|-------------------------------------------------------|
| MockSalesforce        | Salesforce Sales Cloud REST / Bulk API 2.0 (SRC-01)   |
| MockAnaplan           | Anaplan export API (SRC-02)                           |
| MockFinance           | SAP S/4HANA OData contract extract (SRC-04)           |
| MockEntra             | Microsoft Graph users/groups/members (SRC-16)         |
| MockOfferingCatalogue | SharePoint List via Microsoft Graph / M365 MCP        |
| MockValidation        | SharePoint List (AI validation register) via Graph (SRC-13) |
| MockKnowledge         | SharePoint knowledge repository via Graph (SRC-12)    |
| MockAssetTracker      | Adobe Workfront API (SRC-17)                          |
| MockAccountPlan       | CRM account-plan object / SharePoint (SRC-14)         |
| MockPartnerPortal     | Adobe / Salesforce partner-portal export (SRC-08)     |
| MockLms               | Enterprise LMS extract (SRC-09)                       |
| MockPricing           | Pricing tool / deal-desk export (SRC-05)              |
| MockResource          | Resource-management API (SRC-06)                      |
| MockTimesheet         | Timesheet system extract (SRC-07)                     |

The same payloads are exposed over HTTP under `/mock/*` (api/routes/mock_sources.py) so the
contract can be inspected or pointed at by an HTTP-based connector.
"""

from __future__ import annotations

from app.config import settings
from app.connectors.base import SourceConnector, SourceUnavailable
from app.data.excel_loader import load_from_excel
from app.data.generator import generate


class _MockBase:
    source_id: str = ""
    key: str = ""

    def _check(self) -> None:
        if self.key in settings.mock_fail_sources:
            raise SourceUnavailable(f"{self.source_id} mock configured to fail (GTM_MOCK_FAIL_SOURCES)")


class MockSalesforce(_MockBase):
    source_id, key = "SRC-01", "crm"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        excel_data = load_from_excel()
        return {
            "Account": excel_data.get("Account", ds.accounts) if excel_data and "Account" in excel_data else ds.accounts,
            "Opportunity": (
                excel_data.get("Opportunity", ds.opportunities)
                if excel_data and "Opportunity" in excel_data
                else ds.opportunities
            ),
            "OpportunityHistory": (
                excel_data.get("OpportunityHistory", ds.stage_history)
                if excel_data and "OpportunityHistory" in excel_data
                else ds.stage_history
            ),
            "OpportunityLineItem": (
                excel_data.get("OpportunityLineItem", ds.line_items)
                if excel_data and "OpportunityLineItem" in excel_data
                else ds.line_items
            ),
            "User": ds.users,
            "OpportunityTeam": ds.opportunity_team,
            "Workshop": (
                excel_data.get("Workshop", ds.workshops)
                if excel_data and "Workshop" in excel_data
                else ds.workshops
            ),
        }


class MockAnaplan(_MockBase):
    source_id, key = "SRC-02", "planning"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        excel_data = load_from_excel()
        return {
            "BookingsTarget": (
                excel_data.get("BookingsTarget", ds.targets)
                if excel_data and "BookingsTarget" in excel_data
                else ds.targets
            ),
            "BuildPlan": ds.build_plan,
        }


class MockFinance(_MockBase):
    source_id, key = "SRC-04", "finance"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        excel_data = load_from_excel()
        return {
            "Contract": (
                excel_data.get("Contract", ds.finance_contracts)
                if excel_data and "Contract" in excel_data
                else ds.finance_contracts
            ),
            "BookingHistory": ds.booking_history,
            "CostRate": (
                excel_data.get("CostRate", ds.cost_rates)
                if excel_data and "CostRate" in excel_data
                else ds.cost_rates
            ),
            "ProjectFinancials": (
                excel_data.get("ProjectFinancials", ds.project_financials)
                if excel_data and "ProjectFinancials" in excel_data
                else ds.project_financials
            ),
        }


class MockBidTool(_MockBase):
    source_id, key = "SRC-03", "bid"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        excel_data = load_from_excel()
        return {
            "Pursuit": (
                excel_data.get("Pursuit", ds.bid_pursuits)
                if excel_data and "Pursuit" in excel_data
                else ds.bid_pursuits
            ),
            "ProposalAsset": (
                excel_data.get("ProposalAsset", ds.proposal_assets)
                if excel_data and "ProposalAsset" in excel_data
                else ds.proposal_assets
            ),
            "QualityReview": (
                excel_data.get("QualityReview", ds.quality_reviews)
                if excel_data and "QualityReview" in excel_data
                else ds.quality_reviews
            ),
        }


class MockPricing(_MockBase):
    source_id, key = "SRC-05", "pricing"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "PricingVersion": (
                excel_data.get("PricingVersion", generate().pricing_versions)
                if excel_data and "PricingVersion" in excel_data
                else generate().pricing_versions
            )
        }


class MockResource(_MockBase):
    source_id, key = "SRC-06", "resource"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "Resource": (
                excel_data.get("Resource", generate().resources)
                if excel_data and "Resource" in excel_data
                else generate().resources
            )
        }


class MockTimesheet(_MockBase):
    source_id, key = "SRC-07", "timesheet"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "TimesheetEntry": (
                excel_data.get("TimesheetEntry", generate().timesheets)
                if excel_data and "TimesheetEntry" in excel_data
                else generate().timesheets
            )
        }


class MockEntra(_MockBase):
    source_id, key = "SRC-16", "identity"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        return {
            "users": ds.identity_users,
            "groups": ds.identity_groups,
            "members": ds.identity_memberships,
        }


class MockOfferingCatalogue(_MockBase):
    source_id, key = "REF-OFF", "catalogue"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "OfferingCatalogue": (
                excel_data.get("OfferingCatalogue", generate().offerings)
                if excel_data and "OfferingCatalogue" in excel_data
                else generate().offerings
            )
        }


class MockValidation(_MockBase):
    source_id, key = "SRC-13", "validation"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "ValidationRecord": (
                excel_data.get("ValidationRecord", generate().validation_records)
                if excel_data and "ValidationRecord" in excel_data
                else generate().validation_records
            )
        }


class MockKnowledge(_MockBase):
    source_id, key = "SRC-12", "kb"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "KbAsset": (
                excel_data.get("KbAsset", generate().kb_assets)
                if excel_data and "KbAsset" in excel_data
                else generate().kb_assets
            )
        }


class MockAssetTracker(_MockBase):
    source_id, key = "SRC-17", "assets"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "AssetBuild": (
                excel_data.get("AssetBuild", generate().asset_builds)
                if excel_data and "AssetBuild" in excel_data
                else generate().asset_builds
            )
        }


class MockAccountPlan(_MockBase):
    source_id, key = "SRC-14", "account_plan"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        excel_data = load_from_excel()
        return {
            "AccountPlan": (
                excel_data.get("AccountPlan", generate().account_plans)
                if excel_data and "AccountPlan" in excel_data
                else generate().account_plans
            )
        }


class MockPartnerPortal(_MockBase):
    source_id, key = "SRC-08", "partner"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        excel_data = load_from_excel()
        return {
            "DealRegistration": (
                excel_data.get("DealRegistration", ds.partner_registrations)
                if excel_data and "DealRegistration" in excel_data
                else ds.partner_registrations
            ),
            "Certification": (
                excel_data.get("Certification", ds.partner_certifications)
                if excel_data and "Certification" in excel_data
                else ds.partner_certifications
            ),
            "Tier": (
                excel_data.get("Tier", ds.partner_tiers)
                if excel_data and "Tier" in excel_data
                else ds.partner_tiers
            ),
        }


class MockLms(_MockBase):
    source_id, key = "SRC-09", "lms"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        return {"LearningRecord": generate().lms_records}


class MockMarketingAutomation(_MockBase):
    source_id, key = "SRC-10", "mktg"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        return {"Campaign": ds.campaigns, "CampaignMember": ds.campaign_members}


class MockWebAnalytics(_MockBase):
    source_id, key = "SRC-11", "web"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        ds = generate()
        return {"ContentAsset": ds.web_assets, "EngagementMetric": ds.web_engagement}


class MockAnalystRelations(_MockBase):
    source_id, key = "SRC-15", "analyst"

    def extract(self) -> dict[str, list[dict]]:
        self._check()
        return {"AnalystEvaluation": generate().analyst_evaluations}


def connectors() -> list[SourceConnector]:
    if settings.source_mode != "mock":
        raise NotImplementedError("Only GTM_SOURCE_MODE=mock is implemented; add real API connectors here.")
    return [
        MockSalesforce(),
        MockAnaplan(),
        MockFinance(),
        MockBidTool(),
        MockEntra(),
        MockOfferingCatalogue(),
        MockValidation(),
        MockKnowledge(),
        MockAssetTracker(),
        MockAccountPlan(),
        MockPartnerPortal(),
        MockLms(),
        MockPricing(),
        MockResource(),
        MockTimesheet(),
        MockMarketingAutomation(),
        MockWebAnalytics(),
        MockAnalystRelations(),
    ]
