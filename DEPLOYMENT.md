# Moment GTM Dashboard — Server Deployment Guide

This archive contains the production-ready source code, analytical databases, and deployment assets for the **Moment GTM Dashboard**.

---

## Architecture Overview

- **Backend**: FastAPI REST API + DuckDB analytical engine (Python 3.11+)
  - Port: `8000`
  - Pre-seeded Analytical Engine: `backend/var/gtm_snapshot.duckdb`, `backend/var/admin.duckdb`, `backend/var/audit.duckdb`
  - Master Template Ingestion: `data/templates/Moment_GTM_Dashboard_Master_Data_Template.xlsx`
- **Frontend**: React 18 + TypeScript + Tailwind CSS UI
  - Development / Dev-Server Port: `5173` / `3000`
  - Pre-built Production Bundle: `frontend/dist/`

---

## Deployment Option 1: Docker Compose (Recommended)

From dashboard root directory:

```bash
docker compose up --build -d
```

- **Frontend**: `http://<server-ip>:5173`
- **Backend API**: `http://<server-ip>:8000`
- **Interactive Swagger Docs**: `http://<server-ip>:8000/docs`

---

## Deployment Option 2: Standalone Production Services

### 1. Backend Setup (FastAPI / Uvicorn)

```bash
cd backend

# Create virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# Run backend service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Hosting

#### A. Direct Static Serving (Nginx / Caddy / Static Web Server)
The production bundle is already compiled in `frontend/dist`. You can directly serve this directory via Nginx, Apache, or Caddy.

Sample Nginx configuration:
```nginx
server {
    listen 80;
    server_name dashboard.yourdomain.com;

    root /path/to/dashboard/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /mock/ {
        proxy_pass http://127.0.0.1:8000/mock/;
        proxy_set_header Host $host;
    }
}
```

#### B. Node.js Production Preview / Dev Server
```bash
cd frontend
npm ci
npm run build   # If rebuilding bundle
npx vite preview --host 0.0.0.0 --port 5173
```

---

## Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `GTM_DEMO_TODAY` | `2026-08-14` | Frozen anchor date for quarterly pacing calculations |
| `GTM_CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed CORS origins for frontend access |
| `GTM_SOURCE_MODE` | `mock` | Source connector mode (`mock` or real API connectors) |
| `GTM_ENABLE_SCHEDULER` | `1` | Enable background ELT refresh scheduler |
| `VITE_BACKEND_URL` | `http://127.0.0.1:8000` | Frontend target URL for API proxying |
| `GTM_AUTH_MODE` | `mock_entra` | Authentication mode (`mock_entra` or `entra` for production Azure AD) |
| `GTM_ALLOW_PASSWORDLESS_LOGIN` | `0` | Demo only: accept UPN-only / any-password login. Keep `0` outside demos |
| `GTM_ALLOW_MOCK_IDENTITY` | `1` | Honour unauthenticated `X-Mock-Role` / `?role=` (mock mode only; used by tests, k6, export downloads). Set `0` for any shared deployment |
| `GTM_ENABLE_PERSONA_SWITCHER` | `0` | Demo only: `/api/reference/roles` lists every persona (backs the optional switcher). Frontend flag: `VITE_ENABLE_PERSONA_SWITCHER=true` |
| `ENTRA_TENANT_ID` | `""` | Microsoft Entra (Azure AD) Directory Tenant GUID |
| `ENTRA_CLIENT_ID` | `""` | Microsoft Entra Registered Application Client GUID |
| `ENTRA_CLIENT_SECRET` | `""` | Microsoft Entra Client Secret (optional) |

---

## Microsoft Entra ID (Azure AD) Single Sign-On Configuration

The application features a turnkey, pluggable authentication architecture compliant with **RSD Requirement NFR-04** (SSO via Entra ID) and **NFR-05** (RLS via Entra Group Membership).

### Operating Modes

1. **Mock Entra Mode (Default — `GTM_AUTH_MODE=mock_entra`)**:
   - Ingests mock directory users and group memberships directly from DuckDB (`raw_identity_user`, `raw_identity_group`, `raw_identity_group_membership`).
   - Issues Microsoft-compatible claims tokens (`oid`, `sub`, `upn`, `name`, `email`, `roles`, `groups`).
   - Authenticates corporate work accounts via the "Sign In with Corporate Work Account (UPN)" portal on `/login`, supporting the 12 certified personas with assigned security groups with one persona per login (no in-session persona switching; the demo-only `RoleSwitcher` is off by default).

2. **Production Microsoft Entra ID Mode (`GTM_AUTH_MODE=entra`)**:
   - Validates live Microsoft Entra bearer tokens using Microsoft's OpenID Connect discovery endpoints (`https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys`).
   - Maps standard Microsoft JWT claims directly into the analytical Row-Level Security (RLS) layer.

### Turnkey Azure AD Setup Steps

1. **Register App in Microsoft Entra Admin Center**:
   - Navigate to **Azure Portal** > **Microsoft Entra ID** > **App registrations** > **New registration**.
   - Name: `Moment GTM Dashboard`.
   - Supported account types: `Accounts in this organizational directory only (Single tenant)`.
   - Redirect URI: Single-page application (SPA): `https://dashboard.yourdomain.com/` (or `http://localhost:5173/` for local testing).

2. **Configure API Permissions & Entra Security Groups**:
   - Under **API Permissions**, ensure `Microsoft Graph` > `User.Read` is granted.
   - Under **App roles** or **Security Groups**, configure the standard GTM security groups:
     - `GTM-Dashboard-GTMLead` (All data + Admin)
     - `GTM-Dashboard-Leadership` (All data)
     - `GTM-Dashboard-Finance` (All data + Margin/Retention)
     - `GTM-Dashboard-PracticeLead-DxP` (DxP Practice deals)
     - `GTM-Dashboard-ClientPartner` (Strategic accounts)
     - `GTM-Dashboard-Alliance-Adobe` (Adobe partner deals)
     - `GTM-Dashboard-Marketing` (Campaign attribution)
     - `GTM-Dashboard-SalesOps` (Operations & Data Quality)
     - `GTM-Dashboard-Solutions` (Technical capacity)

3. **Set Environment Variables**:
   In backend `.env` or system environment:
   ```bash
   GTM_AUTH_MODE=entra
   ENTRA_TENANT_ID=<your-azure-tenant-guid>
   ENTRA_CLIENT_ID=<your-azure-app-client-guid>
   ENTRA_CLIENT_SECRET=<your-azure-client-secret>
   ```
