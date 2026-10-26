/** FR-PUR-02 / PUR-02 — why Moment loses; the single most frequent reason is called out. */
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useLossReasons } from "@/hooks/usePursuitsData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";
import { PctBars } from "./PctBars";

interface ReasonRow {
  reason: string;
  count: number;
  tcv: number;
  share: number | null;
  most_frequent: boolean;
}

export function LossReasons() {
  const q = useLossReasons();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as ReasonRow[];
  return (
    <WidgetCard
      testId="widget-loss-reasons"
      title="Loss reasons"
      description="Closed Lost deals over the last four quarters by the reason recorded in CRM."
      metricId="PUR-02"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.length ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="loss-reason-basis">
          {q.data?.status_basis}
        </p>
        <PctBars
          testIdPrefix="loss"
          rows={rows.map((r) => ({
            key: r.reason,
            label: r.reason,
            value: r.share,
            detail: `${r.count} lost`,
            emphasis: r.most_frequent,
            badge: r.most_frequent ? "most frequent" : undefined,
          }))}
          onSelect={(reason) =>
            open({ metricId: "PUR-02", segment: reason, title: `Lost — ${reason}` })
          }
        />
        <ChartTable
          caption="Loss reasons"
          rows={rows}
          rowKey={(r) => r.reason}
          columns={[
            { header: "Reason", cell: (r) => r.reason },
            { header: "Lost deals", cell: (r) => r.count },
            { header: "Share", cell: (r) => formatPct(r.share) },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
