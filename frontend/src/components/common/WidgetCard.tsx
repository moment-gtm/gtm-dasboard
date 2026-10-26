/**
 * Standard widget frame: title, one-line description, metric ID & inline sources (when global
 * "Show metric IDs and sources" is switched on), info + export slots, optional status and
 * pro-rated badge; owns loading / empty / error states (FR-GEN-07/08/13).
 */
import * as Tooltip from "@radix-ui/react-tooltip";
import type { ReactNode } from "react";
import type { StatusValue } from "@/api/types";
import { useMetricMeta } from "@/hooks/useReference";
import { useShowMetricIds } from "@/state/metricIds";
import { EmptyState, type EmptyReason } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { ExportMenu } from "./ExportMenu";
import { MetricInfoPopover } from "./MetricInfoPopover";
import { StatusBadge } from "./StatusBadge";

export function ProratedBadge({ basis }: { basis: string | null }) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <span
          tabIndex={0}
          data-testid="prorated-badge"
          className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
          style={{ background: "var(--accent-wash)", color: "var(--accent-strong)" }}
        >
          Pro-rated target
        </span>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content className="popover" sideOffset={6} style={{ maxWidth: 320 }}>
          {basis ??
            "No planned target at this filter grain; the parent target is pro-rated by pipeline share."}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

export function MetricTraceabilityBadges({
  metricId,
  sources,
}: {
  metricId: string;
  sources?: string[];
}) {
  const { meta } = useMetricMeta(metricId);
  const sourceIds = sources?.length ? sources : (meta?.sources.map((s) => s.source_id) ?? []);
  const sourceTitle = meta?.sources.length
    ? meta.sources.map((s) => `${s.source_id} ${s.name}`).join("; ")
    : sourceIds.join(", ");
  return (
    <>
      <span
        className="rounded px-1.5 py-0.5 text-xs tabular"
        style={{
          background: "var(--page)",
          color: "var(--ink-2)",
          border: "1px solid var(--border)",
        }}
        data-testid="metric-id-chip"
      >
        {metricId}
      </span>
      {sourceIds.length > 0 ? (
        <span
          className="rounded px-1.5 py-0.5 text-xs tabular"
          style={{
            background: "var(--accent-wash)",
            color: "var(--accent-strong)",
          }}
          title={sourceTitle}
          data-testid="metric-sources-chip"
        >
          {sourceIds.join(" · ")}
        </span>
      ) : null}
    </>
  );
}

export interface WidgetCardProps {
  title: string;
  description: string;
  /** Bento emphasis: "hero" = the tile a module leads with (accent rule + wash). */
  variant?: "default" | "hero";
  /** Small uppercase label above the title, e.g. "FY26 · Headline". */
  eyebrow?: string;
  /** Big-number slot rendered under the header (hero tiles). Hidden while loading / on error. */
  headline?: ReactNode;
  metricId?: string;
  sources?: string[];
  status?: StatusValue | null;
  statusBasis?: string | null;
  prorated?: boolean;
  proratedBasis?: string | null;
  isLoading?: boolean;
  isFetching?: boolean;
  error?: unknown;
  onRetry?: () => void;
  empty?: EmptyReason | false;
  emptyHint?: string;
  exportable?: boolean;
  className?: string;
  children?: ReactNode;
  testId?: string;
}

export function WidgetCard({
  title,
  description,
  variant = "default",
  eyebrow,
  headline,
  metricId,
  sources,
  status,
  statusBasis,
  prorated,
  proratedBasis,
  isLoading,
  isFetching,
  error,
  onRetry,
  empty,
  emptyHint,
  exportable = true,
  className = "",
  children,
  testId,
}: WidgetCardProps) {
  const showMetricIds = useShowMetricIds();
  const headingId = `${testId ?? `widget-${metricId}`}-title`;
  let body: ReactNode;
  if (isLoading) body = <div className="skeleton" style={{ height: 160 }} aria-label="Loading" />;
  else if (error) body = <ErrorState error={error} onRetry={onRetry} />;
  else if (empty) body = <EmptyState reason={empty} hint={emptyHint} />;
  else body = children;

  return (
    <section
      aria-labelledby={headingId}
      className={`card flex min-w-0 flex-col gap-4 p-5 ${variant === "hero" ? "tile-hero" : ""} ${className}`}
      data-testid={testId ?? `widget-${metricId}`}
      data-variant={variant}
    >
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          {eyebrow ? <p className="eyebrow m-0 mb-1">{eyebrow}</p> : null}
          <div className="flex flex-wrap items-center gap-2">
            <h2
              id={headingId}
              className={`m-0 font-semibold tracking-tight ${variant === "hero" ? "text-xl" : "text-[17px]"}`}
              style={{ color: "var(--nav)" }}
            >
              {title}
            </h2>
            {showMetricIds && metricId ? (
              <MetricTraceabilityBadges metricId={metricId} sources={sources} />
            ) : null}
            {!isLoading && !error && status ? (
              <StatusBadge status={status} basis={statusBasis} />
            ) : null}
            {!isLoading && !error && prorated ? (
              <ProratedBadge basis={proratedBasis ?? null} />
            ) : null}
          </div>
          <p className="m-0 mt-1 text-[13px] leading-relaxed" style={{ color: "var(--ink-2)" }}>
            {description}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {metricId ? <MetricInfoPopover id={metricId} /> : null}
          {metricId && exportable ? <ExportMenu metricId={metricId} /> : null}
        </div>
      </header>
      {headline && !isLoading && !error && !empty ? (
        <div data-testid="widget-headline">{headline}</div>
      ) : null}
      <div style={{ opacity: isFetching && !isLoading ? 0.6 : 1, transition: "opacity .15s" }}>
        {body}
      </div>
    </section>
  );
}
