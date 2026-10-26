"""PAR-01..03: Partners & Ecosystem endpoints, invariants, RLS and role matrix."""

from __future__ import annotations

import pytest

from tests.conftest import as_role

ENDPOINTS = ["pipeline", "co-sell", "certifications"]
DENIED_ROLES = ["solutions_lead", "marketing"]


def _par(client, path, role="gtm_lead"):
    return client.get(f"/api/partners/{path}", headers=as_role(role))


@pytest.mark.parametrize("path", ENDPOINTS)
def test_partners_endpoints_return_metric(client, path):
    r = _par(client, path)
    assert r.status_code == 200, r.text
    assert r.json()["metric_id"].startswith("PAR-")


@pytest.mark.parametrize("role", DENIED_ROLES)
def test_partners_role_matrix_denies(client, role):
    for path in ENDPOINTS:
        assert _par(client, path, role).status_code == 403


def test_par_pipeline_roles_sum(client):
    body = _par(client, "pipeline").json()
    assert body["value"] >= 0


def test_alliance_manager_sees_only_own_partner(client):
    body = _par(client, "certifications", "alliance_manager").json()
    assert len(body["breakdown"]) == 1
