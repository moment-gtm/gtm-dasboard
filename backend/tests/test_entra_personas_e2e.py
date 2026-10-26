"""End-to-end verification test for Microsoft Entra ID authentication and persona access.

Verifies:
1. Legacy accounts ('balaji', 'deepak', 'bindya') are rejected (401).
2. All 9 official Entra personas can authenticate via /api/auth/entra/login.
3. Bearer token claims are validated by /api/auth/me.
4. Each designated persona can query their authorized dashboard modules.
5. Strict RLS enforcement: Restricted metrics (PUR-06) permitted for Finance/GTM Lead, forbidden (403) for Sales Ops.
6. Solutions Lead access denied (403) to Executive summary per RSD role matrix, while permitted to Solutions Capacity.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.data import reference_data as ref

client = TestClient(app)


def _login(upn: str):
    """Password login with the persona-specific Entra password (passwordless SSO is off by default)."""
    first = upn.split(".")[0].capitalize()
    return client.post("/api/auth/entra/login", json={"upn": upn, "password": f"Moment#2026${first}!GTM"})


def test_legacy_users_rejected():
    for user in ["balaji", "deepak", "bindya"]:
        res = client.post("/api/auth/login", json={"username": user, "password": "AnyPassword123!"})
        assert res.status_code == 401
        assert "Invalid credentials" in res.json()["detail"]


def test_all_nine_entra_personas_login_and_me():
    assert len(ref.PERSONA_USERS) >= 9
    for p in ref.PERSONA_USERS:
        upn = p["upn"]
        resp = _login(upn)
        assert resp.status_code == 200, f"Login failed for {upn}: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        token = data["access_token"]
        user = data["user"]
        assert user["upn"] == upn
        assert user["role"] == p["role"].value

        # Verify /api/auth/me resolves the user with this Bearer token
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        me_user = me_resp.json()
        assert me_user["upn"] == upn
        assert me_user["role"] == p["role"].value
        assert me_user.get("group_name", "").startswith("GTM-Dashboard-")


def test_designated_users_dashboard_modules():
    # 1. Jordan Avery (GTM Lead) - All modules
    jordan_resp = _login("jordan.avery@moment.example")
    jordan_token = jordan_resp.json()["access_token"]
    h_jordan = {"Authorization": f"Bearer {jordan_token}"}

    assert client.get("/api/executive/kpis", headers=h_jordan).status_code == 200
    assert client.get("/api/executive/runway", headers=h_jordan).status_code == 200
    assert client.get("/api/pipeline/funnel", headers=h_jordan).status_code == 200
    assert client.get("/api/pursuits/win-rate", headers=h_jordan).status_code == 200
    assert client.get("/api/offerings/by-offering", headers=h_jordan).status_code == 200
    assert client.get("/api/accounts/penetration", headers=h_jordan).status_code == 200
    assert client.get("/api/partners/pipeline", headers=h_jordan).status_code == 200
    assert client.get("/api/capacity/architect-load", headers=h_jordan).status_code == 200
    assert client.get("/api/market/thought-leadership", headers=h_jordan).status_code == 200
    assert client.get("/api/admin/dq/completeness", headers=h_jordan).status_code == 200

    # 2. Sam Okafor (Leadership)
    sam_resp = _login("sam.okafor@moment.example")
    h_sam = {"Authorization": f"Bearer {sam_resp.json()['access_token']}"}
    assert client.get("/api/executive/kpis", headers=h_sam).status_code == 200
    assert client.get("/api/pipeline/funnel", headers=h_sam).status_code == 200

    # 3. Lena Kovacs (Finance) - PUR-06 Margin allowed
    lena_resp = _login("lena.kovacs@moment.example")
    h_lena = {"Authorization": f"Bearer {lena_resp.json()['access_token']}"}
    assert client.get("/api/pursuits/margin", headers=h_lena).status_code == 200

    # 4. Ravi Iyer (Practice Lead - DxP)
    ravi_resp = _login("ravi.iyer@moment.example")
    h_ravi = {"Authorization": f"Bearer {ravi_resp.json()['access_token']}"}
    assert client.get("/api/pipeline/funnel", headers=h_ravi).status_code == 200
    assert client.get("/api/capacity/architect-load", headers=h_ravi).status_code == 200

    # 5. Asha Menon (Client Partner)
    asha_resp = _login("asha.menon@moment.example")
    h_asha = {"Authorization": f"Bearer {asha_resp.json()['access_token']}"}
    assert client.get("/api/accounts/penetration", headers=h_asha).status_code == 200

    # 6. Noah Berg (Alliance Manager - Adobe)
    noah_resp = _login("noah.berg@moment.example")
    h_noah = {"Authorization": f"Bearer {noah_resp.json()['access_token']}"}
    assert client.get("/api/partners/pipeline", headers=h_noah).status_code == 200

    # 7. Mia Chen (Marketing)
    mia_resp = _login("mia.chen@moment.example")
    h_mia = {"Authorization": f"Bearer {mia_resp.json()['access_token']}"}
    assert client.get("/api/market/thought-leadership", headers=h_mia).status_code == 200

    # 8. Omar Haddad (Sales Ops) - Restricted PUR-06 margin forbidden (403)
    omar_resp = _login("omar.haddad@moment.example")
    h_omar = {"Authorization": f"Bearer {omar_resp.json()['access_token']}"}
    assert client.get("/api/admin/dq/completeness", headers=h_omar).status_code == 200
    assert client.get("/api/pursuits/margin", headers=h_omar).status_code == 403

    # 9. Kai Watanabe (Solutions Lead) - Executive forbidden (403), Solutions Capacity allowed (200)
    kai_resp = _login("kai.watanabe@moment.example")
    h_kai = {"Authorization": f"Bearer {kai_resp.json()['access_token']}"}
    assert client.get("/api/executive/kpis", headers=h_kai).status_code == 403
    assert client.get("/api/capacity/architect-load", headers=h_kai).status_code == 200
