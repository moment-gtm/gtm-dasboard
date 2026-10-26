import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { MetricMeta, MetricResult } from "@/api/types";
import { KpiCard } from "@/components/charts/KpiCard";
import { WidgetCard } from "@/components/common/WidgetCard";
import { MetricIdsToggle } from "@/components/layout/MetricIdsToggle";
import { useMetricIdsStore } from "@/state/metricIds";

const MOCK_METRICS_META: MetricMeta[] = [
  {
    metric_id: "EXE-02",
    name: "Pipeline coverage",
    definition: "Qualified open pipeline divided by combined target for current and next quarter.",
    calculation: "SUM(tcv_usd) open Qualify+ ÷ remaining target",
    sources: [
      { source_id: "SRC-01", name: "CRM (Salesforce Sales Cloud)" },
      { source_id: "SRC-02", name: "Planning / targets (Anaplan)" },
    ],
    owner: "Sales Operations",
    refresh: "Daily; weekly snapshot",
    dimensions: ["Vertical", "Practice", "Platform"],
    period_sensitive: false,
    goal_label: "3.0x (Watch 2.5x–3.0x)",
    last_refresh: "2026-08-14T01:30:00Z",
  },
  {
    metric_id: "PIP-01",
    name: "Stage funnel & conversion",
    definition: "Open pipeline by sales stage and stage-to-stage conversion rate.",
    calculation: "SUM(tcv_usd) and COUNT(*) grouped by stage",
    sources: [{ source_id: "SRC-01", name: "CRM (Salesforce Sales Cloud)" }],
    owner: "Sales Operations",
    refresh: "Daily",
    dimensions: ["Stage", "Practice", "Vertical"],
    period_sensitive: true,
    goal_label: null,
    last_refresh: "2026-08-14T01:30:00Z",
  },
];

const MOCK_KPI_RESULT: MetricResult = {
  metric_id: "EXE-02",
  name: "Pipeline coverage",
  unit: "x",
  value: 3.2,
  target: 3.0,
  target_prorated: false,
  target_basis: null,
  goal: 3.0,
  goal_label: "Goal 3.0x",
  attainment: 1.07,
  status: "on_track",
  status_basis: "3.2x vs 3.0x goal",
  breakdown: [],
  sparkline: [
    { label: "2025-Q4", value: 2.8, partial: false },
    { label: "2026-Q1", value: 3.0, partial: false },
    { label: "2026-Q2", value: 3.1, partial: false },
    { label: "2026-Q3", value: 3.2, partial: true },
  ],
  narrative: null,
  period: {
    kind: "fytd",
    start: "2026-01-01",
    end: "2026-08-14",
    label: "FY26 to date",
    fiscal_year: 2026,
  },
  as_of: "2026-08-14",
  sources: ["SRC-01", "SRC-02"],
  meta: {},
};

function renderWithQueryClient() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  qc.setQueryData(["metric-meta", "gtm_lead"], MOCK_METRICS_META);
  return render(
    <QueryClientProvider client={qc}>
      <MetricIdsToggle />
      <KpiCard metric={MOCK_KPI_RESULT} />
      <WidgetCard
        title="Stage funnel & conversion"
        description="Open pipeline across sales stages."
        metricId="PIP-01"
      >
        <div>Chart content</div>
      </WidgetCard>
    </QueryClientProvider>,
  );
}

describe("MetricIdsToggle (FR-GEN-07)", () => {
  beforeEach(() => {
    useMetricIdsStore.setState({ showMetricIds: false });
  });

  it("hides metric ID chips and inline source badges by default, and reveals them across all widgets when switched on", () => {
    renderWithQueryClient();

    const toggle = screen.getByTestId("toggle-metric-ids");
    expect(toggle).not.toBeChecked();
    expect(screen.queryAllByTestId("metric-id-chip")).toHaveLength(0);
    expect(screen.queryAllByTestId("metric-sources-chip")).toHaveLength(0);

    fireEvent.click(toggle);
    expect(toggle).toBeChecked();

    const idChips = screen.getAllByTestId("metric-id-chip");
    expect(idChips.map((el) => el.textContent)).toEqual(["EXE-02", "PIP-01"]);

    const sourceChips = screen.getAllByTestId("metric-sources-chip");
    expect(sourceChips.map((el) => el.textContent)).toEqual(["SRC-01 · SRC-02", "SRC-01"]);

    fireEvent.click(toggle);
    expect(toggle).not.toBeChecked();
    expect(screen.queryAllByTestId("metric-id-chip")).toHaveLength(0);
    expect(screen.queryAllByTestId("metric-sources-chip")).toHaveLength(0);
  });
});
