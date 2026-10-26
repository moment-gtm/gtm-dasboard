"""ACC-01..04: Accounts & Whitespace endpoints, account detail scope and role matrix."""

from __future__ import annotations

import pytest

from tests.conftest import as_role

ENDPOINTS = ["penetration", "whitespace", "expansion", "plan-health"]
DENIED_ROLES = ["solutions_lead", "alliance_manager", "marketing"]


def _acc(client, path, role="gtm_lead"):
    return client.get(f"/api/accounts/{path}", headers=as_role(role))


@pytest.mark.parametrize("path", ENDPOINTS)
def test_accounts_endpoints_return_metric(client, path):
    r = _acc(client, path)
    assert r.status_code == 200, r.text
    assert r.json()["metric_id"].startswith("ACC-")


@pytest.mark.parametrize("role", DENIED_ROLES)
def test_accounts_role_matrix_denies(client, role):
    for path in ENDPOINTS:
        assert _acc(client, path, role).status_code == 403


def test_account_detail_scope(client):
    assert _acc(client, "UNKNOWN/opportunities").status_code == 404
