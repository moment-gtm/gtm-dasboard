/** FR-EXE-02 — six north-star KPIs (EXE-01..06), each with value, goal, status and sparkline. */
import type { MetricResult } from "@/api/types";
import { KpiCard } from "@/components/charts/KpiCard";
import { KpiStrip } from "@/components/charts/KpiStrip";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Money } from "@/components/common/Money";
import { useKpis } from "@/hooks/useExecutiveData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";

const LABEL: Record<string, string> = {
  "EXE-01": "Bookings vs target",
  "EXE-02": "Pipeline coverage",
  "EXE-03": "Win rate",
  "EXE-04": "New pipeline created",
  "EXE-05": "Offering-led share",
  "EXE-06": "Average deal cycle",
};

function sublabel(m: MetricResult) {
  const meta = m.meta as Record<string, number | undefined>;
  switch (m.metric_id) {
    case "EXE-01":
      return (
        <>
          {meta.pct_of_target != null ? `${formatPct(meta.pct_of_target)} of target ` : ""}
          {m.target != null ? (
            <>
              (<Money value={m.target} />)
            </>
          ) : null}
          {m.attainment != null ? ` · ${formatPct(m.attainment, 0)} of pace` : ""}
        </>
      );
    case "EXE-03":
      return meta.won != null
        ? `${meta.won} won / ${meta.lost} lost · by value ${formatPct(meta.value_win_rate)}`
        : null;
    case "EXE-04":
      return m.attainment != null ? `${formatPct(m.attainment, 0)} of goal` : null;
    default:
      return null;
  }
}

export function NorthStarKpis() {
  const q = useKpis();
  const open = useDrilldown((s) => s.open);
  if (q.isLoading)
    return (
      <KpiStrip>
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="skeleton" style={{ height: 190 }} />
        ))}
      </KpiStrip>
    );
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data?.length) return <EmptyState reason="no-data" />;
  return (
    <section aria-label="North-star KPIs" style={{ opacity: q.isFetching ? 0.6 : 1 }}>
      <h2 className="sr-only">North-star KPIs</h2>
      <KpiStrip>
        {q.data.map((m) => (
          <KpiCard
            key={m.metric_id}
            metric={m}
            label={LABEL[m.metric_id]}
            sublabel={sublabel(m)}
            onSelect={() =>
              open({ metricId: m.metric_id, segment: null, title: LABEL[m.metric_id] ?? m.name })
            }
          />
        ))}
      </KpiStrip>
    </section>
  );
}
