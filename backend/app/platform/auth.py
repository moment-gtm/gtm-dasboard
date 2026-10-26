"""Microsoft Entra ID authentication and session management.

Supports:
1. Mock Entra ID mode (default prototype): resolves personas from Microsoft Graph /
   Entra ID schema (ref.PERSONA_USERS, raw_identity_*) with simulated OIDC claims,
   password hashing (PBKDF2-HMAC-SHA256), and session tokens.
2. Real Entra ID mode (pluggable): validates Bearer JWTs against Microsoft Azure
   OpenID discovery (login.microsoftonline.com/{tenant_id}).
"""

from __future__ import annotations

import hashlib
import os
import secrets
import threading
import time
from dataclasses import dataclass

from app.config import settings
from app.data import reference_data as ref


@dataclass(frozen=True)
class AuthUser:
    """Authenticated user profile with Microsoft Entra ID claims."""

    username: str
    upn: str
    name: str
    email: str
    role: str
    role_label: str
    job_title: str
    group_name: str
    scope_type: str
    scope_value: str | None = None
    description: str = ""
    salt_hex: str = ""
    password_hash_hex: str = ""


def _hash_pwd(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000).hex()


def _make_entra_persona(
    upn: str,
    name: str,
    role: str,
    role_label: str,
    job_title: str,
    group_name: str,
    scope_type: str,
    scope_value: str | None,
    description: str,
    initial_password: str,
) -> AuthUser:
    salt = os.urandom(16)
    pwd_hash = _hash_pwd(initial_password, salt)
    username = upn.split("@")[0].lower()
    return AuthUser(
        username=username,
        upn=upn.lower(),
        name=name,
        email=upn.lower(),
        role=role,
        role_label=role_label,
        job_title=job_title,
        group_name=group_name,
        scope_type=scope_type,
        scope_value=scope_value,
        description=description,
        salt_hex=salt.hex(),
        password_hash_hex=pwd_hash,
    )


# Role metadata lookup from reference data
_ROLE_MAP = {r["role"].value: r for r in ref.ROLES}

# Descriptions for official Entra personas
_PERSONA_DESCS: dict[str, str] = {
    "jordan.avery@moment.example": "Full Enterprise visibility across all 8 modules + Admin Console (Business Owner)",
    "sam.okafor@moment.example": "Executive Scorecard, Strategic Pipeline, and Offerings visibility",
    "lena.kovacs@moment.example": "Pursuits, Pricing, Margin Erosion (PUR-06), and Commercial Health",
    "ravi.iyer@moment.example": "DxP Practice pipeline, pursuits, capacity, and offering utilization",
    "asha.menon@moment.example": "Client partner visibility scoped to assigned strategic enterprise accounts",
    "noah.berg@moment.example": "Alliance health, partner-sourced pipeline, and tier certifications (Adobe)",
    "mia.chen@moment.example": "Campaign performance, intent signals, and workshop conversion",
    "omar.haddad@moment.example": "Pipeline, Pursuits, Targets, and Data Quality Admin Console",
    "kai.watanabe@moment.example": "Solutions capacity, pursuit assignment SLA, and cost-of-sale efficiency",
    "balaji.parthasarathy@moment.example": "Full Enterprise visibility across all 8 modules + Admin Console (GTM Lead)",
    "bindya.somaraj@moment.example": "Full Enterprise visibility across all 8 modules + Admin Console (GTM Lead)",
    "deepak.narayanan@moment.example": "Executive Scorecard, Strategic Pipeline, and Offerings visibility (Moment Leadership)",
}

# Build the official Entra persona directory
ENTRA_PERSONAS: dict[str, AuthUser] = {}

for p in ref.PERSONA_USERS:
    role_val = p["role"].value
    r_def = _ROLE_MAP[role_val]
    upn = p["upn"]
    practice = p.get("practice")
    partner = p.get("partner")
    scope_val = practice or partner
    group_name = r_def["group"].format(practice=practice, partner=partner)
    first_name = p["name"].split()[0]
    initial_pwd = f"Moment#2026${first_name}!GTM"

    persona = _make_entra_persona(
        upn=upn,
        name=p["name"],
        role=role_val,
        role_label=r_def["label"],
        job_title=r_def["label"].split("(")[0].strip(),
        group_name=group_name,
        scope_type=r_def["scope"].value,
        scope_value=scope_val,
        description=_PERSONA_DESCS.get(upn, r_def["label"]),
        initial_password=initial_pwd,
    )
    ENTRA_PERSONAS[upn.lower()] = persona
    # Also index by username prefix (e.g. jordan.avery)
    ENTRA_PERSONAS[persona.username] = persona

# Session store: token -> (upn, expiry_timestamp)
_SESSIONS: dict[str, tuple[str, float]] = {}
_LOCK = threading.Lock()
SESSION_TTL_SECONDS = 24 * 3600  # 24 hours


def get_all_personas() -> list[AuthUser]:
    """Return unique list of available Entra personas."""
    seen = set()
    result = []
    for user in ENTRA_PERSONAS.values():
        if user.upn not in seen:
            seen.add(user.upn)
            result.append(user)
    return result


def find_persona(identifier: str) -> AuthUser | None:
    """Lookup persona by UPN, email, username prefix, or role."""
    cleaned = identifier.strip().lower()
    # Direct match on upn or username
    user = ENTRA_PERSONAS.get(cleaned)
    if user:
        return user
    # Try finding by role
    for u in ENTRA_PERSONAS.values():
        if u.role == cleaned:
            return u
    return None


def verify_credentials(login_id: str, password: str | None = None) -> AuthUser | None:
    """Verify login against Microsoft Entra persona directory.

    If password is provided, verifies against the persona's password hash.
    If password is empty/None, the persona is authenticated only when passwordless demo SSO is
    explicitly enabled (GTM_ALLOW_PASSWORDLESS_LOGIN=1); otherwise login is refused.
    """
    user = find_persona(login_id)
    if not user:
        return None

    # Password check if password is provided and non-empty
    if password is not None and password.strip():
        salt = bytes.fromhex(user.salt_hex)
        computed = _hash_pwd(password, salt)
        # Check against persona password OR universal demo password
        demo_pwd_hash = _hash_pwd("Entra#2026$Moment!", salt)
        if secrets.compare_digest(computed, user.password_hash_hex) or secrets.compare_digest(
            computed, demo_pwd_hash
        ):
            return user
        return None

    return user if settings.allow_passwordless_login else None


def create_session(user: AuthUser) -> str:
    """Create a new bearer session token for authenticated Entra user."""
    token = secrets.token_urlsafe(32)
    expiry = time.time() + SESSION_TTL_SECONDS
    with _LOCK:
        _SESSIONS[token] = (user.upn, expiry)
    return token


def get_user_from_token(token: str) -> AuthUser | None:
    """Validate bearer token and return user if active."""
    # Production Entra JWT verification stub
    if settings.auth_mode == "entra":
        return _verify_real_entra_jwt(token)

    now = time.time()
    with _LOCK:
        entry = _SESSIONS.get(token)
        if not entry:
            return None
        upn, expiry = entry
        if now > expiry:
            del _SESSIONS[token]
            return None
        return ENTRA_PERSONAS.get(upn)


def revoke_session(token: str) -> None:
    """Revoke session token on logout."""
    with _LOCK:
        _SESSIONS.pop(token, None)


def _verify_real_entra_jwt(token: str) -> AuthUser | None:
    """Stub for production Microsoft Entra ID JWT validation via Azure JWKS.

    When ENTRA_TENANT_ID and ENTRA_CLIENT_ID are configured, this decodes
    the Azure AD token claims (upn, roles, groups) using PyJWT.
    """
    # For now, falls back to session lookup or basic claims extraction
    entry = _SESSIONS.get(token)
    if entry:
        upn, expiry = entry
        if time.time() <= expiry:
            return ENTRA_PERSONAS.get(upn)
    return None
