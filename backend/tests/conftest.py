"""Test fixtures. Env is set before the app is imported so settings pick it up."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="gtm_tests_"))
os.environ.setdefault("GTM_AUDIT_DB", str(_tmp / "audit.duckdb"))
os.environ.setdefault("GTM_ADMIN_DB", str(_tmp / "admin.duckdb"))
os.environ.setdefault("GTM_SNAPSHOT_DB", str(_tmp / "snapshot.duckdb"))
os.environ["GTM_ENABLE_SCHEDULER"] = "0"
os.environ.setdefault("GTM_DISABLE_EXCEL", "1")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.data.generator import generate  # noqa: E402
from app.main import app  # noqa: E402
from app.platform.db import get_platform  # noqa: E402
from app.semantic.context import QueryContext  # noqa: E402
from app.semantic.filters import FilterParams  # noqa: E402
from app.semantic.rls import resolve_user  # noqa: E402

ALL_ROLES = [
    "gtm_lead",
    "leadership",
    "finance",
    "practice_lead",
    "client_partner",
    "alliance_manager",
    "marketing",
    "sales_ops",
    "solutions_lead",
]
EXEC_ROLES = [r for r in ALL_ROLES if r != "solutions_lead"]


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def platform(client):
    # Function-scoped: reconciliation tests rebuild (and swap) the platform.
    return get_platform()


@pytest.fixture(scope="session")
def dataset():
    return generate()


@pytest.fixture
def ctx(platform):
    def make(role: str = "gtm_lead", **filters) -> QueryContext:
        return QueryContext(
            platform=platform, params=FilterParams(**filters), user=resolve_user(platform, role)
        )

    return make


def as_role(role: str) -> dict:
    return {"X-Mock-Role": role}
