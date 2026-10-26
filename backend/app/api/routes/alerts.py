"""/api/alerts/* — FR-ALR-01..03: threshold alert rules, user subscriptions, and weekly digest."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, platform_dep, require_module
from app.data import reference_data as ref
from app.domain.enums import Role
from app.domain.models import User
from app.platform.admin_store import get_admin_store
from app.platform.audit import get_audit
from app.platform.db import Platform
from app.semantic import alerts as alerts_engine
from app.semantic import definitions, rls

router = APIRouter(prefix="/api/alerts", tags=["alerts & digest"])
AdminUser = Annotated[User, Depends(require_module("admin"))]
Plat = Annotated[Platform, Depends(platform_dep)]

VALID_CHANNELS = {"email", "teams"}
VALID_OPERATORS = {"lt", "lte", "gt", "gte", "eq"}
VALID_SEVERITIES = {"critical", "warning"}
VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


class AlertRuleIn(BaseModel):
    rule_id: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=3, max_length=500)
    metric_id: str
    kind: Literal["coverage_drop", "large_deal_slip", "unvalidated_ai_propose", "metric_threshold"] = (
        "metric_threshold"
    )
    operator: Literal["lt", "lte", "gt", "gte", "eq"] = "lt"
    threshold: float
    unit: str = "count"
    severity: Literal["critical", "warning"] = "warning"
    channels: list[Literal["email", "teams"]] = Field(default_factory=lambda: ["email", "teams"])
    enabled: bool = True


class SubscriptionItemIn(BaseModel):
    target_id: str
    email: bool = True
    teams: bool = True


class SubscriptionsUpdateIn(BaseModel):
    subscriptions: list[SubscriptionItemIn]


class DigestScheduleIn(BaseModel):
    enabled: bool = True
    day_of_week: Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] = (
        "Monday"
    )
    hour_utc: int = Field(default=7, ge=0, le=23)
    channels: list[Literal["email", "teams"]] = Field(default_factory=lambda: ["email", "teams"])


class DigestDispatchIn(BaseModel):
    scope: Literal["self", "all_subscribed"] = "self"
    channels: list[Literal["email", "teams"]] | None = None
    schedule: DigestScheduleIn | None = None


def _audit(user: User, action: str, resource: str, detail: dict, status: int = 200) -> None:
    get_audit().record(
        upn=user.upn, role=user.role.value, action=action, resource=resource, status=status, detail=detail
    )


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:48] or "custom_rule"


# --- FR-ALR-02 threshold alert rules -------------------------------------------------------------
@router.get("/rules", summary="FR-ALR-02 Evaluate threshold alert rules in caller's RLS scope")
def list_alert_rules(user: CurrentUser, p: Plat) -> dict:
    rules = alerts_engine.evaluate_rules(p, user)
    return {
        "rules": rules,
        "triggered_count": sum(1 for r in rules if r["enabled"] and r["triggered"]),
        "can_manage": user.role in {Role.GTM_LEAD, Role.SALES_OPS},
    }


@router.post("/rules", status_code=201, summary="FR-ALR-02 Create or update an alert rule (admin only)")
def upsert_alert_rule(body: AlertRuleIn, user: AdminUser, p: Plat) -> dict:
    if body.metric_id not in definitions.METRICS:
        raise HTTPException(422, f"{body.metric_id} is not a registered metric.")
    if not body.channels:
        raise HTTPException(422, "Select at least one delivery channel (email or teams).")
    rule_id = body.rule_id or _slug(body.name)
    existing = get_admin_store().alert_rule(rule_id)
    payload = body.model_dump()
    payload["rule_id"] = rule_id
    if existing and existing["kind"] in ("coverage_drop", "large_deal_slip", "unvalidated_ai_propose"):
        payload["kind"] = existing["kind"]
        payload["unit"] = existing["unit"]
    saved = get_admin_store().upsert_alert_rule(payload, user.upn)
    _audit(
        user,
        "admin.alert.rule",
        f"/api/alerts/rules/{rule_id}",
        {"before": existing, "after": saved},
    )
    evaluated = next(
        (r for r in alerts_engine.evaluate_rules(p, user) if r["rule_id"] == rule_id),
        saved,
    )
    return evaluated


@router.put("/rules/{rule_id}", summary="FR-ALR-02 Update an existing alert rule (admin only)")
def update_alert_rule(rule_id: str, body: AlertRuleIn, user: AdminUser, p: Plat) -> dict:
    body.rule_id = rule_id
    return upsert_alert_rule(body, user, p)


# --- FR-ALR-03 user alert & digest subscriptions -------------------------------------------------
@router.get("/subscriptions", summary="FR-ALR-03 Get caller's alert & digest channel subscriptions")
def get_subscriptions(user: CurrentUser) -> dict:
    return alerts_engine.subscriptions_payload(user)


@router.put("/subscriptions", summary="FR-ALR-03 Update caller's alert & digest channel subscriptions")
def update_subscriptions(body: SubscriptionsUpdateIn, user: CurrentUser) -> dict:
    allowed_ids = {"weekly_digest"} | {
        r["rule_id"] for r in get_admin_store().alert_rules() if alerts_engine.can_see_rule(user, r)
    }
    unknown = [s.target_id for s in body.subscriptions if s.target_id not in allowed_ids]
    if unknown:
        raise HTTPException(422, f"Unknown or restricted subscription target: {', '.join(unknown)}.")
    items = [s.model_dump() for s in body.subscriptions]
    get_admin_store().set_subscriptions(user.upn, items)
    _audit(
        user,
        "admin.alert.subscriptions",
        "/api/alerts/subscriptions",
        {"upn": user.upn, "subscriptions": items},
    )
    return alerts_engine.subscriptions_payload(user)


# --- FR-ALR-01 weekly digest preview, schedule & dispatch ----------------------------------------
@router.get("/digest", summary="FR-ALR-01 Preview weekly digest in caller's (or preview role's) RLS scope")
def preview_digest(
    user: CurrentUser,
    p: Plat,
    preview_role: Annotated[Role | None, Query(description="Admin-only role preview")] = None,
) -> dict:
    target_user = user
    if preview_role is not None:
        if user.role not in {Role.GTM_LEAD, Role.SALES_OPS}:
            raise HTTPException(403, "Only GTM Lead or Sales Ops can preview another persona's digest.")
        target_user = rls.resolve_user(p, preview_role.value)
    return alerts_engine.build_digest(p, target_user)


@router.put("/digest/schedule", summary="FR-ALR-01 Update weekly digest schedule (admin only)")
def update_digest_schedule(body: DigestScheduleIn, user: AdminUser) -> dict:
    if not body.channels:
        raise HTTPException(422, "Select at least one delivery channel (email or teams).")
    before = get_admin_store().digest_config()
    after = get_admin_store().set_digest_config(
        enabled=body.enabled,
        day_of_week=body.day_of_week,
        hour_utc=body.hour_utc,
        channels=list(body.channels),
        user=user.upn,
    )
    _audit(
        user,
        "admin.digest.schedule",
        "/api/alerts/digest/schedule",
        {"before": before, "after": after},
    )
    return after


@router.post("/digest", summary="FR-ALR-01 Dispatch weekly digest (logs delivery run + audit entry)")
def send_digest(
    user: CurrentUser,
    p: Plat,
    body: Annotated[DigestDispatchIn | None, Body()] = None,
) -> dict:
    req = body or DigestDispatchIn()
    store = get_admin_store()

    if req.schedule is not None:
        if user.role not in {Role.GTM_LEAD, Role.SALES_OPS}:
            raise HTTPException(403, "Only GTM Lead or Sales Ops can change the digest schedule.")
        store.set_digest_config(
            enabled=req.schedule.enabled,
            day_of_week=req.schedule.day_of_week,
            hour_utc=req.schedule.hour_utc,
            channels=list(req.schedule.channels),
            user=user.upn,
        )

    if req.scope == "all_subscribed":
        if user.role not in {Role.GTM_LEAD, Role.SALES_OPS}:
            raise HTTPException(403, "Only GTM Lead or Sales Ops can dispatch the digest to all personas.")
        recipients = [rls.resolve_user(p, entry["role"].value) for entry in ref.ROLES]
    else:
        recipients = [user]

    cfg = store.digest_config()
    runs = []
    for recipient in recipients:
        subs = store.subscriptions_for(recipient.upn)
        sub = alerts_engine.subscription_for_target(subs, "weekly_digest", cfg["channels"])
        active_channels = (
            list(req.channels)
            if req.channels is not None
            else [ch for ch in ("email", "teams") if sub.get(ch)]
        )
        if not active_channels:
            continue
        digest = alerts_engine.build_digest(p, recipient)
        run = store.record_digest_run(
            triggered_by=user.upn,
            recipient_upn=recipient.upn,
            recipient_role=recipient.role.value,
            channels=active_channels,
            kpi_count=len(digest["kpis"]),
            stalled_deal_count=digest["stalled_deals"]["total_count"],
            over_capacity_count=digest["over_capacity_architects"]["over_count"],
            triggered_alert_count=len(digest["triggered_alerts"]),
            status="delivered",
        )
        runs.append(run)

    _audit(
        user,
        "admin.digest.send",
        "/api/alerts/digest",
        {"scope": req.scope, "deliveries": len(runs), "runs": runs},
    )
    return {
        "dispatched": len(runs),
        "runs": runs,
        "digest": alerts_engine.build_digest(p, user),
    }
