"""/mock/* — HTTP stand-ins for the external source APIs (not available yet).

Payloads follow the shape of each real API closely enough to develop and test connectors:
Salesforce query results, Anaplan export rows, SAP OData `value` arrays, Microsoft Graph
collections. They serve the same seeded dataset the ELT loads.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.connectors.base import SourceUnavailable
from app.connectors.mock import (
    MockAccountPlan,
    MockAnalystRelations,
    MockAnaplan,
    MockAssetTracker,
    MockBidTool,
    MockEntra,
    MockFinance,
    MockKnowledge,
    MockLms,
    MockMarketingAutomation,
    MockOfferingCatalogue,
    MockPartnerPortal,
    MockSalesforce,
    MockValidation,
    MockWebAnalytics,
)

router = APIRouter(prefix="/mock", tags=["mock source APIs"])

SF_OBJECTS = {"Account", "Opportunity", "OpportunityHistory", "OpportunityLineItem", "User", "Workshop"}


def _extract(connector) -> dict[str, list[dict]]:
    try:
        return connector.extract()
    except SourceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/salesforce/services/data/v60.0/sobjects/{sobject}/records",
    summary="SRC-01 Salesforce — query result for one object",
)
def salesforce(sobject: str, limit: int = 2000, offset: int = 0) -> dict:
    if sobject not in SF_OBJECTS:
        raise HTTPException(status_code=404, detail=f"Unsupported sObject {sobject}")
    records = _extract(MockSalesforce())[sobject]
    page = records[offset : offset + limit]
    done = offset + limit >= len(records)
    return {
        "totalSize": len(records),
        "done": done,
        "nextRecordsUrl": (
            None
            if done
            else f"/mock/salesforce/services/data/v60.0/sobjects/{sobject}/records?offset={offset + limit}"
            f"&limit={limit}"
        ),
        "records": [{"attributes": {"type": sobject}, **r} for r in page],
    }


@router.get(
    "/anaplan/2/0/workspaces/moment/models/gtm-plan/exports/bookings-target",
    summary="SRC-02 Anaplan — bookings target export",
)
def anaplan_targets() -> dict:
    return {"status": {"code": 200}, "rows": _extract(MockAnaplan())["BookingsTarget"]}


@router.get("/sap/opu/odata/sap/ZGTM_CONTRACT_SRV/Contracts", summary="SRC-04 SAP S/4HANA OData")
def finance_contracts() -> dict:
    return {"value": _extract(MockFinance())["Contract"]}


@router.get("/bid/api/v1/pursuits", summary="SRC-03 Bid & proposal tool — pursuits")
def bid_pursuits() -> dict:
    return {"value": _extract(MockBidTool())["Pursuit"]}


@router.get("/graph/v1.0/users", summary="SRC-16 Microsoft Graph users")
def graph_users() -> dict:
    return {"value": _extract(MockEntra())["users"]}


@router.get("/graph/v1.0/groups", summary="SRC-16 Microsoft Graph groups")
def graph_groups() -> dict:
    return {"value": _extract(MockEntra())["groups"]}


@router.get("/graph/v1.0/groups/{group_id}/members", summary="SRC-16 Graph group members")
def graph_members(group_id: str) -> dict:
    data = _extract(MockEntra())
    ids = {m["userId"] for m in data["members"] if m["groupId"] == group_id}
    return {"value": [u for u in data["users"] if u["id"] in ids]}


@router.get(
    "/graph/v1.0/sites/moment/lists/offering-catalogue/items",
    summary="Offering catalogue — SharePoint List via Graph",
)
def offering_catalogue() -> dict:
    return {"value": [{"fields": o} for o in _extract(MockOfferingCatalogue())["OfferingCatalogue"]]}


@router.get("/graph/v1.0/sites/moment/lists/ai-validation/items", summary="SRC-13 AI validation register")
def ai_validation_register() -> dict:
    return {"value": [{"fields": r} for r in _extract(MockValidation())["ValidationRecord"]]}


@router.get("/graph/v1.0/sites/moment/lists/knowledge/items", summary="SRC-12 Knowledge repository")
def knowledge_repository() -> dict:
    return {"value": [{"fields": r} for r in _extract(MockKnowledge())["KbAsset"]]}


@router.get("/workfront/attask/api/v15.0/proj/search", summary="SRC-17 Workfront asset builds")
def workfront_builds() -> dict:
    return {"data": _extract(MockAssetTracker())["AssetBuild"]}


@router.get("/graph/v1.0/sites/moment/lists/account-plans/items", summary="SRC-14 Account plans")
def account_plans() -> dict:
    return {"value": [{"fields": r} for r in _extract(MockAccountPlan())["AccountPlan"]]}


@router.get("/partners/api/v1/{object_name}", summary="SRC-08 Partner portal export")
def partner_portal(object_name: str) -> dict:
    data = _extract(MockPartnerPortal())
    keys = {"registrations": "DealRegistration", "certifications": "Certification", "tiers": "Tier"}
    if object_name not in keys:
        raise HTTPException(status_code=404, detail=f"Unsupported object {object_name}")
    return {"value": data[keys[object_name]]}


@router.get("/lms/api/v1/learning-records", summary="SRC-09 LMS learning records")
def lms_records() -> dict:
    return {"value": _extract(MockLms())["LearningRecord"]}


@router.get("/mktg/api/v1/{object_name}", summary="SRC-10 Marketing automation export")
def marketing_automation(object_name: str) -> dict:
    data = _extract(MockMarketingAutomation())
    keys = {"campaigns": "Campaign", "members": "CampaignMember"}
    if object_name not in keys:
        raise HTTPException(status_code=404, detail=f"Unsupported object {object_name}")
    return {"value": data[keys[object_name]]}


@router.get("/web-analytics/api/v1/{object_name}", summary="SRC-11 Web & content analytics")
def web_analytics(object_name: str) -> dict:
    data = _extract(MockWebAnalytics())
    keys = {"assets": "ContentAsset", "engagement": "EngagementMetric"}
    if object_name not in keys:
        raise HTTPException(status_code=404, detail=f"Unsupported object {object_name}")
    return {"value": data[keys[object_name]]}


@router.get(
    "/graph/v1.0/sites/moment/lists/analyst-evaluations/items",
    summary="SRC-15 Analyst relations register",
)
def analyst_evaluations() -> dict:
    return {"value": [{"fields": r} for r in _extract(MockAnalystRelations())["AnalystEvaluation"]]}
