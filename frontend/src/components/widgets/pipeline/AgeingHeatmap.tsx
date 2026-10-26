/** FR-PIP-02 / PIP-02 — stage × days-in-stage heatmap (count + TCV per cell). */
import { Heatmap, type HeatmapRow } from "@/components/charts/Heatmap";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAgeing } from "@/hooks/usePipelineData";
import { useDrilldown } from "@/state/drilldown";
import { formatMoney } from "@/utils/format";

interface Cell {
  count: number;
  tcv: number;
}
interface BucketMeta {
  key: string;
  label: string;
  review: boolean;
}

export function AgeingHeatmap() {
  const q = useAgeing();
  const open = useDrilldown((s) => s.open);
  const buckets = (q.data?.meta?.buckets ?? []) as BucketMeta[];
  const rows = (q.data?.breakdown ?? []) as unknown as ({ stage: string } & Record<
    string,
    unknown
  >)[];
  const heatRows: HeatmapRow[] = rows.map((r) => ({
    key: r.stage,
    label: r.stage,
    cells: Object.fromEntries(
      buckets.map((b) => {
        const c = r[b.key] as Cell | undefined;
        return [b.key, { count: c?.count ?? 0, value: c?.tcv ?? 0 }];
      }),
    ),
  }));
  return (
    <WidgetCard
      testId="widget-ageing-heatmap"
      title="Pipeline ageing"
      description="Open deals by stage and days in the current stage. Buckets past the review line are marked “review”. Select a cell to list its deals."
      metricId="PIP-02"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !q.data.value ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-2">
        <Heatmap
          ariaLabel="Open pipeline ageing by stage and days in stage"
          rows={heatRows}
          columns={buckets.map((b) => ({
            key: b.key,
            label: b.review ? `${b.label} (review)` : b.label,
          }))}
          formatValue={formatMoney}
          onSelect={(stage, bucket) => {
            const b = buckets.find((x) => x.key === bucket);
            open({
              metricId: "PIP-02",
              segment: `${stage}|${bucket}`,
              title: `${stage} — ${b?.label ?? bucket} in stage`,
            });
          }}
        />
        {q.data?.status_basis ? (
          <p className="m-0 text-sm" style={{ color: "var(--ink-2)" }}>
            {q.data.status_basis}
          </p>
        ) : null}
      </div>
    </WidgetCard>
  );
}
