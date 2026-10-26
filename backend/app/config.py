"""Runtime configuration for the prototype (seed, demo "today", plan FX, source mode).

Every value can be overridden with an environment variable so tests and demos stay
deterministic without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _csv(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [v.strip() for v in raw.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    # Synthetic data is seeded so every run (and every test) sees the same deals.
    seed: int = int(os.getenv("GTM_SEED", "42"))
    # Frozen demo "today" (mid Q3 FY26) so plan pace / QTD are stable (Exec plan OQ-3).
    demo_today: date = date.fromisoformat(os.getenv("GTM_DEMO_TODAY", "2026-08-14"))
    # Fiscal year runs Jan-Dec (RSD 7.3); FY26 = CY2026.
    fiscal_year_start_month: int = 1
    # "mock" = in-process mock connectors (no external APIs available yet).
    source_mode: str = os.getenv("GTM_SOURCE_MODE", "mock")
    # Comma list of source ids whose mock connector should fail (demo error/stale states).
    mock_fail_sources: list[str] = field(default_factory=lambda: _csv("GTM_MOCK_FAIL_SOURCES"))
    # Comma list of source ids to report as stale (demo the staleness banner).
    mock_stale_sources: list[str] = field(default_factory=lambda: _csv("GTM_MOCK_STALE_SOURCES"))
    # Read-only DuckDB copy of the platform written after each ELT run (for the DuckDB MCP).
    snapshot_db_path: Path = Path(
        os.getenv("GTM_SNAPSHOT_DB", str(BACKEND_DIR / "var" / "gtm_snapshot.duckdb"))
    )
    # Audit log persists across ELT rebuilds (NFR-07, 12-month retention).
    audit_db_path: Path = Path(os.getenv("GTM_AUDIT_DB", str(BACKEND_DIR / "var" / "audit.duckdb")))
    admin_db_path: Path = Path(os.getenv("GTM_ADMIN_DB", str(BACKEND_DIR / "var" / "admin.duckdb")))
    crm_record_url: str = os.getenv(
        "GTM_CRM_RECORD_URL",
        "https://moment-demo.lightning.force.com/lightning/r/Opportunity/{id}/view",
    )
    enable_scheduler: bool = os.getenv("GTM_ENABLE_SCHEDULER", "1") == "1"
    cors_origins: list[str] = field(
        default_factory=lambda: _csv("GTM_CORS_ORIGINS") or ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    # Authentication mode: "mock_entra" (default prototype directory) or "entra" (production Azure MSAL/OIDC).
    auth_mode: str = os.getenv("GTM_AUTH_MODE", "mock_entra")
    entra_tenant_id: str = os.getenv("ENTRA_TENANT_ID", "")
    entra_client_id: str = os.getenv("ENTRA_CLIENT_ID", "")
    entra_client_secret: str = os.getenv("ENTRA_CLIENT_SECRET", "")
    # Demo-only switches. A user holds one persona per login; these are OFF/restricted by default.
    # Passwordless (UPN-only) simulated SSO, and the "any password is accepted" mock fallback.
    allow_passwordless_login: bool = os.getenv("GTM_ALLOW_PASSWORDLESS_LOGIN", "0") == "1"
    # Honour the unauthenticated X-Mock-Role header / ?role= query (test + export-download fallback).
    # Only ever effective when auth_mode == "mock_entra"; a valid Bearer token always wins.
    allow_mock_identity: bool = os.getenv("GTM_ALLOW_MOCK_IDENTITY", "1") == "1"
    # Lets /api/reference/roles list every persona (feeds the optional in-app persona switcher).
    enable_persona_switcher: bool = os.getenv("GTM_ENABLE_PERSONA_SWITCHER", "0") == "1"

    @property
    def mock_identity_enabled(self) -> bool:
        return self.auth_mode == "mock_entra" and self.allow_mock_identity


settings = Settings()
