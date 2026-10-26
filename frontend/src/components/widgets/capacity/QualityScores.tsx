/** FR-CAP-04 / CAP-04 — bid quality score on won vs lost pursuits. */
import { ChartTable } from "@/components/charts/ChartTable";
import { WidgetCard } from "@/components/common/WidgetCard";
import { PctBars } from "@/components/widgets/pursuits/PctBars";
import { useQualityScores } from "@/hooks/useCapacityData";
import { useDrilldown } from "@/state/drilldown";

interface Row {
  outcome: "won" | "lost";
  label: string;
  count: number;
  avg_score: number | null;
  distribution: { score: number; count: number }[];
}

const fmt = (n: number | null | undefined) => (n == null ? "—" : n.toFixed(1));

export function QualityScores() {
  const q = useQualityScores();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    won_avg?: number | null;
    lost_avg?: number | null;
    gap?: number | null;
    max_score?: number;
  };
  const max = meta.max_score ?? 5;
  return (
    <WidgetCard
      testId="widget-quality-scores"
      title="Bid quality score"
      description="Average post-bid quality review score on won versus lost pursuits."
      metricId="CAP-04"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.some((r) => r.count) ? "no-match-filters" : false}
      emptyHint="No quality reviews in the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="quality-score-value">
          <span className="text-2xl font-semibold">{fmt(meta.won_avg)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            won vs {fmt(meta.lost_avg)} lost · gap {fmt(meta.gap)} of {max}
          </span>
        </p>
        <PctBars
          testIdPrefix="quality"
          rows={rows.map((r) => ({
            key: r.outcome,
            label: r.label,
            value: r.avg_score == null ? null : r.avg_score / max,
            detail: `${fmt(r.avg_score)} avg · ${r.count} reviews`,
            emphasis: r.outcome === "won",
          }))}
          onSelect={(outcome) =>
            open({ metricId: "CAP-04", segment: outcome, title: `Reviewed — ${outcome}` })
          }
        />
        <ChartTable
          caption="Quality score distribution by outcome"
          rows={rows}
          rowKey={(r) => r.outcome}
          columns={[
            { header: "Outcome", cell: (r) => r.label },
            { header: "Reviews", cell: (r) => r.count },
            { header: "Average", cell: (r) => fmt(r.avg_score) },
            {
              header: "Scores 1–5",
              cell: (r) => r.distribution.map((d) => `${d.score}: ${d.count}`).join(" · "),
            },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
