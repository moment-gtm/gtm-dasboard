/** FR-EXE-03 / EXE-08 — bookings by quarter vs quarterly target; current quarter marked QTD. */
import { ChartTable } from "@/components/charts/ChartTable";
import { GoalBarChart, type GoalBarDatum } from "@/components/charts/GoalBarChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useBookingsByQuarter } from "@/hooks/useExecutiveData";
import { useDrilldown } from "@/state/drilldown";

interface QuarterRow {
  quarter: string;
  label: string;
  bookings: number | null;
  target: number | null;
  met: boolean | null;
  is_current: boolean;
  is_future: boolean;
}

function toDatum(r: QuarterRow): GoalBarDatum {
  if (r.is_future)
    return { key: r.quarter, label: r.label, value: null, goal: r.target, tag: "Upcoming" };
  if (r.is_current)
    return { key: r.quarter, label: r.label, value: r.bookings, goal: r.target, tag: "QTD" };
  return {
    key: r.quarter,
    label: r.label,
    value: r.bookings,
    goal: r.target,
    tag: r.met ? "Met" : "Missed",
    tagTone: r.met ? "good" : "bad",
  };
}

export function BookingsByQuarter() {
  const q = useBookingsByQuarter();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as QuarterRow[];
  const data = rows.map(toDatum);
  const drill = (key: string) => {
    const r = rows.find((x) => x.quarter === key);
    if (r && !r.is_future) open({ metricId: "EXE-08", segment: key, title: `Bookings ${r.label}` });
  };
  return (
    <WidgetCard
      testId="widget-bookings-by-quarter"
      title="Bookings by quarter"
      description="Closed-won TCV per fiscal quarter against the quarterly target."
      metricId="EXE-08"
      prorated={q.data?.target_prorated}
      proratedBasis={q.data?.target_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
    >
      <GoalBarChart
        data={data}
        valueLabel="Bookings (TCV)"
        goalLabel="Quarterly target"
        onSelect={drill}
      />
      <ChartTable
        caption="Bookings by quarter vs target"
        rows={data}
        rowKey={(r) => r.key}
        columns={[
          { header: "Quarter", cell: (r) => r.label },
          { header: "Bookings", cell: (r) => <Money value={r.value} /> },
          { header: "Target", cell: (r) => <Money value={r.goal} /> },
          { header: "Status", cell: (r) => r.tag },
        ]}
        onSelect={(r) => drill(r.key)}
        selectLabel={(r) => `View ${r.label} deals`}
      />
    </WidgetCard>
  );
}
