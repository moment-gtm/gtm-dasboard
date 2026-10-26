"""Tests for Microsoft Entra authentication endpoints: login, personas, me, and logout."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_auth_legacy_users_removed():
    """Verify legacy Balaji, Deepak, and Bindya accounts are removed and rejected."""
    legacy = ["balaji", "deepak", "bindya"]
    for user in legacy:
        resp = client.post("/api/auth/login", json={"username": user, "password": "AnyPassword!"})
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]


def test_auth_login_invalid_credentials():
    resp = client.post(
        "/api/auth/login",
        json={"username": "jordan.avery@moment.example", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


def test_auth_entra_personas_endpoint():
    """Verify the /api/auth/entra/personas endpoint lists the official Entra personas."""
    resp = client.get("/api/auth/entra/personas")
    assert resp.status_code == 200
    personas = resp.json()
    assert len(personas) >= 9
    upns = {p["upn"] for p in personas}
    assert "jordan.avery@moment.example" in upns
    assert "sam.okafor@moment.example" in upns
    assert "omar.haddad@moment.example" in upns


def test_auth_login_all_entra_personas():
    """Verify authentication for official Entra personas via UPN."""
    test_cases = [
        ("jordan.avery@moment.example", "Moment#2026$Jordan!GTM", "Jordan Avery", "gtm_lead"),
        ("sam.okafor@moment.example", "Moment#2026$Sam!GTM", "Sam Okafor", "leadership"),
        ("lena.kovacs@moment.example", "Moment#2026$Lena!GTM", "Lena Kovacs", "finance"),
        ("ravi.iyer@moment.example", "Moment#2026$Ravi!GTM", "Ravi Iyer", "practice_lead"),
        ("asha.menon@moment.example", "Moment#2026$Asha!GTM", "Asha Menon", "client_partner"),
        ("omar.haddad@moment.example", "Moment#2026$Omar!GTM", "Omar Haddad", "sales_ops"),
        ("balaji.parthasarathy@moment.example", "Moment#2026$Balaji!GTM", "Balaji Parthasarathy", "gtm_lead"),
        ("bindya.somaraj@moment.example", "Moment#2026$Bindya!GTM", "Bindya Somaraj", "gtm_lead"),
        ("deepak.narayanan@moment.example", "Moment#2026$Deepak!GTM", "Deepak Narayanan", "leadership"),
    ]
    for upn, pwd, expected_name, expected_role in test_cases:
        resp = client.post("/api/auth/login", json={"username": upn, "password": pwd})
        assert resp.status_code == 200, f"Login failed for {upn}: {resp.text}"
        data = resp.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["name"] == expected_name
        assert data["user"]["role"] == expected_role
        assert data["user"]["upn"] == upn


@pytest.fixture
def override():
    """Patch a field on the frozen Settings dataclass for one test (restored on teardown)."""
    saved: dict[str, object] = {}

    def _set(name: str, value) -> None:
        saved.setdefault(name, getattr(settings, name))
        object.__setattr__(settings, name, value)

    yield _set
    for name, original in saved.items():
        object.__setattr__(settings, name, original)

JORDAN = {"upn": "jordan.avery@moment.example", "password": "Moment#2026$Jordan!GTM"}


def test_auth_entra_login_with_password():
    """Verify /api/auth/entra/login authenticates a persona with its password."""
    resp = client.post("/api/auth/entra/login", json=JORDAN)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["name"] == "Jordan Avery"
    assert data["user"]["group_name"] == "GTM-Dashboard-GTMLead"


def test_auth_entra_login_requires_password():
    """Passwordless / wrong-password login is refused unless demo SSO is explicitly enabled."""
    upn = JORDAN["upn"]
    assert client.post("/api/auth/entra/login", json={"upn": upn}).status_code == 401
    assert client.post("/api/auth/entra/login", json={"upn": upn, "password": "nope"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": upn}).status_code == 401


def test_auth_entra_passwordless_demo_flag(override):
    override("allow_passwordless_login", True)
    resp = client.post("/api/auth/entra/login", json={"upn": JORDAN["upn"]})
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "gtm_lead"


def test_auth_personas_do_not_leak_passwords():
    for p in client.get("/api/auth/entra/personas").json():
        assert "password_hint" not in p


def test_reference_roles_lists_only_own_persona():
    token = client.post("/api/auth/entra/login", json=JORDAN).json()["access_token"]
    resp = client.get("/api/reference/roles", headers={"Authorization": f"Bearer {token}"})
    assert [p["role"] for p in resp.json()] == ["gtm_lead"]


def test_reference_roles_lists_all_when_switcher_enabled(override):
    override("enable_persona_switcher", True)
    resp = client.get("/api/reference/roles", headers={"X-Mock-Role": "gtm_lead"})
    assert len(resp.json()) >= 9


def test_token_wins_over_mock_role_header():
    token = client.post("/api/auth/entra/login", json=JORDAN).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Mock-Role": "finance"}
    assert client.get("/api/me", headers=headers).json()["role"] == "gtm_lead"
    assert client.get("/api/me?role=finance", headers={"Authorization": f"Bearer {token}"}).json()[
        "role"
    ] == ("gtm_lead")


def test_mock_role_header_disabled(override):
    override("allow_mock_identity", False)
    assert client.get("/api/me", headers={"X-Mock-Role": "finance"}).status_code == 401
    assert client.get("/api/me?role=finance").status_code == 401


def test_auth_me_and_logout():
    # Login as Jordan Avery (GTM Lead)
    login_resp = client.post("/api/auth/entra/login", json=JORDAN)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Verify /api/auth/me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    user_info = me_resp.json()
    assert user_info["name"] == "Jordan Avery"
    assert user_info["role"] == "gtm_lead"
    assert user_info["upn"] == "jordan.avery@moment.example"

    # Verify API request using Bearer token (e.g. /api/me)
    profile_resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_resp.status_code == 200
    assert profile_resp.json()["role"] == "gtm_lead"

    # Logout
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # /api/auth/me should now fail
    me_after_logout = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after_logout.status_code == 401
