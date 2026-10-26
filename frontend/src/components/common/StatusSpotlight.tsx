/**
 * Generic spotlight for any module: lists the module's headline metrics that are Off track or
 * Watch (worst first) with value, StatusBadge and the semantic layer's status basis. Statuses
 * come from the API — no banding here. When nothing is flagged it switches to a "status check"
 * listing the on-track metrics, so the tile still tells leadership what is going well.
 */
import type { MetricResult, StatusValue } from "@/api/types";
import { formatByUnit } from "@/utils/format";
import { SpotlightCard } from "./SpotlightCard";
import { StatusBadge } from "./StatusBadge";

const RANK: Record<StatusValue, number> = { off_track: 0, watch: 1, on_track: 2 };

export function StatusSpotlight({
  metrics,
  labels = {},
  isLoading,
  max = 4,
  testId = "spotlight-status",
}: {
  metrics: (MetricResult | null | undefined)[];
  labels?: Record<string, string>;
  isLoading?: boolean;
  max?: number;
  testId?: string;
}) {
  const known = metrics
    .filter((m): m is MetricResult => !!m?.status)
    .sort((a, b) => RANK[a.status!] - RANK[b.status!]);
  const flagged = known.filter((m) => m.status !== "on_track");
  const off = flagged.filter((m) => m.status === "off_track").length;
  const allClear = known.length > 0 && flagged.length === 0;
  const rows = allClear ? known : flagged;
  const title = flagged.length
    ? `${flagged.length} of ${known.length} tracked metric${known.length === 1 ? "" : "s"} need${flagged.length === 1 ? "s" : ""} attention`
    : allClear
      ? "All headline metrics are on track"
      : "No status available for the current filters";

  return (
    <SpotlightCard
      testId={testId}
      eyebrow={allClear ? "Status check" : "Needs your attention"}
      tone={allClear ? "ok" : "alert"}
      title={title}
      isLoading={isLoading && !known.length}
      stats={
        !known.length
          ? undefined
          : allClear
            ? [
                { label: "On track", value: known.length },
                { label: "Need attention", value: 0 },
              ]
            : [
                { label: "Off track", value: off },
                { label: "Watch", value: flagged.length - off },
              ]
      }
    >
      {rows.length ? (
        <ul
          className="m-0 flex list-none flex-col gap-2 p-0"
          aria-label={allClear ? "Metrics on track" : "Metrics needing attention"}
        >
          {rows.slice(0, max).map((m) => (
            <li
              key={m.metric_id}
              className="flex flex-col gap-1 rounded-xl px-3 py-2 text-sm"
              style={{ background: "var(--spotlight-row)" }}
            >
              <span className="flex items-center justify-between gap-2">
                <span className="min-w-0 truncate font-medium">
                  {labels[m.metric_id] ?? m.name}
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  <span className="font-semibold tabular">{formatByUnit(m.value, m.unit)}</span>
                  <StatusBadge status={m.status} size="sm" />
                </span>
              </span>
              {m.status_basis ? (
                <span className="text-xs" style={{ color: "var(--spotlight-muted)" }}>
                  {m.status_basis}
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </SpotlightCard>
  );
}
