/** FR-CAP-03 / CAP-03 — cost of sale (restricted). Rendered only for restricted personas. */
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { PctBars } from "@/components/widgets/pursuits/PctBars";
import { useCostOfSale } from "@/hooks/useCapacityData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";

interface Row {
  quarter: string;
  label: string;
  pursuits: number;
  hours: number;
  cost: number;
  tcv: number;
  cost_of_sale: number | null;
  partial: boolean;
}

export function CostOfSale() {
  const q = useCostOfSale(true);
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as { cost?: number; tcv?: number };
  const peak = Math.max(0.0001, ...rows.map((r) => r.cost_of_sale ?? 0));
  return (
    <WidgetCard
      testId="widget-cost-of-sale"
      title="Cost of sale"
      description="Pursuit effort cost as a share of the TCV of decided pursuits (restricted)."
      metricId="CAP-03"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.tcv ? "no-match-filters" : false}
      emptyHint="No pursuit effort has been recorded for the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="cost-of-sale-value">
          <span className="text-2xl font-semibold">{formatPct(q.data?.value, 2)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            <Money value={meta.cost} /> pursuit cost on <Money value={meta.tcv} /> TCV
          </span>
        </p>
        <PctBars
          testIdPrefix="cost"
          rows={rows.map((r) => ({
            key: r.quarter,
            label: r.partial ? `${r.label} (in progress)` : r.label,
            value: r.cost_of_sale == null ? null : r.cost_of_sale / peak,
            detail: `${formatPct(r.cost_of_sale, 2)} · ${r.pursuits} pursuits`,
          }))}
          onSelect={(quarter) =>
            open({ metricId: "CAP-03", segment: quarter, title: `Pursuits — ${quarter}` })
          }
        />
        <ChartTable
          caption="Cost of sale by quarter"
          rows={rows}
          rowKey={(r) => r.quarter}
          columns={[
            { header: "Quarter", cell: (r) => r.label },
            { header: "Pursuits", cell: (r) => r.pursuits },
            { header: "Hours", cell: (r) => Math.round(r.hours).toLocaleString() },
            { header: "Cost", cell: (r) => <Money value={r.cost} /> },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
            { header: "Cost of sale", cell: (r) => formatPct(r.cost_of_sale, 2) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
