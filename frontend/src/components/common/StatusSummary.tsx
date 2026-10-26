/**
 * Scorecard strip: how many of a module's headline metrics are On track / Watch / Off track.
 * Counts the statuses the semantic layer already returned — no banding happens here. Each pill
 * is text + icon + colour (FR-GEN-05, NFR-08).
 */
import type { StatusValue } from "@/api/types";
import { StatusBadge } from "./StatusBadge";

const ORDER: StatusValue[] = ["off_track", "watch", "on_track"];

export function StatusSummary({
  label,
  statuses,
}: {
  label: string;
  statuses: (StatusValue | null | undefined)[];
}) {
  const counts = ORDER.map((s) => ({ s, n: statuses.filter((x) => x === s).length }));
  if (!statuses.some(Boolean)) return null;
  return (
    <div
      className="card flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3"
      data-testid="status-summary"
      style={{ borderRadius: 16 }}
    >
      <span className="text-sm font-semibold" style={{ color: "var(--nav)" }}>
        {label}
      </span>
      <ul className="m-0 flex list-none flex-wrap items-center gap-2 p-0">
        {counts.map(({ s, n }) => (
          <li key={s} className="flex items-center gap-1.5">
            <span className="text-lg font-bold tabular">{n}</span>
            <StatusBadge status={s} size="sm" />
          </li>
        ))}
      </ul>
    </div>
  );
}
