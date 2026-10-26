/**
 * KPI stat tile: value + goal + StatusBadge + 4-quarter Sparkline. Clickable → drill-down.
 * Bento: a 4px status rule across the top echoes the StatusBadge (which still carries the text
 * + icon), so a leader can scan the strip for red/amber before reading a single number.
 */
import type { ReactNode } from "react";
import type { MetricResult } from "@/api/types";
import { MetricInfoPopover } from "@/components/common/MetricInfoPopover";
import { StatusBadge } from "@/components/common/StatusBadge";
import { MetricTraceabilityBadges, ProratedBadge } from "@/components/common/WidgetCard";
import { useShowMetricIds } from "@/state/metricIds";
import { tokens } from "@/theme/tokens";
import { formatByUnit } from "@/utils/format";
import { Sparkline } from "./Sparkline";

export function KpiCard({
  metric,
  label,
  sublabel,
  onSelect,
}: {
  metric: MetricResult;
  label?: string;
  sublabel?: ReactNode;
  onSelect?: () => void;
}) {
  const showMetricIds = useShowMetricIds();
  const fmt = (v: number | null) => formatByUnit(v, metric.unit);
  const rule = metric.status ? tokens.status[metric.status].fill : tokens.grid;
  return (
    <article
      className={`card relative flex min-w-0 flex-col gap-2 overflow-hidden p-4 pt-5 ${onSelect ? "card-hover" : ""}`}
      data-testid={`kpi-${metric.metric_id}`}
      data-status={metric.status ?? undefined}
      aria-label={`${metric.name} ${fmt(metric.value)}`}
    >
      <span
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-1"
        style={{ background: rule }}
      />
      <div className="flex items-start justify-between gap-1">
        <div className="min-w-0">
          <p
            className="m-0 text-xs font-semibold tracking-wide uppercase"
            style={{ color: "var(--ink-2)" }}
          >
            {label ?? metric.name}
          </p>
          {showMetricIds ? (
            <div className="mt-1 flex flex-wrap items-center gap-1">
              <MetricTraceabilityBadges metricId={metric.metric_id} sources={metric.sources} />
            </div>
          ) : null}
        </div>
        <MetricInfoPopover id={metric.metric_id} />
      </div>
      <button
        type="button"
        onClick={onSelect}
        disabled={!onSelect}
        className="m-0 border-0 bg-transparent p-0 text-left"
        style={{ cursor: onSelect ? "pointer" : "default", color: "var(--nav)" }}
        aria-label={`${metric.name}: ${fmt(metric.value)}. Show underlying opportunities`}
        data-testid={`kpi-value-${metric.metric_id}`}
      >
        <span className="hero-number" style={{ fontSize: "2rem" }}>
          {fmt(metric.value)}
        </span>
      </button>
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge status={metric.status} basis={metric.status_basis} size="sm" />
        {metric.target_prorated ? <ProratedBadge basis={metric.target_basis} /> : null}
      </div>
      <p className="m-0 text-xs leading-relaxed" style={{ color: "var(--ink-2)" }}>
        {metric.goal_label ?? (metric.goal != null ? `Goal ${fmt(metric.goal)}` : "")}
      </p>
      {sublabel ? (
        <p className="m-0 text-xs leading-relaxed" style={{ color: "var(--ink-2)" }}>
          {sublabel}
        </p>
      ) : null}
      <div
        className="mt-auto flex items-end justify-between gap-2 pt-2"
        style={{ borderTop: `1px solid ${tokens.grid}` }}
      >
        <Sparkline points={metric.sparkline} format={fmt} />
        <span className="text-xs" style={{ color: "var(--ink-muted)" }}>
          4-qtr trend
        </span>
      </div>
    </article>
  );
}
