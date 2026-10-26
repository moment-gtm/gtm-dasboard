/** FR-MKT-03 / MKT-03 — Campaign-sourced pipeline TCV by quarter and campaign, reconciled CRM <-> Marketing Automation. */
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { PctBars } from "@/components/widgets/pursuits/PctBars";
import { useCampaignSourced } from "@/hooks/useMarketData";
import { useDrilldown } from "@/state/drilldown";
import { formatMoney, formatPct, formatX } from "@/utils/format";

interface QuarterRow {
  quarter: string;
  label: string;
  deals: number;
  tcv: number;
  won_tcv: number;
  partial: boolean;
}

interface CampaignRow {
  campaign_id: string;
  campaign_name: string;
  channel: string;
  practice: string;
  platform: string;
  status: string;
  budget_usd: number;
  deals: number;
  tcv: number;
  won_deals: number;
  won_tcv: number;
  roi_multiple: number | null;
  share: number | null;
}

export function CampaignPipeline() {
  const q = useCampaignSourced();
  const open = useDrilldown((s) => s.open);
  const quarters = (q.data?.breakdown ?? []) as unknown as QuarterRow[];
  const meta = (q.data?.meta ?? {}) as {
    total_tcv?: number;
    total_deals?: number;
    active_campaigns?: number;
    reconciled?: boolean;
    reconciliation_variance_pct?: number;
    by_campaign?: CampaignRow[];
  };
  const campaigns = meta.by_campaign ?? [];
  const maxQuarterTcv = Math.max(1, ...quarters.map((r) => r.tcv));

  return (
    <WidgetCard
      testId="widget-campaign-pipeline"
      title="Campaign-sourced pipeline"
      description="Pipeline TCV created where a marketing campaign is the primary source, reconciled between CRM and Adobe Marketo / Journey Optimizer."
      metricId="MKT-03"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.total_deals ? "no-match-filters" : false}
      emptyHint="No campaign-sourced opportunities match the current filters."
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <p className="m-0 text-sm" data-testid="campaign-pipeline-summary">
            <span className="text-2xl font-semibold">{formatMoney(q.data?.value)}</span>{" "}
            <span style={{ color: "var(--ink-2)" }}>
              across {meta.total_deals ?? 0} deals · {meta.active_campaigns ?? 0} active campaigns
            </span>
          </p>
          <span
            className="rounded px-2 py-0.5 text-xs font-medium"
            style={{
              background: "var(--accent-wash)",
              color: "var(--accent-strong)",
            }}
            data-testid="campaign-reconciliation-badge"
          >
            {meta.reconciled !== false ? "✓ Reconciled" : "⚠ Variance"} CRM ↔ SRC-10 (
            {formatPct(meta.reconciliation_variance_pct ?? 0, 2)} delta)
          </span>
        </div>
        <PctBars
          testIdPrefix="campaign-quarter"
          rows={quarters.map((r) => ({
            key: r.quarter,
            label: r.partial ? `${r.label} (in progress)` : r.label,
            value: r.tcv / maxQuarterTcv,
            detail: `${formatMoney(r.tcv)} · ${r.deals} deals`,
          }))}
          onSelect={(quarter) =>
            open({
              metricId: "MKT-03",
              segment: quarter,
              title: `Campaign-sourced opportunities — ${quarter}`,
            })
          }
        />
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="campaign-table">
            <caption className="sr-only">Campaign-sourced pipeline by campaign</caption>
            <thead>
              <tr>
                {["Campaign", "Channel", "Practice", "Deals", "Pipeline TCV", "Won TCV", "ROI"].map(
                  (h) => (
                    <th key={h} scope="col" className="p-1 text-left">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.campaign_id} data-testid={`campaign-row-${c.campaign_id}`}>
                  <td className="p-1">
                    <button
                      type="button"
                      className="btn text-left"
                      onClick={() =>
                        open({
                          metricId: "MKT-03",
                          segment: c.campaign_id,
                          title: `Campaign-sourced — ${c.campaign_name}`,
                        })
                      }
                      data-testid={`campaign-drill-${c.campaign_id}`}
                    >
                      {c.campaign_name}
                    </button>
                  </td>
                  <td className="p-1">{c.channel}</td>
                  <td className="p-1">{c.practice}</td>
                  <td className="p-1 tabular">{c.deals}</td>
                  <td className="p-1 tabular">
                    <Money value={c.tcv} />
                  </td>
                  <td className="p-1 tabular">
                    <Money value={c.won_tcv} />
                  </td>
                  <td className="p-1 tabular">{formatX(c.roi_multiple)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ChartTable
          caption="Campaign-sourced pipeline by quarter"
          rows={quarters}
          rowKey={(r) => r.quarter}
          columns={[
            { header: "Quarter", cell: (r) => r.label },
            { header: "Deals", cell: (r) => r.deals },
            { header: "Pipeline TCV", cell: (r) => <Money value={r.tcv} /> },
            { header: "Won TCV", cell: (r) => <Money value={r.won_tcv} /> },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
