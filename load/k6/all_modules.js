// AC-04 load test: 50 concurrent users across all 8 analytical modules + filter changes.
// Asserts P90 <= 3s on initial module view load and P90 <= 2s on filter changes.
// Run against a started backend: k6 run load/k6/all_modules.js
import http from "k6/http";
import { check, group, sleep } from "k6";

const BASE = __ENV.API_URL || "http://localhost:8000";

export const options = {
  scenarios: {
    all_modules_load: {
      executor: "ramping-vus",
      startVUs: 10,
      stages: [
        { duration: "15s", target: 50 },
        { duration: "45s", target: 50 },
        { duration: "10s", target: 0 },
      ],
    },
  },
  thresholds: {
    "http_req_duration{kind:view}": ["p(90)<3000"],
    "http_req_duration{kind:filter}": ["p(90)<2000"],
    http_req_failed: ["rate<0.01"],
  },
};

const PERSONA_VIEWS = [
  {
    role: "gtm_lead",
    endpoints: [
      "/api/executive/runway",
      "/api/executive/kpis",
      "/api/pipeline/funnel",
      "/api/pursuits/win-rate",
      "/api/pursuits/margin",
      "/api/offerings/by-offering",
      "/api/accounts/penetration",
      "/api/partners/pipeline",
      "/api/capacity/architect-load",
      "/api/capacity/cost-of-sale",
      "/api/market/thought-leadership",
    ],
  },
  {
    role: "leadership",
    endpoints: [
      "/api/executive/kpis",
      "/api/pipeline/ageing",
      "/api/pursuits/bid-discipline",
      "/api/offerings/attach-rate",
      "/api/accounts/whitespace",
      "/api/partners/co-sell",
      "/api/capacity/rfp-turnaround",
      "/api/market/analyst-positioning",
    ],
  },
  {
    role: "finance",
    endpoints: [
      "/api/executive/runway",
      "/api/pursuits/margin",
      "/api/capacity/cost-of-sale",
      "/api/market/campaign-sourced",
    ],
  },
  {
    role: "practice_lead",
    endpoints: [
      "/api/executive/kpis",
      "/api/pipeline/by-practice",
      "/api/pursuits/win-rate",
      "/api/offerings/asset-reuse",
      "/api/accounts/penetration",
      "/api/capacity/architect-load",
      "/api/market/workshop-funnel",
    ],
  },
  {
    role: "client_partner",
    endpoints: [
      "/api/executive/kpis",
      "/api/pipeline/funnel",
      "/api/accounts/penetration",
      "/api/accounts/expansion",
      "/api/partners/pipeline",
    ],
  },
  {
    role: "alliance_manager",
    endpoints: [
      "/api/executive/kpis",
      "/api/partners/pipeline",
      "/api/partners/co-sell",
      "/api/partners/certifications",
      "/api/offerings/by-offering",
    ],
  },
  {
    role: "solutions_lead",
    endpoints: [
      "/api/pipeline/funnel",
      "/api/pursuits/bid-discipline",
      "/api/offerings/ai-validation",
      "/api/capacity/architect-load",
      "/api/capacity/rfp-turnaround",
      "/api/capacity/quality-scores",
    ],
  },
  {
    role: "marketing",
    endpoints: [
      "/api/executive/kpis",
      "/api/market/thought-leadership",
      "/api/market/workshop-funnel",
      "/api/market/campaign-sourced",
      "/api/market/analyst-positioning",
    ],
  },
  {
    role: "sales_ops",
    endpoints: [
      "/api/executive/kpis",
      "/api/pipeline/register",
      "/api/pipeline/stage-movement",
      "/api/pursuits/loss-reasons",
      "/api/accounts/plan-health",
      "/api/admin/dq",
    ],
  },
];

const FILTERS = [
  "period_mode=QTD",
  "practice=DxP",
  "practice=Data%20%26%20AI&vertical=Financial%20Services",
  "geography=North%20America",
  "platform=Adobe",
];

export default function () {
  const persona = PERSONA_VIEWS[__VU % PERSONA_VIEWS.length];
  const headers = { "X-Demo-Role": persona.role };

  group("module view load", () => {
    const batch = persona.endpoints.map((ep) => [
      "GET",
      `${BASE}${ep}`,
      null,
      { headers, tags: { kind: "view" } },
    ]);
    const responses = http.batch(batch);
    check(responses, {
      "module view endpoints return 200": (rs) => rs.every((r) => r.status === 200),
    });
  });

  group("filter change", () => {
    const qs = FILTERS[__ITER % FILTERS.length];
    const ep = persona.endpoints[__ITER % persona.endpoints.length];
    const sep = ep.includes("?") ? "&" : "?";
    const res = http.get(`${BASE}${ep}${sep}${qs}`, {
      headers,
      tags: { kind: "filter" },
    });
    check(res, { "filtered endpoint 200": (r) => r.status === 200 });
  });

  sleep(0.3);
}
