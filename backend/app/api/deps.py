"""API building blocks: current user, module/role gates, filter params, query context."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, Request

from app.config import settings
from app.domain.enums import Role
from app.domain.models import User
from app.platform.audit import get_audit
from app.platform.auth import get_user_from_token
from app.platform.db import Platform, get_platform
from app.semantic.context import QueryContext
from app.semantic.filters import FilterParams
from app.semantic.rls import UnknownRole, resolve_user

DEFAULT_ROLE = Role.GTM_LEAD.value


def platform_dep() -> Platform:
    return get_platform()


def current_user(
    platform: Annotated[Platform, Depends(platform_dep)],
    authorization: Annotated[str | None, Header()] = None,
    x_mock_role: Annotated[str | None, Header()] = None,
    role: Annotated[str | None, Query(description="Mock role for file downloads")] = None,
) -> User:
    """Mock SSO (NFR-04 in production: Entra ID OIDC).

    A valid Bearer token is the identity and always wins. The unauthenticated X-Mock-Role header /
    ?role= query are honoured only in mock_entra mode with GTM_ALLOW_MOCK_IDENTITY enabled (tests,
    load scripts, export downloads); otherwise a request without a valid token is rejected.
    """
    auth_identifier = None
    if authorization:
        parts = authorization.split()
        token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else authorization
        session_user = get_user_from_token(token)
        if session_user:
            auth_identifier = session_user.upn

    if auth_identifier:
        resolved_target = auth_identifier
    elif settings.mock_identity_enabled:
        resolved_target = x_mock_role or role or DEFAULT_ROLE
    else:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        return resolve_user(platform, resolved_target)
    except UnknownRole as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


CurrentUser = Annotated[User, Depends(current_user)]


def filter_params(params: Annotated[FilterParams, Query()]) -> FilterParams:
    # A query-parameter model must be the only query param of its function, so routes with
    # their own query params (paging, metric_id, ...) receive it through this dependency.
    return params


Filters = Annotated[FilterParams, Depends(filter_params)]


def require_module(module: str):
    def check(user: CurrentUser) -> User:
        if not user.can_access(module):
            raise HTTPException(
                status_code=403,
                detail=f"{user.role_label} does not have access to the {module.replace('_', ' ')} module.",
            )
        return user

    return check


def require_role(*roles: Role):
    """Gate for role-specific endpoints; restricted metrics use `guard_restricted` below."""

    def check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(roles)}")
        return user

    return check


def executive_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, Depends(require_module("executive"))],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


ExecutiveContext = Annotated[QueryContext, Depends(executive_context)]


def pipeline_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, Depends(require_module("pipeline"))],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


PipelineContext = Annotated[QueryContext, Depends(pipeline_context)]


def pursuits_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, Depends(require_module("pursuits"))],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


PursuitsContext = Annotated[QueryContext, Depends(pursuits_context)]


_OFFERINGS_USER = Depends(require_module("offerings"))
_ACCOUNTS_USER = Depends(require_module("accounts"))
_PARTNERS_USER = Depends(require_module("partners"))


def offerings_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, _OFFERINGS_USER],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


def accounts_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, _ACCOUNTS_USER],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


def partners_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, _PARTNERS_USER],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


OfferingsContext = Annotated[QueryContext, Depends(offerings_context)]
AccountsContext = Annotated[QueryContext, Depends(accounts_context)]
PartnersContext = Annotated[QueryContext, Depends(partners_context)]


def guard_restricted(user: User, metric_id: str, resource: str) -> None:
    """Restricted metrics (PUR-06, CAP-03): 403 for other roles, and every attempt is audited (NFR-07)."""
    allowed = user.restricted
    get_audit().record(
        upn=user.upn,
        role=user.role.value,
        action="restricted.access" if allowed else "restricted.denied",
        resource=f"{metric_id} {resource}",
        status=200 if allowed else 403,
    )
    if not allowed:
        raise HTTPException(
            status_code=403, detail=f"{metric_id} is restricted; {user.role_label} cannot view it."
        )


_CAPACITY_USER = Depends(require_module("solutions_capacity"))


def capacity_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, _CAPACITY_USER],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


def cost_of_sale_context(
    request: Request,
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, _CAPACITY_USER],
) -> QueryContext:
    guard_restricted(user, "CAP-03", request.url.path)
    return QueryContext(platform=platform, params=params, user=user)


def margin_context(
    request: Request,
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, Depends(require_module("pursuits"))],
) -> QueryContext:
    guard_restricted(user, "PUR-06", request.url.path)
    return QueryContext(platform=platform, params=params, user=user)


CapacityContext = Annotated[QueryContext, Depends(capacity_context)]
CostOfSaleContext = Annotated[QueryContext, Depends(cost_of_sale_context)]
MarginContext = Annotated[QueryContext, Depends(margin_context)]

_MARKET_SIGNALS_USER = Depends(require_module("market_signals"))


def market_signals_context(
    params: Filters,
    platform: Annotated[Platform, Depends(platform_dep)],
    user: Annotated[User, _MARKET_SIGNALS_USER],
) -> QueryContext:
    return QueryContext(platform=platform, params=params, user=user)


MarketSignalsContext = Annotated[QueryContext, Depends(market_signals_context)]
