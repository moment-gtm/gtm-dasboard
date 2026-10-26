import { render, screen, within } from "@testing-library/react";
import type { MetricResult, StatusValue } from "@/api/types";
import { StatusSpotlight } from "./StatusSpotlight";
import { StatusSummary } from "./StatusSummary";

const metric = (id: string, status: StatusValue | null, value = 0.5): MetricResult =>
  ({
    metric_id: id,
    name: `Metric ${id}`,
    unit: "pct",
    value,
    status,
    status_basis: status ? `${id} basis` : null,
  }) as MetricResult;

describe("StatusSummary", () => {
  it("counts the statuses it is given, each as text + icon", () => {
    render(
      <StatusSummary
        label="Scorecard"
        statuses={["on_track", "watch", "off_track", "watch", null]}
      />,
    );
    const items = within(screen.getByTestId("status-summary")).getAllByRole("listitem");
    expect(items.map((li) => li.textContent)).toEqual(["1Off track", "2Watch", "1On track"]);
  });

  it("renders nothing when no status is known", () => {
    const { container } = render(<StatusSummary label="Scorecard" statuses={[null]} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("StatusSpotlight", () => {
  it("lists off-track metrics before watch ones and skips on-track", () => {
    render(
      <StatusSpotlight
        metrics={[metric("A", "watch"), metric("B", "on_track"), metric("C", "off_track")]}
      />,
    );
    expect(screen.getByText("2 of 3 tracked metrics need attention")).toBeInTheDocument();
    const list = screen.getByRole("list", { name: "Metrics needing attention" });
    const names = within(list)
      .getAllByRole("listitem")
      .map((li) => li.textContent ?? "");
    expect(names[0]).toContain("Metric C");
    expect(names[1]).toContain("Metric A");
    expect(screen.queryByText("Metric B")).toBeNull();
    expect(screen.getByText("C basis")).toBeInTheDocument();
  });

  it("switches to a status check listing on-track metrics when nothing is flagged", () => {
    render(<StatusSpotlight metrics={[metric("A", "on_track"), undefined]} />);
    expect(screen.getByText("All headline metrics are on track")).toBeInTheDocument();
    expect(screen.getByText("Status check")).toBeInTheDocument();
    const list = screen.getByRole("list", { name: "Metrics on track" });
    expect(within(list).getByText("Metric A")).toBeInTheDocument();
  });
});
