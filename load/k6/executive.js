// AC-04 / NFR-01: Executive view at 50 concurrent users; P90 < 3s (filter changes < 2s).
// Run: k6 run load/k6/executive.js  (BASE_URL defaults to the backend on :8000)
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";
const ROLES = ["gtm_lead", "leadership", "practice_lead", "client_partner", "sales_ops"];
const ENDPOINTS = [
  "/api/executive/runway",
  "/api/executive/kpis",
  "/api/executive/bookings-by-quarter",
  "/api/executive/pipeline-by-vertical",
  "/api/executive/deals-attention",
];
const FILTERS = ["", "&vertical=BFSI", "&practice=DxP", "&period=qtd", "&platform=Adobe&geography=EMEA"];

export const options = {
  scenarios: {
    executive_view: { executor: "constant-vus", vus: 50, duration: "2m" },
  },
  thresholds: {
    "http_req_duration{kind:view}": ["p(90)<3000"],
    "http_req_duration{kind:filter}": ["p(90)<2000"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const role = ROLES[__VU % ROLES.length];
  const headers = { "X-Mock-Role": role };
  const filter = FILTERS[__ITER % FILTERS.length];
  const kind = filter ? "filter" : "view";
  const responses = http.batch(
    ENDPOINTS.map((p) => ["GET", `${BASE}${p}?period=fytd${filter}`, null, { headers, tags: { kind } }]),
  );
  for (const r of responses) check(r, { "status 200": (x) => x.status === 200 });
  sleep(1);
}
