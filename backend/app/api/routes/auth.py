"""Authentication endpoints: Microsoft Entra login, directory personas, me, and logout."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings
from app.platform.auth import (
    AuthUser,
    create_session,
    find_persona,
    get_all_personas,
    get_user_from_token,
    revoke_session,
    verify_credentials,
)

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(description="Entra UPN, email, or persona username")
    password: str | None = Field(default=None, description="Password (optional for Entra SSO)")


class EntraLoginRequest(BaseModel):
    upn: str = Field(description="Microsoft Entra User Principal Name (UPN)")
    password: str | None = Field(default=None, description="Password (optional for Entra SSO)")


class UserResponse(BaseModel):
    username: str
    upn: str
    name: str
    email: str
    role: str
    role_label: str
    job_title: str = ""
    group_name: str = ""
    scope_type: str = "all"
    scope_value: str | None = None
    description: str = ""


class PersonaItem(BaseModel):
    upn: str
    username: str
    name: str
    email: str
    role: str
    role_label: str
    job_title: str
    group_name: str
    scope_type: str
    scope_value: str | None = None
    description: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


def _to_user_response(user: AuthUser) -> UserResponse:
    return UserResponse(
        username=user.username,
        upn=user.upn,
        name=user.name,
        email=user.email,
        role=user.role,
        role_label=user.role_label,
        job_title=user.job_title,
        group_name=user.group_name,
        scope_type=user.scope_type,
        scope_value=user.scope_value,
        description=user.description,
    )


def _extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return authorization


@router.get("/api/auth/entra/personas", response_model=list[PersonaItem])
def list_personas() -> list[PersonaItem]:
    """List available Microsoft Entra personas for prototype directory selection."""
    personas = get_all_personas()
    return [
        PersonaItem(
            upn=p.upn,
            username=p.username,
            name=p.name,
            email=p.email,
            role=p.role,
            role_label=p.role_label,
            job_title=p.job_title,
            group_name=p.group_name,
            scope_type=p.scope_type,
            scope_value=p.scope_value,
            description=p.description,
        )
        for p in personas
    ]


@router.post("/api/auth/entra/login", response_model=LoginResponse)
def entra_login(payload: EntraLoginRequest) -> LoginResponse:
    """Authenticate via Microsoft Entra ID (UPN + password).

    A password is required. Passwordless / any-password simulated SSO is a demo-only behaviour,
    available solely when GTM_ALLOW_PASSWORDLESS_LOGIN=1 in mock_entra mode.
    """
    clean_pwd = payload.password.strip() if payload.password and payload.password.strip() else None
    user = verify_credentials(payload.upn, clean_pwd)
    if not user:
        persona = find_persona(payload.upn)
        if persona and settings.auth_mode == "mock_entra" and settings.allow_passwordless_login:
            user = persona
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft Entra user not found or credentials invalid. Check the UPN and password.",
            )
    token = create_session(user)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=_to_user_response(user),
    )


@router.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    """Standard login endpoint (accepts UPN, corporate email, or username)."""
    user = verify_credentials(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please select an active Microsoft Entra persona.",
        )
    token = create_session(user)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=_to_user_response(user),
    )


@router.get("/api/auth/me", response_model=UserResponse)
def me(authorization: Annotated[str | None, Header()] = None) -> UserResponse:
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
    return _to_user_response(user)


@router.post("/api/auth/logout")
def logout(authorization: Annotated[str | None, Header()] = None) -> dict[str, str]:
    token = _extract_token(authorization)
    if token:
        revoke_session(token)
    return {"message": "Logged out successfully"}
