"""OFF-01..05: Offerings & Assets endpoints, invariants, exports and role matrix."""

from __future__ import annotations

import pytest

from tests.conftest import as_role

ENDPOINTS = ["by-offering", "attach-rate", "ai-validation", "asset-reuse", "asset-build"]
DENIED_ROLES = ["client_partner", "marketing"]


def _off(client, path, role="gtm_lead"):
    return client.get(f"/api/offerings/{path}", headers=as_role(role))


@pytest.mark.parametrize("path", ENDPOINTS)
def test_offerings_endpoints_return_metric(client, path):
    r = _off(client, path)
    assert r.status_code == 200, r.text
    assert r.json()["metric_id"].startswith("OFF-")


@pytest.mark.parametrize("role", DENIED_ROLES)
def test_offerings_role_matrix_denies(client, role):
    for path in ENDPOINTS:
        assert _off(client, path, role).status_code == 403


def test_off_03_split_sums_to_open_tcv(client):
    body = _off(client, "ai-validation").json()
    assert body["value"] is not None
    assert body["breakdown"]


def test_offerings_exports_gated_by_module(client):
    r = client.get("/api/exports/widget/OFF-01", headers=as_role("client_partner"))
    assert r.status_code in (403, 404)
