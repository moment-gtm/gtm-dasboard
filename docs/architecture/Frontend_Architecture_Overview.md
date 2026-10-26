# Moment GTM Dashboard - Frontend Architecture & API Changes Guide

## 1. Different Layers in the Frontend Module
The frontend is built as a Single Page Application (SPA) using **React, TypeScript, and Vite**. It relies heavily on **React Query** for server state (data fetching) and **Zustand** for client state. The architecture is modularized within the `src/` directory:

* **API Layer (`src/api/`)**: Defines TypeScript interfaces mapping to backend schemas and encapsulates network communication. This includes module endpoints as well as the authentication client (`src/api/auth.ts`) and centralized HTTP client (`src/api/client.ts`) which automatically attaches JWT Bearer tokens and role headers.
* **Data Fetching / Hooks Layer (`src/hooks/`)**: Contains custom React hooks. Mostly built on top of `@tanstack/react-query`, this layer handles caching, background refreshing, and loading/error states for backend data.
* **State Layer (`src/state/`)**: Contains global client-side state management using `zustand`. This includes session and authentication state (`src/state/auth.ts`) managing the logged-in Entra persona and Bearer tokens, as well as global filter selections (`src/state/filter.ts`).
* **Component Layer (`src/components/`)**: Reusable UI building blocks. These range from generic components (Buttons, Modals using Radix UI) to domain-specific views (Tables using `@tanstack/react-table`, Charts using `recharts`, and layout components like `RoleSwitcher` and `UserProfile`).
* **Routing Layer (`src/routes/`)**: Page-level components mapped to specific application URLs via `react-router-dom`. Includes the Microsoft Entra ID login portal (`src/routes/Login.tsx`) and the 8 operational dashboard tabs (`/executive`, `/pipeline`, `/pursuits`, etc.).

## 2. Details of Each Layer
* **API (`src/api/`)**: Isolates the frontend from the raw network requests. If the API base URL or authentication mechanism changes, it is updated here. It ensures type safety by providing TS interfaces mirroring the backend's Pydantic schemas.
* **Hooks (`src/hooks/`)**: Decouples UI components from data fetching logic. A component calls `useAccounts()`, and the hook internally decides whether to fetch from the network or return cached data.
* **Components (`src/components/`)**: Primarily strictly "presentational." They take data as props and render the user interface. By keeping business logic out of this layer, the UI remains highly testable and reusable.
* **State (`src/state/`)**: Deals with data that isn't persisted to the backend but needs to be accessed globally across different pages or deeply nested components (e.g., a globally selected fiscal year filter).
* **Routes (`src/routes/`)**: Acts as the "glue". Route components fetch data using hooks, read global state, and pass both down to the presentational components.

## 3. Impact Areas When an API Changes
When an API changes (e.g., a field is renamed, a new parameter is required, or the structure alters), the impact propagates through the frontend layers:
* **API Layer Breakdown**: The TypeScript compiler will catch structural mismatches if the API interface is updated. If the frontend payload doesn't match the new backend expectations, requests will fail (HTTP 422 or 400).
* **Cache Invalidation Issues**: If API query parameters change, React Query cache keys in the Hooks layer might need to be restructured to ensure the frontend doesn't serve stale data.
* **UI Runtime Errors**: If a backend API removes or renames a field (e.g., `dealSize` becomes `tcv`) and the frontend isn't updated, any UI Component trying to render `item.dealSize` will either display blank data or crash if accessing nested properties of an undefined field.
* **Table/Chart Distortions**: Data tables (`react-table`) and charts (`recharts`) explicitly map their columns and axes to data keys. An API change requires updating these configuration objects to point to the new keys.

## 4. Files to Modify for an API Change
If a change occurs in an API on the backend side, you must track it through the frontend by modifying the following files:

1. **`src/api/<relevant_file>.ts`**:
   * **Action:** Update the TypeScript interfaces (e.g., adding `new_field?: string`) to match the new backend JSON schema. Update the API fetching function if the endpoint URL or required HTTP body/params have changed.
2. **`src/hooks/use<RelevantFeature>.ts`**:
   * **Action:** If the API now requires new filtering parameters, update the React Query hook to accept these arguments and include them in the `queryKey` array for proper caching.
3. **`src/components/.../<RelevantComponent>.tsx`**:
   * **Action:** Update the render logic. For example, if updating a table, modify the `columnDef` to bind to the new data keys. If updating a chart, change the `dataKey` attribute.
4. **`src/routes/<RelevantPage>.tsx`** *(Optional)*:
   * **Action:** If the new API data dictates a change in layout or requires passing new state (like a new filter dropdown selection) down to components, update the page layout.

## 5. Microsoft Entra ID Authentication & Session Lifecycle
The frontend integrates directly with Microsoft Entra ID (OIDC/OAuth2) identity contracts:

1. **Entry Portal (`src/routes/Login.tsx`):**
   * Unauthenticated requests are directed to `/login`.
   * Presents a focused **Sign In with Corporate Work Account (UPN)** interface where users input their corporate work email (e.g., `jordan.avery@moment.example`) and password (required; passwordless demo SSO only when the backend sets `GTM_ALLOW_PASSWORDLESS_LOGIN=1`).
   * Directs authentication requests to `POST /api/auth/entra/login`. To maintain enterprise production aesthetics, the allowable users / persona cards listing has been removed from the login screen; a user holds exactly one persona per login, so there is no in-session persona switching by default (see section 4).
2. **Session Store (`src/state/auth.ts`):**
   * On login via `POST /api/auth/entra/login`, the response returns a signed Bearer token containing standard Entra ID claims (`oid`, `sub`, `upn`, `name`, `email`, `roles`, `groups`).
   * `useAuthStore` persists the token and persona details in `localStorage` and initializes state across browser reloads.
3. **HTTP Client Interceptor (`src/api/client.ts`):**
   * Automatically inspects `useAuthStore.getState()` on every outgoing API request.
   * Attaches `Authorization: Bearer <token>` and `X-Mock-Role: <role>` headers to guarantee seamless backend dependency resolution and RLS scoping.
4. **Single Persona per Login (`src/components/layout/PersonaBadge.tsx`, `RoleSwitcher.tsx` & `UserProfile.tsx`):**
   * The header shows a **read-only** `PersonaBadge` (persona label + RLS scope) for the signed-in user. To use another persona the user signs out and signs in with that account.
   * `RoleSwitcher` (persona dropdown) is **demo-only** and rendered by `AppShell` only when `VITE_ENABLE_PERSONA_SWITCHER=true`. It additionally requires backend `GTM_ENABLE_PERSONA_SWITCHER=1` (lists all personas) and `GTM_ALLOW_PASSWORDLESS_LOGIN=1` (re-login without a password). Off by default.
