/** FR-OFF-05 / OFF-05 — assets released vs the build plan, by quarter, with reuse share. */
import { ChartTable } from "@/components/charts/ChartTable";
import { ProgressToTarget } from "@/components/charts/ProgressToTarget";
import { StatusBadge } from "@/components/common/StatusBadge";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAssetBuild } from "@/hooks/useOfferingsData";
import { formatPct } from "@/utils/format";
import type { StatusValue } from "@/api/types";

interface Quarter {
  quarter: string;
  label: string;
  planned: number;
  released: number;
  in_development: number;
  planned_items: number;
  partial: boolean;
}

export function AssetBuild() {
  const q = useAssetBuild();
  const rows = (q.data?.breakdown ?? []) as unknown as Quarter[];
  const meta = (q.data?.meta ?? {}) as {
    released?: number;
    in_development?: number;
    plan_pace?: number;
    annual_plan?: number;
    reuse_share?: number | null;
    reuse_status?: StatusValue | null;
    reuse_goal?: number | null;
    mean_build_weeks?: number | null;
    excluded_incomplete?: number;
  };
  return (
    <WidgetCard
      testId="widget-asset-build"
      title="Assets developed"
      description="Assets released this fiscal year against the build plan pace, and how many were reused."
      metricId="OFF-05"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      prorated={q.data?.target_prorated}
      proratedBasis={q.data?.target_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="build-summary">
          <span className="text-2xl font-semibold">{q.data?.value ?? 0}</span> released vs{" "}
          <strong>{meta.plan_pace?.toFixed(1)}</strong> planned to date (annual plan{" "}
          {meta.annual_plan}) · {meta.in_development} in development
          {meta.mean_build_weeks != null
            ? ` · ${meta.mean_build_weeks.toFixed(1)} weeks mean build time`
            : ""}
        </p>
        <div className="flex flex-col gap-1">
          <ProgressToTarget
            testIdPrefix="reuse"
            rows={[
              {
                key: "share",
                label: "Released assets reused in proposals",
                value: meta.reuse_share ?? null,
                goal: meta.reuse_goal ?? null,
                detail:
                  meta.reuse_goal != null ? `goal ${formatPct(meta.reuse_goal, 0)}` : "no goal set",
                status: meta.reuse_status ?? null,
              },
            ]}
          />
        </div>
        {meta.excluded_incomplete ? (
          <p className="m-0 text-sm" role="note" data-testid="build-incomplete">
            <span aria-hidden="true">⚠ </span>
            {meta.excluded_incomplete} released assets are excluded because their records are
            missing an asset ID or type (DQ-09).
          </p>
        ) : null}
        <ChartTable
          caption="Assets by quarter"
          rows={rows}
          rowKey={(r) => r.quarter}
          columns={[
            { header: "Quarter", cell: (r) => r.label },
            { header: "Planned", cell: (r) => r.planned },
            { header: "Released", cell: (r) => r.released },
            { header: "In development", cell: (r) => r.in_development },
          ]}
        />
        {q.data?.status ? <StatusBadge status={q.data.status} size="sm" /> : null}
      </div>
    </WidgetCard>
  );
}
