/** FR-PUR-01 / PUR-01 — win rate by quarter, last eight quarters, against the goal. */
import { useState } from "react";
import { ChartTable } from "@/components/charts/ChartTable";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useWinRate } from "@/hooks/usePursuitsData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";
import { PctBars } from "./PctBars";

interface QuarterRow {
  quarter: string;
  label: string;
  won: number;
  lost: number;
  decided: number;
  win_rate: number | null;
  value_win_rate: number | null;
  partial: boolean;
}

export function WinRateTrend() {
  const q = useWinRate();
  const open = useDrilldown((s) => s.open);
  const [byValue, setByValue] = useState(false);
  const rows = (q.data?.breakdown ?? []) as unknown as QuarterRow[];
  const goal = q.data?.goal ?? null;
  const rate = (r: QuarterRow) => (byValue ? r.value_win_rate : r.win_rate);
  return (
    <WidgetCard
      variant="hero"
      testId="widget-win-rate"
      title="Win rate by quarter"
      description="Closed Won ÷ (Won + Lost). No-bid and client-cancelled deals are excluded. The tick marks the goal."
      metricId="PUR-01"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.some((r) => r.decided) ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="m-0 text-sm" data-testid="win-rate-headline">
            Trailing four quarters: <strong>{formatPct(q.data?.value)}</strong> (goal{" "}
            {formatPct(goal, 0)}+)
          </p>
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="checkbox"
              checked={byValue}
              onChange={(e) => setByValue(e.target.checked)}
              data-testid="win-rate-by-value"
            />
            Show by value (TCV)
          </label>
        </div>
        <PctBars
          testIdPrefix="winrate"
          rows={rows.map((r) => ({
            key: r.quarter,
            label: r.label,
            value: rate(r),
            goal,
            detail: `${r.won} won / ${r.decided} decided`,
            badge: r.partial ? "in progress" : undefined,
          }))}
          onSelect={(quarter) =>
            open({
              metricId: "PUR-01",
              segment: quarter,
              title: `${rows.find((r) => r.quarter === quarter)?.label ?? quarter} — decided deals`,
            })
          }
        />
        <ChartTable
          caption="Win rate by quarter"
          rows={rows}
          rowKey={(r) => r.quarter}
          columns={[
            { header: "Quarter", cell: (r) => r.label },
            { header: "Won", cell: (r) => r.won },
            { header: "Lost", cell: (r) => r.lost },
            { header: "Win rate (count)", cell: (r) => formatPct(r.win_rate) },
            { header: "Win rate (value)", cell: (r) => formatPct(r.value_win_rate) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
