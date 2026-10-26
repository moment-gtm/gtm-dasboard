import { ApiError } from "@/api/errors";
import fixtures from "./data.json";

type MockRequest = {
  url: string;
  method: string;
  body?: BodyInit | null;
  headers?: HeadersInit;
};

type Persona = {
  upn: string;
  username: string;
  name: string;
  email: string;
  role: string;
  role_label: string;
  job_title: string;
  group_name: string;
  scope_type: string;
  scope_value: string | null;
  description: string;
};

const fixtureData = fixtures as Record<string, unknown>;
const sessionKey = "gtm-frontend-mock-session";
const overridesKey = "gtm-frontend-mock-overrides";

function copy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function personas(): Persona[] {
  return copy(fixtureData["/api/auth/entra/personas"] as Persona[]);
}

function readOverrides(): Record<string, unknown> {
  const stored = localStorage.getItem(overridesKey);
  return stored ? (JSON.parse(stored) as Record<string, unknown>) : {};
}

function saveOverride(path: string, value: unknown): void {
  const overrides = readOverrides();
  overrides[path] = value;
  localStorage.setItem(overridesKey, JSON.stringify(overrides));
}

function personaForRole(role: string): Record<string, unknown> | undefined {
  const allRoles = copy(fixtureData["/api/reference/roles"] as Record<string, unknown>[]);
  return allRoles.find((persona) => persona.role === role);
}

function asUser(persona: Persona): Record<string, unknown> {
  return {
    username: persona.username,
    upn: persona.upn,
    name: persona.name,
    email: persona.email,
    role: persona.role,
    role_label: persona.role_label,
    job_title: persona.job_title,
    group_name: persona.group_name,
    scope_type: persona.scope_type,
    scope_value: persona.scope_value,
    description: persona.description,
  };
}

function readBody(body: BodyInit | null | undefined): Record<string, unknown> {
  if (typeof body !== "string") return {};
  return JSON.parse(body) as Record<string, unknown>;
}

function pagedOpportunities(path: string, search: URLSearchParams): unknown {
  const base = copy(fixtureData[path] as Record<string, unknown>);
  const rows = base.rows as Record<string, unknown>[];
  const query = (search.get("search") ?? "").toLowerCase();
  let filtered = rows.filter((row) =>
    [row.name, row.account_name, row.opportunity_id].some((value) =>
      String(value ?? "").toLowerCase().includes(query),
    ),
  );
  const dimensions: [string, string][] = [
    ["vertical", "vertical"],
    ["practice", "lead_practice"],
    ["platform", "primary_platform"],
    ["account", "account_id"],
    ["client_partner", "owner_name"],
    ["deal_source", "lead_source"],
    ["geography", "geography"],
  ];
  let hasFilter = Boolean(query);
  for (const [key, field] of dimensions) {
    const selected = search.getAll(key);
    if (selected.length) {
      hasFilter = true;
      filtered = filtered.filter((row) => selected.includes(String(row[field] ?? "")));
    }
  }
  const sortBy = search.get("sort") ?? "tcv";
  const sortFields: Record<string, string> = {
    tcv: "tcv",
    weighted_tcv: "weighted_tcv",
    close_date: "close_date",
    name: "name",
    account_name: "account_name",
    days_in_stage: "days_in_stage",
    stage: "stage",
  };
  const sortField = sortFields[sortBy] ?? "tcv";
  const direction = search.get("order") === "asc" ? 1 : -1;
  filtered = [...filtered].sort((a, b) => {
    const left = a[sortField];
    const right = b[sortField];
    if (typeof left === "number" && typeof right === "number") return (left - right) * direction;
    return String(left ?? "").localeCompare(String(right ?? "")) * direction;
  });
  const pageSize = Math.min(Number(search.get("page_size") ?? base.page_size ?? 25), 50);
  const page = Math.max(Number(search.get("page") ?? 1), 1);
  return {
    ...base,
    total_count: hasFilter ? filtered.length : base.total_count,
    page,
    page_size: pageSize,
    rows: filtered.slice((page - 1) * pageSize, page * pageSize),
  };
}

function dynamicFixture(path: string): unknown {
  const overrides = readOverrides();
  if (path in overrides) return overrides[path];
  if (path === "/api/opportunities") return fixtureData[path];
  if (/^\/api\/accounts\/[^/]+\/opportunities$/.test(path) && path in fixtureData) {
    return fixtureData[path];
  }
  if (/^\/api\/admin\/thresholds\/[^/]+\/history$/.test(path)) {
    return fixtureData[path] ?? [];
  }
  if (/^\/api\/admin\/reference\/[^/]+$/.test(path) && path in fixtureData) {
    return fixtureData[path];
  }
  return undefined;
}

function mutate(path: string, method: string, body: Record<string, unknown>): unknown {
  const overrides = readOverrides();
  const thresholds = copy(
    (overrides["/api/admin/thresholds"] ??
      fixtureData["/api/admin/thresholds"]) as Record<string, unknown>[],
  );
  const thresholdMatch = path.match(/^\/api\/admin\/thresholds\/([^/]+)$/);
  if (method === "PUT" && thresholdMatch) {
    const metricId = decodeURIComponent(thresholdMatch[1]);
    const updated = thresholds.find((item) => item.metric_id === metricId);
    if (!updated) throw new ApiError(404, "Threshold not found");
    Object.assign(updated, body, { version: Number(updated.version ?? 0) + 1 });
    saveOverride("/api/admin/thresholds", thresholds);
    saveOverride(path, updated);
    const historyPath = `${path}/history`;
    const history = copy(
      (overrides[historyPath] ?? fixtureData[historyPath] ?? []) as Record<string, unknown>[],
    );
    history.unshift({
      version: updated.version,
      on_track: updated.on_track,
      watch: updated.watch,
      reason: body.reason ?? "Updated in browser demo",
      changed_by: "Frontend demo user",
      changed_at: new Date().toISOString(),
    });
    saveOverride(historyPath, history);
    return copy(updated);
  }

  const referenceMatch = path.match(/^\/api\/admin\/reference\/([^/]+)$/);
  if (method === "PUT" && referenceMatch) {
    const key = decodeURIComponent(referenceMatch[1]);
    const referencePath = `/api/admin/reference/${encodeURIComponent(key)}`;
    const current = copy(
      (overrides[referencePath] ?? fixtureData[referencePath]) as Record<string, unknown>,
    );
    Object.assign(current, body, { version: Number(current.version ?? 0) + 1 });
    current.count = Array.isArray(current.values) ? current.values.length : 0;
    saveOverride(referencePath, current);
    const summaries = copy(
      (overrides["/api/admin/reference"] ??
        fixtureData["/api/admin/reference"]) as Record<string, unknown>[],
    );
    const summary = summaries.find((item) => item.key === key);
    if (summary) Object.assign(summary, { count: current.count, version: current.version });
    saveOverride("/api/admin/reference", summaries);
    return { key, version: current.version };
  }

  if (method === "POST" && path === "/api/admin/change-requests") {
    const requests = copy(
      (overrides[path] ?? fixtureData[path]) as Record<string, unknown>[],
    );
    const created = {
      ...body,
      id: Date.now(),
      requested_by: "Frontend demo user",
      status: "logged",
      assessments: [],
      decision_by: null,
      decision_note: null,
      release_window: null,
      created_at: new Date().toISOString(),
    };
    requests.unshift(created);
    saveOverride(path, requests);
    return copy(created);
  }

  const changeMatch = path.match(/^\/api\/admin\/change-requests\/(\d+)(?:\/(assess|decide|release))?$/);
  if (changeMatch && method === "POST") {
    const requests = copy(
      (overrides["/api/admin/change-requests"] ??
        fixtureData["/api/admin/change-requests"]) as Record<string, unknown>[],
    );
    const request = requests.find((item) => item.id === Number(changeMatch[1]));
    if (!request) throw new ApiError(404, "Change request not found");
    if (changeMatch[2] === "assess") {
      const assessments = (request.assessments as Record<string, unknown>[]) ?? [];
      assessments.push({ role: "gtm_lead", by: "Frontend demo user", ...body, at: new Date().toISOString() });
      request.assessments = assessments;
      request.status = "assessed";
    } else if (changeMatch[2] === "decide") {
      request.status = body.decision === "approve" ? "approved" : "rejected";
      request.decision_by = "Frontend demo user";
      request.decision_note = body.note;
    } else if (changeMatch[2] === "release") {
      request.status = "released";
    }
    saveOverride("/api/admin/change-requests", requests);
    return copy(request);
  }

  const alertList = (overrides["/api/alerts/rules"] ??
    fixtureData["/api/alerts/rules"]) as { rules: Record<string, unknown>[] };
  const alertRules = copy(alertList.rules);
  const alertMatch = path.match(/^\/api\/alerts\/rules(?:\/([^/]+))?$/);
  if (alertMatch && method === "PUT") {
    const rule = alertRules.find((item) => item.rule_id === decodeURIComponent(alertMatch[1] ?? ""));
    if (!rule) throw new ApiError(404, "Alert rule not found");
    Object.assign(rule, body);
    saveOverride("/api/alerts/rules", { ...alertList, rules: alertRules });
    return copy(rule);
  }
  if (alertMatch && method === "POST") {
    const rule = {
      ...body,
      rule_id: `mock-rule-${Date.now()}`,
      triggered: false,
      status: "neutral",
      observed_value: null,
      observed_label: "No matching data",
      summary: "This mock rule has not been evaluated.",
      matching_deals: [],
      deep_link: "/admin",
      subscription: { email: false, teams: false },
    };
    alertRules.push(rule);
    saveOverride("/api/alerts/rules", { ...alertList, rules: alertRules });
    return copy(rule);
  }

  if (path === "/api/alerts/subscriptions" && method === "PUT") {
    const current = copy(
      (overrides[path] ?? fixtureData[path]) as Record<string, unknown>,
    );
    const updates = body.subscriptions as Record<string, unknown>[];
    const subscriptions = current.subscriptions as Record<string, unknown>[];
    for (const update of updates) {
      const target = subscriptions.find((item) => item.target_id === update.target_id);
      if (target) Object.assign(target, update);
    }
    saveOverride(path, current);
    return current;
  }

  if (path === "/api/alerts/digest/schedule" && method === "PUT") {
    const digest = copy(
      (overrides["/api/alerts/digest"] ??
        fixtureData["/api/alerts/digest"]) as Record<string, unknown>,
    );
    digest.schedule = body;
    saveOverride("/api/alerts/digest", digest);
    saveOverride(path, body);
    return copy(body);
  }

  if (path === "/api/exports/view" || path === "/api/alerts/digest") {
    return { message: "Mock action recorded", ...body };
  }

  const result = { ...body, id: Date.now(), mock: true };
  saveOverride(path, result);
  return result;
}

export async function mockRequest<T>({ url, method, body, headers }: MockRequest): Promise<T> {
  const parsed = new URL(url, window.location.origin);
  const path = parsed.pathname;
  const normalizedMethod = method.toUpperCase();
  const overrides = readOverrides();

  if (path === "/api/auth/entra/login" || path === "/api/auth/login") {
    const requestBody = readBody(body);
    const identifier = String(requestBody.upn ?? requestBody.username ?? "").trim().toLowerCase();
    const allPersonas = personas();
    const persona =
      identifier === "gtm-user"
        ? allPersonas.find((item) => item.username === "jordan.avery")
        : allPersonas.find(
            (item) => item.upn.toLowerCase() === identifier || item.username.toLowerCase() === identifier,
          );
    if (!persona) throw new ApiError(401, "Choose a listed synthetic demo persona.");
    const expectedPassword =
      identifier === "gtm-user" ? "gtm-dashboard" : `Moment#2026$${persona.name.split(" ")[0]}!GTM`;
    if (requestBody.password !== expectedPassword) {
      throw new ApiError(401, "Invalid synthetic demo credentials. Check the demo password format.");
    }
    const user = asUser(persona);
    const token = `mock-${crypto.randomUUID()}`;
    sessionStorage.setItem(sessionKey, JSON.stringify({ token, user }));
    return { access_token: token, token_type: "bearer", user } as T;
  }

  if (path === "/api/auth/me") {
    const authorization = new Headers(headers).get("Authorization") ?? "";
    const stored = sessionStorage.getItem(sessionKey);
    const session = stored
      ? (JSON.parse(stored) as { token: string; user: Record<string, unknown> })
      : undefined;
    if (!session || authorization !== `Bearer ${session.token}`) {
      throw new ApiError(401, "Not authenticated");
    }
    return copy(session.user) as T;
  }

  if (path === "/api/auth/logout") {
    sessionStorage.removeItem(sessionKey);
    return { message: "Logged out successfully" } as T;
  }

  if (normalizedMethod === "GET") {
    if (path === "/api/me") {
      const persona = personaForRole(new Headers(headers).get("X-Mock-Role") ?? "gtm_lead");
      if (!persona) throw new ApiError(404, "Persona not found");
      return copy(persona) as T;
    }
    if (path === "/api/opportunities" || /^\/api\/accounts\/[^/]+\/opportunities$/.test(path)) {
      const fixture = dynamicFixture(path);
      if (!fixture) throw new ApiError(404, "No synthetic opportunity data is available");
      return pagedOpportunities(path, parsed.searchParams) as T;
    }
    const value = dynamicFixture(path) ?? overrides[path] ?? fixtureData[path];
    if (value === undefined) throw new ApiError(404, `No synthetic fixture for ${path}`);
    return copy(value) as T;
  }

  return mutate(path, normalizedMethod, readBody(body)) as T;
}

export function mockDownloadUrl(
  path: string,
  extra: Record<string, string | number | null | undefined>,
): string {
  const metricId = extra.metric_id ?? "dashboard";
  const candidates = Object.values(fixtureData).flatMap((value) =>
    Array.isArray(value) ? value : [value],
  );
  const metric = candidates.find(
    (value): value is Record<string, unknown> =>
      !!value && typeof value === "object" && "metric_id" in value && value.metric_id === metricId,
  );
  const rows = path.endsWith("/opportunities")
    ? fixtureData["/api/opportunities"]
    : metric && Array.isArray(metric.breakdown)
      ? metric.breakdown
      : fixtureData["/api/opportunities"];
  const records = Array.isArray(rows)
    ? rows
    : ((rows as Record<string, unknown> | undefined)?.rows ?? []);
  const objects = records as Record<string, unknown>[];
  const columns = [...new Set(objects.flatMap((row) => Object.keys(row)))];
  const escape = (value: unknown) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const content = [columns.map(escape).join(","), ...objects.map((row) => columns.map((key) => escape(row[key])).join(","))].join("\n");
  return `data:text/csv;charset=utf-8,${encodeURIComponent(content)}`;
}
