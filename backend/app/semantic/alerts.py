"""Alerts & weekly digest engine (FR-ALR-01..03).

Every alert rule evaluation and weekly digest runs through `QueryContext` (semantic layer + `rls.py`),
so every persona only sees metrics, deal rows, and architect capacity inside their row-level security
scope. Restricted metrics (`CAP-03`, `PUR-06`) are gated to GTM Lead, Leadership, and Finance.
"""

from __future__ import annotations

from collections.abc import Callable

from app.domain.enums import Role
from app.domain.models import User
from app.platform.admin_store import get_admin_store
from app.platform.db import Platform
from app.schemas.common import MetricResult
from app.semantic import definitions, rls
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.filters import FilterParams
from app.semantic.metrics import acc, cap, exe, mkt, off, par, pip, pur

RESTRICTED_METRICS = {"CAP-03", "PUR-06"}

STATUS_META = {
    "on_track": {"label": "On track", "icon": "●"},
    "watch": {"label": "Watch", "icon": "▲"},
    "off_track": {"label": "Off track", "icon": "◆"},
}

MODULE_LINKS = [
    ("executive", "Executive summary", "/executive"),
    ("pipeline", "Pipeline analysis", "/pipeline"),
    ("pursuits", "Pursuits & wins", "/pursuits"),
    ("offerings", "Offerings & solutions", "/offerings"),
    ("accounts", "Accounts & whitespace", "/accounts"),
    ("partners", "Partner ecosystem", "/partners"),
    ("solutions_capacity", "Solutions capacity", "/solutions-capacity"),
    ("market_signals", "Market signals", "/market-signals"),
]

METRIC_DEEP_LINKS = {
    "EXE": "/executive",
    "PIP": "/pipeline",
    "PUR": "/pursuits",
    "OFF": "/offerings",
    "ACC": "/accounts",
    "PAR": "/partners",
    "CAP": "/solutions-capacity",
    "MKT": "/market-signals",
}

_ALL_FUNCTIONS: dict[str, Callable[[QueryContext], MetricResult]] = {
    "EXE-07": exe.exe_07,
    "EXE-08": exe.exe_08,
    "EXE-09": exe.exe_09,
    **{fn.__name__.upper().replace("_", "-"): fn for fn in exe.KPI_FUNCTIONS},
    **pip.FUNCTIONS,
    **pur.FUNCTIONS,
    **off.FUNCTIONS,
    **acc.FUNCTIONS,
    **par.FUNCTIONS,
    **cap.FUNCTIONS,
    **mkt.FUNCTIONS,
    "CAP-03": cap.cap_03,
    "PUR-06": pur.pur_06,
}


def can_see_metric(user: User, metric_id: str) -> bool:
    if metric_id in RESTRICTED_METRICS and not user.restricted:
        return False
    return metric_id in definitions.METRICS


def can_see_rule(user: User, rule: dict) -> bool:
    return can_see_metric(user, rule["metric_id"])


def _format_value(value: float | None, unit: str) -> str:
    if value is None:
        return "—"
    if unit == "usd":
        return h.fmt_musd(value)
    if unit == "pct":
        return h.fmt_pct(value)
    if unit == "x":
        return f"{value:.2f}×"
    if unit == "days":
        return f"{value:.0f}d"
    if unit == "pts":
        return f"{value:.1f} pts"
    return f"{value:g}"


def _compare(observed: float | None, operator: str, threshold: float) -> bool:
    if observed is None:
        return False
    if operator == "lt":
        return observed < threshold
    if operator == "lte":
        return observed <= threshold
    if operator == "gt":
        return observed > threshold
    if operator == "gte":
        return observed >= threshold
    if operator == "eq":
        return observed == threshold
    return False


def _deep_link_for(metric_id: str) -> str:
    prefix = metric_id.split("-")[0]
    return METRIC_DEEP_LINKS.get(prefix, "/")


def evaluate_rule(ctx: QueryContext, rule: dict) -> dict:
    kind = rule.get("kind", "metric_threshold")
    threshold_val = float(rule["threshold"])
    operator = rule["operator"]
    metric_id = rule["metric_id"]

    if kind == "coverage_drop":
        res = exe.exe_02(ctx)
        observed = res.value
        triggered = _compare(observed, operator, threshold_val)
        summary = (
            f"Pipeline coverage is {_format_value(observed, 'x')} vs "
            f"{_format_value(threshold_val, 'x')} threshold ({res.status_basis})."
        )
        return {
            **rule,
            "triggered": triggered,
            "observed_value": observed,
            "formatted_observed": _format_value(observed, "x"),
            "formatted_threshold": _format_value(threshold_val, "x"),
            "status": "off_track" if triggered else "on_track",
            "status_label": "Triggered" if triggered else "Clear",
            "status_icon": "◆" if triggered else "●",
            "summary": summary,
            "matching_deals": [],
            "deep_link": "/pipeline",
        }

    if kind == "large_deal_slip":
        ar = exe.attention_rules(ctx)
        cond = "o.stage_group = 'open' AND o.tcv_usd >= ? AND (o.days_in_stage > ? OR o.past_dated)"
        cargs = [threshold_val, ar["stalled_days"]]
        where, args = ctx.where(cond, args=cargs)
        agg = ctx.platform.query(
            f"SELECT count(*) AS n, {exe.SUM_TCV} AS tcv FROM mart_opportunity o WHERE {where}",
            args,
        )[0]
        count = int(agg["n"])
        tcv = float(agg["tcv"])
        rows = exe.select_rows(ctx, cond, cargs, limit=10)
        triggered = count > 0
        summary = (
            f"{count} open deal{'s' if count != 1 else ''} ≥ {h.fmt_musd(threshold_val)} "
            f"({h.fmt_musd(tcv)} TCV) stalled (> {ar['stalled_days']}d) or past close date in your scope."
        )
        return {
            **rule,
            "triggered": triggered,
            "observed_value": float(count),
            "observed_tcv": tcv,
            "formatted_observed": f"{count} deals ({h.fmt_musd(tcv)})",
            "formatted_threshold": h.fmt_musd(threshold_val),
            "status": "off_track" if triggered else "on_track",
            "status_label": "Triggered" if triggered else "Clear",
            "status_icon": "◆" if triggered else "●",
            "summary": summary,
            "matching_deals": [
                {
                    "opportunity_id": r.opportunity_id,
                    "name": r.name,
                    "account_name": r.account_name,
                    "stage": r.stage,
                    "tcv_usd": r.tcv,
                    "days_in_stage": r.days_in_stage,
                    "close_date": r.close_date,
                    "flag": r.flag,
                    "lead_practice": r.lead_practice,
                }
                for r in rows
            ],
            "deep_link": "/",
        }

    if kind == "unvalidated_ai_propose":
        cond = (
            "o.stage_group = 'open' AND o.stage IN ('Propose', 'Orals', 'Negotiate') "
            "AND o.ai_led AND coalesce(v.status, '') <> 'Validated'"
        )
        where, args = ctx.where(cond)
        agg = ctx.platform.query(
            f"SELECT count(*) AS n, {exe.SUM_TCV} AS tcv FROM {off.VALIDATION_JOIN} WHERE {where}",
            args,
        )[0]
        count = int(agg["n"])
        tcv = float(agg["tcv"])
        d_where, d_args = ctx.where(cond, detail=True)
        d_rows = ctx.platform.query(
            f"""SELECT o.opportunity_id, o.name, o.account_name, o.stage, o.tcv_usd,
                       o.days_in_stage, o.close_date, o.lead_practice
                FROM {off.VALIDATION_JOIN}
                WHERE {d_where}
                ORDER BY o.tcv_usd DESC, o.opportunity_id LIMIT 10""",
            d_args,
        )
        triggered = _compare(float(count), operator, threshold_val)
        summary = (
            f"{count} AI-led deal{'s' if count != 1 else ''} ({h.fmt_musd(tcv)} TCV) in "
            "Propose, Orals, or Negotiate without completed technical validation."
        )
        return {
            **rule,
            "triggered": triggered,
            "observed_value": float(count),
            "observed_tcv": tcv,
            "formatted_observed": f"{count} deals ({h.fmt_musd(tcv)})",
            "formatted_threshold": f"> {int(threshold_val)} deals",
            "status": "off_track" if triggered else "on_track",
            "status_label": "Triggered" if triggered else "Clear",
            "status_icon": "◆" if triggered else "●",
            "summary": summary,
            "matching_deals": [
                {
                    "opportunity_id": r["opportunity_id"],
                    "name": r["name"],
                    "account_name": r["account_name"],
                    "stage": r["stage"],
                    "tcv_usd": float(r["tcv_usd"]),
                    "days_in_stage": int(r["days_in_stage"]),
                    "close_date": r["close_date"].isoformat(),
                    "flag": "Unvalidated AI-led",
                    "lead_practice": r["lead_practice"],
                }
                for r in d_rows
            ],
            "deep_link": "/offerings",
        }

    fn = _ALL_FUNCTIONS.get(metric_id)
    if fn is None:
        return {
            **rule,
            "triggered": False,
            "observed_value": None,
            "formatted_observed": "—",
            "formatted_threshold": _format_value(threshold_val, rule.get("unit", "count")),
            "status": "on_track",
            "status_label": "Clear",
            "status_icon": "●",
            "summary": f"Metric {metric_id} is not evaluable.",
            "matching_deals": [],
            "deep_link": _deep_link_for(metric_id),
        }

    res = fn(ctx)
    unit = res.unit or rule.get("unit", "count")
    observed = res.value
    triggered = _compare(observed, operator, threshold_val)
    op_symbol = {"lt": "<", "lte": "≤", "gt": ">", "gte": "≥", "eq": "="}.get(operator, operator)
    summary = (
        f"{res.name} ({metric_id}) is {_format_value(observed, unit)} "
        f"(rule triggers when {op_symbol} {_format_value(threshold_val, unit)})."
    )
    return {
        **rule,
        "triggered": triggered,
        "observed_value": observed,
        "formatted_observed": _format_value(observed, unit),
        "formatted_threshold": f"{op_symbol} {_format_value(threshold_val, unit)}",
        "status": "off_track" if triggered else "on_track",
        "status_label": "Triggered" if triggered else "Clear",
        "status_icon": "◆" if triggered else "●",
        "summary": summary,
        "matching_deals": [],
        "deep_link": _deep_link_for(metric_id),
    }


def subscription_for_target(subs: dict[str, dict], target_id: str, default_channels: list[str]) -> dict:
    if target_id in subs:
        return {
            "target_id": target_id,
            "email": subs[target_id]["email"],
            "teams": subs[target_id]["teams"],
        }
    return {
        "target_id": target_id,
        "email": "email" in default_channels,
        "teams": "teams" in default_channels,
    }


def evaluate_rules(platform: Platform, user: User) -> list[dict]:
    store = get_admin_store()
    rules = [r for r in store.alert_rules() if can_see_rule(user, r)]
    subs = store.subscriptions_for(user.upn)
    ctx = QueryContext(platform=platform, params=FilterParams(), user=user)
    out = []
    for r in rules:
        ev = evaluate_rule(ctx, r)
        ev["subscription"] = subscription_for_target(subs, r["rule_id"], r["channels"])
        out.append(ev)
    return out


def subscriptions_payload(user: User) -> dict:
    store = get_admin_store()
    subs = store.subscriptions_for(user.upn)
    rules = [r for r in store.alert_rules() if can_see_rule(user, r)]
    digest_cfg = store.digest_config()
    items = [
        {
            "target_id": "weekly_digest",
            "name": "Weekly GTM executive digest",
            "description": (
                f"Sent every {digest_cfg['day_of_week']} at {digest_cfg['hour_utc']:02d}:00 UTC "
                "with KPI changes, stalled deals, and architect capacity."
            ),
            "kind": "digest",
            "metric_id": "EXE-01",
            **subscription_for_target(subs, "weekly_digest", digest_cfg["channels"]),
        }
    ]
    for r in rules:
        items.append(
            {
                "target_id": r["rule_id"],
                "name": r["name"],
                "description": r["description"],
                "kind": "alert_rule",
                "metric_id": r["metric_id"],
                "severity": r["severity"],
                **subscription_for_target(subs, r["rule_id"], r["channels"]),
            }
        )
    return {"upn": user.upn, "role": user.role.value, "subscriptions": items}


def _scope_label(user: User) -> str:
    return rls.describe(user)


def build_digest(platform: Platform, user: User) -> dict:
    ctx = QueryContext(platform=platform, params=FilterParams(), user=user)
    kpi_fns = (exe.exe_01, exe.exe_02, exe.exe_03, exe.exe_04, exe.exe_05, exe.exe_06)
    kpis = []
    for fn in kpi_fns:
        res = fn(ctx)
        pts = [p.value for p in res.sparkline if p.value is not None]
        delta = (pts[-1] - pts[-2]) if len(pts) >= 2 else None
        st = res.status or "on_track"
        st_meta = STATUS_META.get(st, STATUS_META["on_track"])
        kpis.append(
            {
                "metric_id": res.metric_id,
                "name": res.name,
                "value": res.value,
                "formatted_value": _format_value(res.value, res.unit),
                "unit": res.unit,
                "goal": res.goal,
                "formatted_goal": _format_value(res.goal, res.unit),
                "status": st,
                "status_label": st_meta["label"],
                "status_icon": st_meta["icon"],
                "status_basis": res.status_basis,
                "delta_vs_prior_quarter": delta,
                "formatted_delta": (
                    None
                    if delta is None
                    else (
                        f"+{_format_value(delta, res.unit)}" if delta >= 0 else _format_value(delta, res.unit)
                    )
                ),
                "deep_link": "/executive",
            }
        )

    # Stalled / attention deals (EXE-10) in recipient's RLS detail scope
    cond, cargs = exe.attention_condition(ctx)
    where, args = ctx.where(cond, args=cargs)
    agg = platform.query(
        f"SELECT count(*) AS n, {exe.SUM_TCV} AS tcv FROM mart_opportunity o WHERE {where}",
        args,
    )[0]
    stalled_rows = exe.select_rows(ctx, cond, cargs, limit=8)
    other = exe.aggregated_other(ctx, cond, cargs)
    stalled_deals = [
        {
            "opportunity_id": r.opportunity_id,
            "name": r.name,
            "account_name": r.account_name,
            "stage": r.stage,
            "tcv_usd": r.tcv,
            "formatted_tcv": h.fmt_musd(r.tcv),
            "days_in_stage": r.days_in_stage,
            "close_date": r.close_date,
            "flag": r.flag,
            "lead_practice": r.lead_practice,
            "owner_name": r.owner_name,
        }
        for r in stalled_rows
    ]

    # Over-capacity architects (CAP-01) in recipient's RLS scope
    cap01 = cap.cap_01(ctx)
    over_capacity = [
        {
            "resource_id": r["resource_id"],
            "architect": r["architect"],
            "open_pursuits": int(r["open_pursuits"]),
            "tcv_usd": float(r["tcv"]),
            "formatted_tcv": h.fmt_musd(float(r["tcv"])),
            "band": r["band"],
        }
        for r in cap01.breakdown
        if r["band"] == "off_track"
    ]
    stretched_architects = [
        {
            "resource_id": r["resource_id"],
            "architect": r["architect"],
            "open_pursuits": int(r["open_pursuits"]),
            "tcv_usd": float(r["tcv"]),
            "formatted_tcv": h.fmt_musd(float(r["tcv"])),
            "band": r["band"],
        }
        for r in cap01.breakdown
        if r["band"] == "watch"
    ]
    healthy_count = sum(1 for r in cap01.breakdown if r["band"] == "on_track")

    # Active triggered alerts for this recipient
    evaluated_rules = evaluate_rules(platform, user)
    triggered_alerts = [r for r in evaluated_rules if r["enabled"] and r["triggered"]]

    # Accessible dashboard links for this recipient
    allowed_modules = set(user.modules)
    # `path` is the SPA route the frontend links to; `href` kept for the email/Teams bodies.
    links = [
        {"module": mod, "label": label, "href": href, "path": href}
        for mod, label, href in MODULE_LINKS
        if mod in allowed_modules
    ]

    scope_desc = _scope_label(user)
    subject = (
        f"[Moment GTM Digest] {ctx.period.label} — "
        f"{len(triggered_alerts)} active alert{'s' if len(triggered_alerts) != 1 else ''}, "
        f"{int(agg['n'])} attention deal{'s' if int(agg['n']) != 1 else ''}"
    )

    kpi_lines = [
        f"  {k['status_icon']} {k['status_label']:9s} | {k['metric_id']} {k['name']}: "
        f"{k['formatted_value']} (goal {k['formatted_goal']})"
        for k in kpis
    ]
    deal_lines = [
        f"  • {d['name']} ({d['account_name']}) — {d['formatted_tcv']} · {d['stage']} · "
        f"{d['flag']} ({d['days_in_stage']}d in stage)"
        for d in stalled_deals[:5]
    ] or ["  • None in your detail scope."]
    arch_lines = [
        f"  • {a['architect']} — {a['open_pursuits']} open pursuits ({a['formatted_tcv']})"
        for a in over_capacity
    ] or ["  • No architects over capacity in your scope."]
    link_lines = [f"  • {lk['label']}: {lk['href']}" for lk in links]

    email_body = "\n".join(
        [
            f"Recipient: {user.name} <{user.upn}> ({user.role.value})",
            f"RLS Scope: {scope_desc}",
            f"Period: {ctx.period.label} (as of {ctx.today.isoformat()})",
            "",
            "1. EXECUTIVE KPI SUMMARY (EXE-01..06)",
            *kpi_lines,
            "",
            f"2. DEALS NEEDING ATTENTION (EXE-10 — {int(agg['n'])} total, {h.fmt_musd(float(agg['tcv']))})",
            *deal_lines,
            "",
            f"3. SOLUTIONS ARCHITECT CAPACITY (CAP-01 — {len(over_capacity)} over capacity)",
            *arch_lines,
            "",
            "4. DIRECT DASHBOARD LINKS",
            *link_lines,
        ]
    )

    store = get_admin_store()
    cfg = store.digest_config()
    subs = store.subscriptions_for(user.upn)
    sub = subscription_for_target(subs, "weekly_digest", cfg["channels"])

    return {
        "recipient": {
            "upn": user.upn,
            "name": user.name,
            "display_name": user.name,
            "role": user.role.value,
            "role_label": user.role_label,
            "practice": user.practice,
            "scope": scope_desc,
        },
        "period": ctx.period.to_info(),
        "as_of": ctx.today.isoformat(),
        "schedule": cfg,
        "subscription": sub,
        "kpis": kpis,
        "stalled_deals": {
            "metric_id": "EXE-10",
            "total_count": int(agg["n"]),
            "total_tcv": float(agg["tcv"]),
            "formatted_total_tcv": h.fmt_musd(float(agg["tcv"])),
            "formatted_tcv": h.fmt_musd(float(agg["tcv"])),
            "deep_link": METRIC_DEEP_LINKS["EXE"],
            "deals": stalled_deals,
            "aggregated_other": other.model_dump() if other else None,
        },
        "over_capacity_architects": {
            "metric_id": "CAP-01",
            "over_count": len(over_capacity),
            "stretched_count": len(stretched_architects),
            "healthy_count": healthy_count,
            "healthy_max": int(cap01.meta.get("healthy_max", 4)),
            "callout": cap01.narrative,
            "narrative": cap01.narrative,
            "deep_link": METRIC_DEEP_LINKS["CAP"],
            "architects": over_capacity,
            "stretched": stretched_architects,
        },
        "triggered_alerts": triggered_alerts,
        "dashboard_links": links,
        "email_preview": {
            "to": user.upn,
            "subject": subject,
            "body": email_body,
            "body_markdown": f"# Moment GTM Weekly Digest\n\n{email_body}",
        },
        "teams_preview": {
            "channel": "#moment-gtm-leadership",
            "title": subject,
            "subtitle": f"Scoped to {scope_desc} · As of {ctx.today.isoformat()}",
            "summary": f"Scoped to {scope_desc} · As of {ctx.today.isoformat()}",
            "facts": [
                {"name": "Active alerts", "value": str(len(triggered_alerts))},
                {
                    "name": "Deals needing attention",
                    "value": f"{int(agg['n'])} ({h.fmt_musd(float(agg['tcv']))})",
                },
                {"name": "Over-capacity architects", "value": str(len(over_capacity))},
            ],
            "actions": links,
        },
        "history": store.digest_runs(
            recipient_upn=None if user.role in {Role.GTM_LEAD, Role.SALES_OPS} else user.upn
        ),
    }
