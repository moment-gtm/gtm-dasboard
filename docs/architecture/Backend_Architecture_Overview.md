# Moment GTM Dashboard - Backend Architecture & API Changes Guide

## 1. Different Layers in the Backend Module
The backend follows a layered architecture to send data to the UI. The main layers found in the `app/` directory are:
* **API Layer** (`app/api/routes`)
* **Dependency & Security Layer** (`app/api/deps.py`)
* **Schema Layer** (`app/schemas`)
* **Semantic / Business Logic Layer** (`app/semantic`)
* **Data Access Layer** (`app/data`)
* **Platform / Infrastructure Layer** (`app/platform`)

## 2. Details of Each Layer
* **API Layer (Routes/Controllers):** Built with FastAPI, this layer exposes HTTP endpoints (e.g., GET, POST) to the UI. It is kept intentionally "thin"—it handles HTTP request parsing, extracts query parameters, and delegates the actual processing to the Semantic layer.
* **Dependency & Security Layer (`app/api/deps.py`):** Resolves incoming request credentials (`Authorization: Bearer <token>` and `X-Mock-Role`), verifies Entra claims (`oid`, `sub`, `upn`, `roles`, `groups`), queries DuckDB `raw_identity_*` tables, and injects authenticated user and RLS context into endpoint handlers.
* **Schema Layer (Data Transfer Objects):** Uses `Pydantic` models to define the exact structure of incoming requests and outgoing JSON responses. It automatically validates the data being sent to the UI screen, ensuring the frontend always receives the expected data types and fields (e.g., `MetricResult` in `app/schemas/common.py`).
* **Semantic Layer (Business Logic & Metrics):** This is the core of the backend. It contains the business rules, filtering logic (e.g., Row-Level Security), and metric calculations (e.g., Penetration matrix logic in `app/semantic/metrics/acc.py`). It takes the context provided by the API layer, formulates the data requirements, and processes the raw data into meaningful metrics.
* **Data Layer:** Responsible for interacting with the database (DuckDB). It handles raw SQL execution, table management, and fetching reference data from the database.
* **Platform Layer:** Handles application-wide infrastructure. This includes authentication providers (`app/platform/auth.py`), database connection pooling, configurations, environment variables, and centralized dependencies.

## 3. Impact Areas When an API Changes
When an API changes for any of the flows, the impact spans across both the Backend and Frontend:
* **Frontend UI Components:** Any component displaying the data will crash or show blank states if the JSON keys they expect are renamed, removed, or if the data hierarchy changes.
* **Frontend API Services:** The HTTP client calls (e.g., `fetch` or `axios` calls) in the frontend must be updated to pass new query parameters or handle the new route structures.
* **Backend Validation:** Changing the API contract immediately impacts the Schema layer, which will reject requests or fail to serialize responses if not updated synchronously.
* **Backend Logic:** If the UI requests a new data point, the Semantic layer must be updated to compute or query this new data point from the database.

## 4. Files to Modify for an API Change
If a change occurs in an API (e.g., adding a new field to the response or changing a filter parameter), you will typically need to modify the following files:

1. **`app/schemas/<relevant_file>.py` (e.g., `common.py`):**
   * **Action:** Update the Pydantic model class to add the new field or modify existing field types. This dictates the JSON structure sent to the UI.
2. **`app/api/routes/<relevant_file>.py` (e.g., `accounts.py`):**
   * **Action:** Update the endpoint's function signature to accept new query parameters. If the endpoint URL itself changes, update the `@router.get(...)` decorator.
3. **`app/semantic/metrics/<relevant_file>.py` (e.g., `acc.py`):**
   * **Action:** Modify the underlying python function that the API route calls. You will need to update the SQL queries or the Python logic to fetch and calculate the new data, and ensure it returns an object that matches the updated schema.
4. **`frontend/src/api/...` (Frontend side):**
   * **Action:** The TypeScript interfaces/types and the service functions that call the backend will need to be updated to consume the new API contract safely.

## 5. Microsoft Entra ID Authentication & Dependency Injection Architecture
The backend implements enterprise identity integration with pluggable provider support (NFR-04):

1. **Pluggable Identity Provider (`app/platform/auth.py`):**
   * Driven by the `GTM_AUTH_MODE` environment variable (`mock` by default, swappable to `azure` for production MSAL).
   * Houses the 9 official Entra ID personas with enterprise claims (`oid`, `sub`, `upn`, `name`, `email`, `roles`, `groups`).
   * Issues standard signed tokens simulating Azure AD tokens and provides persona directory listing (`GET /api/auth/entra/personas`; no password hints are returned).
2. **Auth Route Controllers (`app/api/routes/auth.py`):**
   * Exposes `/api/auth/entra/personas`, `/api/auth/entra/login`, `/api/auth/me`, and `/api/auth/logout`.
   * `POST /api/auth/entra/login` and `/api/auth/login` require a valid password. UPN-only / any-password simulated SSO is available only with `GTM_ALLOW_PASSWORDLESS_LOGIN=1` (demo).
3. **Context Dependency Injection (`app/api/deps.py`):**
   * Inspects `Authorization: Bearer <token>`; a valid token always wins. The `X-Mock-Role` header / `?role=` query is a mock-mode fallback honoured only when `GTM_AUTH_MODE=mock_entra` and `GTM_ALLOW_MOCK_IDENTITY=1` (default on for tests/load/export downloads); otherwise an unauthenticated request gets 401.
   * `GET /api/reference/roles` returns only the caller's own persona unless `GTM_ENABLE_PERSONA_SWITCHER=1`.
   * Resolves the token UPN against DuckDB `raw_identity_user` and `raw_identity_group_membership`.
   * Builds the `CurrentUser` context containing assigned roles, practices, strategic accounts, and restricted metric access flags (`can_view_margin`, `can_view_cost_of_sale`).
   * Injects this user context directly into semantic metric handlers to enforce Row-Level Security (`app/semantic/rls.py`).
