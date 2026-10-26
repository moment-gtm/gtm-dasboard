/** ProgressToTarget — labelled progress bars with an optional goal tick and status. Data in only. */
import type { StatusValue } from "@/api/types";
import { StatusBadge } from "@/components/common/StatusBadge";
import { tokens } from "@/theme/tokens";
import { formatPct } from "@/utils/format";

export interface ProgressRow {
  key: string;
  label: string;
  /** 0..1 */
  value: number | null;
  /** right-hand text, e.g. "23 of 24 certified" */
  detail: string;
  /** optional goal marker, 0..1 */
  goal?: number | null;
  status?: StatusValue | null;
}

export function ProgressToTarget({
  rows,
  testIdPrefix,
}: {
  rows: ProgressRow[];
  testIdPrefix: string;
}) {
  return (
    <ul className="m-0 flex list-none flex-col gap-3 p-0">
      {rows.map((r) => (
        <li key={r.key} data-testid={`${testIdPrefix}-${r.key}`} className="flex flex-col gap-1">
          <span className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <span className="font-medium">{r.label}</span>
            <span className="flex items-center gap-2" style={{ color: "var(--ink-2)" }}>
              {r.value == null ? "—" : formatPct(r.value, 0)} · {r.detail}
              {r.status ? <StatusBadge status={r.status} size="sm" /> : null}
            </span>
          </span>
          <span
            role="img"
            aria-label={`${r.label}: ${r.value == null ? "no data" : formatPct(r.value, 0)}${
              r.goal != null ? `, goal ${formatPct(r.goal, 0)}` : ""
            }`}
            style={{ position: "relative", height: 10, borderRadius: 4, background: tokens.grid }}
          >
            <span
              style={{
                position: "absolute",
                inset: 0,
                width: `${Math.min(100, (r.value ?? 0) * 100)}%`,
                borderRadius: 4,
                background: tokens.series[0],
              }}
            />
            {r.goal != null ? (
              <span
                style={{
                  position: "absolute",
                  top: -2,
                  bottom: -2,
                  left: `${Math.min(100, r.goal * 100)}%`,
                  width: 2.5,
                  background: tokens.ink.primary,
                }}
              />
            ) : null}
          </span>
        </li>
      ))}
    </ul>
  );
}
