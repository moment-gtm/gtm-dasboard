/**
 * Module headline wiring for the bento header: a scorecard strip and a spotlight tile, both fed by
 * a module hook that returns the module's headline MetricResults. The hook is only called inside
 * these components, so nothing is fetched until ModuleGate / the access check has rendered them.
 * The queries are the ones the widgets already use (TanStack Query dedupes them).
 */
import type { MetricResult } from "@/api/types";
import { StatusSpotlight } from "./StatusSpotlight";
import { StatusSummary } from "./StatusSummary";

export interface Headlines {
  metrics: (MetricResult | null | undefined)[];
  isLoading: boolean;
}

/** Collapse a list of module queries into Headlines. */
export function toHeadlines(
  qs: { data?: MetricResult | null; isLoading: boolean; fetchStatus?: string }[],
): Headlines {
  return {
    metrics: qs.map((q) => q.data),
    // Disabled (restricted-only) queries sit in "pending" with fetchStatus "idle" — ignore them.
    isLoading: qs.some((q) => q.isLoading && q.fetchStatus !== "idle"),
  };
}

export function HeadlineScorecard({
  label,
  useHeadlines,
}: {
  label: string;
  useHeadlines: () => Headlines;
}) {
  const h = useHeadlines();
  return <StatusSummary label={label} statuses={h.metrics.map((m) => m?.status)} />;
}

export function HeadlineSpotlight({
  useHeadlines,
  labels,
}: {
  useHeadlines: () => Headlines;
  labels?: Record<string, string>;
}) {
  const h = useHeadlines();
  return <StatusSpotlight metrics={h.metrics} labels={labels} isLoading={h.isLoading} />;
}
