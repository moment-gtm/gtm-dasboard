/** Shared bar-row list for percentage breakdowns (win rate, share). Data-in only, tokens only. */
import { tokens } from "@/theme/tokens";
import { formatPct } from "@/utils/format";

export interface PctBarRow {
  key: string;
  label: string;
  /** 0..1 or null when nothing was decided */
  value: number | null;
  detail: string;
  /** optional goal marker, 0..1 */
  goal?: number | null;
  emphasis?: boolean;
  badge?: string;
}

export function PctBars({
  rows,
  onSelect,
  testIdPrefix,
}: {
  rows: PctBarRow[];
  onSelect?: (key: string) => void;
  testIdPrefix: string;
}) {
  return (
    <ul className="m-0 flex list-none flex-col gap-2 p-0">
      {rows.map((r) => (
        <li key={r.key}>
          <button
            type="button"
            className="flex w-full flex-col gap-1 rounded p-1 text-left"
            style={{
              background: "transparent",
              border: 0,
              cursor: onSelect ? "pointer" : "default",
            }}
            onClick={() => onSelect?.(r.key)}
            data-testid={`${testIdPrefix}-${r.key}`}
            aria-label={`${r.label}: ${r.value == null ? "no decided deals" : formatPct(r.value)}, ${r.detail}${r.badge ? `, ${r.badge}` : ""}`}
          >
            <span className="flex justify-between gap-2 text-sm">
              <span style={{ fontWeight: r.emphasis ? 700 : 500 }}>
                {r.emphasis ? <span aria-hidden="true">★ </span> : null}
                {r.label}
                {r.badge ? <span style={{ color: "var(--ink-2)" }}> · {r.badge}</span> : null}
              </span>
              <span style={{ color: "var(--ink-2)" }}>
                {r.value == null ? "—" : formatPct(r.value)} · {r.detail}
              </span>
            </span>
            <span
              aria-hidden="true"
              style={{
                position: "relative",
                height: 10,
                borderRadius: 4,
                background: tokens.grid,
              }}
            >
              <span
                style={{
                  position: "absolute",
                  inset: 0,
                  width: `${Math.min(100, (r.value ?? 0) * 100)}%`,
                  borderRadius: 4,
                  background: r.emphasis ? tokens.series[1] : tokens.series[0],
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
          </button>
        </li>
      ))}
    </ul>
  );
}
