/** FR-PUR-05 / PUR-06 — margin at bid vs in delivery (restricted). Rendered only for restricted personas. */
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useMargin } from "@/hooks/usePursuitsData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";
import { PctBars } from "./PctBars";

interface Row {
  quarter: string;
  label: string;
  deals: number;
  tcv: number;
  bid_margin: number | null;
  delivery_margin: number | null;
  erosion: number | null;
}

const points = (r: number | null | undefined) => (r == null ? "—" : `${(r * 100).toFixed(1)} pts`);

export function MarginBidVsDelivery() {
  const q = useMargin(true);
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    bid_margin?: number | null;
    delivery_margin?: number | null;
  };
  return (
    <WidgetCard
      testId="widget-margin"
      title="Margin: bid vs delivery"
      description="TCV-weighted margin at bid compared with delivery margin on closed-won deals (restricted)."
      metricId="PUR-06"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.some((r) => r.deals) ? "no-match-filters" : false}
      emptyHint="No won deals with delivery margin yet — margin appears 90 days after close."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="margin-value">
          <span className="text-2xl font-semibold">{points(q.data?.value)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            erosion · {formatPct(meta.bid_margin)} at bid → {formatPct(meta.delivery_margin)} in
            delivery
          </span>
        </p>
        <PctBars
          testIdPrefix="margin"
          rows={rows
            .filter((r) => r.deals)
            .map((r) => ({
              key: r.quarter,
              label: r.label,
              value: r.delivery_margin,
              goal: r.bid_margin,
              detail: `${points(r.erosion)} erosion · ${r.deals} deals`,
            }))}
          onSelect={(quarter) =>
            open({ metricId: "PUR-06", segment: quarter, title: `Won — ${quarter}` })
          }
        />
        <ChartTable
          caption="Margin at bid vs delivery by close quarter"
          rows={rows}
          rowKey={(r) => r.quarter}
          columns={[
            { header: "Quarter", cell: (r) => r.label },
            { header: "Deals", cell: (r) => r.deals },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
            { header: "Bid margin", cell: (r) => formatPct(r.bid_margin) },
            { header: "Delivery margin", cell: (r) => formatPct(r.delivery_margin) },
            { header: "Erosion", cell: (r) => points(r.erosion) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
