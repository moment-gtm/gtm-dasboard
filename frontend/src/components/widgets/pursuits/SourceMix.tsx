/** FR-PUR-03 / PUR-03 — win rate and share of decided deals by deal source. */
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useSourceMix } from "@/hooks/usePursuitsData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";
import { PctBars } from "./PctBars";

interface SourceRow {
  source: string;
  won: number;
  lost: number;
  decided: number;
  tcv: number;
  share: number | null;
  win_rate: number | null;
}

export function SourceMix() {
  const q = useSourceMix();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as SourceRow[];
  return (
    <WidgetCard
      testId="widget-source-mix"
      title="Win rate by deal source"
      description="Decided deals over the last four quarters. Bars show win rate; the tick marks the goal."
      metricId="PUR-03"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.some((r) => r.decided) ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <PctBars
          testIdPrefix="source"
          rows={rows.map((r) => ({
            key: r.source,
            label: r.source,
            value: r.win_rate,
            goal: q.data?.goal ?? null,
            detail: `${r.won} won / ${r.decided} decided (${formatPct(r.share, 0)} of deals)`,
          }))}
          onSelect={(source) =>
            open({ metricId: "PUR-03", segment: source, title: `${source} — decided deals` })
          }
        />
        <ChartTable
          caption="Win rate by deal source"
          rows={rows}
          rowKey={(r) => r.source}
          columns={[
            { header: "Source", cell: (r) => r.source },
            { header: "Decided", cell: (r) => r.decided },
            { header: "Share of deals", cell: (r) => formatPct(r.share) },
            { header: "Win rate", cell: (r) => formatPct(r.win_rate) },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
