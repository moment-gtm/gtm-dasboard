/** FR-MKT-01 / MKT-01 — Thought-leadership output & engagement (POVs published, downloads, engaged visits). */
import { ChartTable } from "@/components/charts/ChartTable";
import { WidgetCard } from "@/components/common/WidgetCard";
import { PctBars } from "@/components/widgets/pursuits/PctBars";
import { useThoughtLeadership } from "@/hooks/useMarketData";
import { formatCount, formatDate } from "@/utils/format";

interface QuarterRow {
  quarter: string;
  label: string;
  povs: number;
  downloads: number;
  engaged_visits: number;
  avg_dwell_seconds: number;
  social_shares: number;
  partial: boolean;
}

interface AssetRow {
  asset_id: string;
  title: string;
  asset_type: string;
  practice: string;
  platform: string;
  published_date: string;
  published_quarter: string;
  downloads: number;
  engaged_visits: number;
}

export function ThoughtLeadership() {
  const q = useThoughtLeadership();
  const rows = (q.data?.breakdown ?? []) as unknown as QuarterRow[];
  const meta = (q.data?.meta ?? {}) as {
    total_assets?: number;
    total_downloads?: number;
    total_engaged_visits?: number;
    assets?: AssetRow[];
  };
  const assets = meta.assets ?? [];
  const maxDownloads = Math.max(1, ...rows.map((r) => r.downloads));

  return (
    <WidgetCard
      variant="hero"
      testId="widget-thought-leadership"
      title="Thought-leadership output & engagement"
      description="POVs and whitepapers published per quarter with downloads and engaged visits (Adobe AEM + CJA)."
      metricId="MKT-01"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !q.data.value ? "no-match-filters" : false}
      emptyHint="No thought-leadership publications match the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="thought-leadership-summary">
          <span className="text-2xl font-semibold">{formatCount(q.data?.value)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            POVs published · {formatCount(meta.total_downloads)} downloads ·{" "}
            {formatCount(meta.total_engaged_visits)} engaged visits
          </span>
        </p>
        <PctBars
          testIdPrefix="tl-quarter"
          rows={rows.map((r) => ({
            key: r.quarter,
            label: r.partial ? `${r.label} (in progress)` : r.label,
            value: r.downloads / maxDownloads,
            detail: `${r.povs} POVs · ${formatCount(r.downloads)} downloads · ${formatCount(r.engaged_visits)} engaged visits`,
          }))}
        />
        <ChartTable
          caption="Thought-leadership publications by quarter"
          rows={rows}
          rowKey={(r) => r.quarter}
          columns={[
            { header: "Quarter", cell: (r) => r.label },
            { header: "POVs published", cell: (r) => r.povs },
            { header: "Downloads", cell: (r) => formatCount(r.downloads) },
            { header: "Engaged visits", cell: (r) => formatCount(r.engaged_visits) },
            { header: "Avg dwell (s)", cell: (r) => `${Math.round(r.avg_dwell_seconds)}s` },
          ]}
        />
        {assets.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="thought-leadership-assets">
              <caption className="sr-only">Published POV and thought-leadership assets</caption>
              <thead>
                <tr>
                  {[
                    "Asset",
                    "Type",
                    "Practice",
                    "Platform",
                    "Published",
                    "Downloads",
                    "Engaged visits",
                  ].map((h) => (
                    <th key={h} scope="col" className="p-1 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {assets.slice(0, 6).map((a) => (
                  <tr key={a.asset_id} data-testid={`tl-asset-${a.asset_id}`}>
                    <td className="p-1 font-medium">{a.title}</td>
                    <td className="p-1">{a.asset_type}</td>
                    <td className="p-1">{a.practice}</td>
                    <td className="p-1">{a.platform}</td>
                    <td className="p-1 whitespace-nowrap">{formatDate(a.published_date)}</td>
                    <td className="p-1 tabular">{formatCount(a.downloads)}</td>
                    <td className="p-1 tabular">{formatCount(a.engaged_visits)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </WidgetCard>
  );
}
