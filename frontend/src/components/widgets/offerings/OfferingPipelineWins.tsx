/** FR-OFF-01 / OFF-01 — open pipeline and FY wins by offering, with the offering-led share. */
import { ChartTable } from "@/components/charts/ChartTable";
import { StackedSplitChart } from "@/components/charts/StackedSplitChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useByOffering } from "@/hooks/useOfferingsData";
import { formatPct } from "@/utils/format";

interface Row {
  offering: string;
  open_tcv: number;
  open_count: number;
  won_tcv: number;
  won_count: number;
  total_tcv: number;
}

export function OfferingPipelineWins() {
  const q = useByOffering();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as { untagged_tcv?: number };
  return (
    <WidgetCard
      variant="hero"
      testId="widget-offering-pipeline"
      title="Pipeline and wins by offering"
      description="Open pipeline and fiscal-year wins for each named offering."
      metricId="OFF-01"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="offering-led-share">
          <strong>{formatPct(q.data?.value)}</strong> of pipeline and wins is offering-led
          {meta.untagged_tcv ? (
            <>
              {" "}
              · <Money value={meta.untagged_tcv} /> has no offering tagged
            </>
          ) : null}
        </p>
        <StackedSplitChart
          ariaLabel="Open pipeline and won TCV by offering"
          parts={[
            { key: "open", label: "Open pipeline" },
            { key: "won", label: "Won FYTD" },
          ]}
          data={rows.map((r) => ({ category: r.offering, open: r.open_tcv, won: r.won_tcv }))}
        />
        <ChartTable
          caption="Pipeline and wins by offering"
          rows={rows}
          rowKey={(r) => r.offering}
          columns={[
            { header: "Offering", cell: (r) => r.offering },
            { header: "Open", cell: (r) => <Money value={r.open_tcv} /> },
            { header: "Open deals", cell: (r) => r.open_count },
            { header: "Won", cell: (r) => <Money value={r.won_tcv} /> },
            { header: "Won deals", cell: (r) => r.won_count },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
