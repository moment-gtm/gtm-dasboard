/**
 * RunwayChart — one horizontal track: committed segments stacked left→right (ordinal blue ramp,
 * 2px surface gaps), with target and pace markers. Segments are keyboard-operable buttons.
 * Data in only.
 */
import { tokens } from "@/theme/tokens";
import { formatMoney } from "@/utils/format";

export interface RunwaySegment {
  key: string;
  label: string;
  value: number;
}
export interface RunwayMarker {
  key: string;
  label: string;
  value: number;
}

const FILLS = [tokens.ordinal.strong, tokens.ordinal.mid, tokens.ordinal.light];

export function RunwayChart({
  segments,
  markers,
  onSelect,
  height = 36,
}: {
  segments: RunwaySegment[];
  markers: RunwayMarker[];
  onSelect?: (key: string) => void;
  height?: number;
}) {
  const total = segments.reduce((s, x) => s + Math.max(0, x.value), 0);
  const max = Math.max(total, ...markers.map((m) => m.value), 1) * 1.04;
  const pct = (v: number) => `${(Math.max(0, v) / max) * 100}%`;
  let acc = 0;
  const summary = [
    ...segments.map((s) => `${s.label} ${formatMoney(s.value)}`),
    ...markers.map((m) => `${m.label} ${formatMoney(m.value)}`),
  ].join("; ");

  return (
    <div className="flex flex-col gap-2" data-testid="runway-chart">
      {/* role="group" (not img): the segments inside are focusable drill-down buttons. */}
      <div
        role="group"
        aria-label={`Bookings runway. ${summary}`}
        className="relative w-full"
        style={{ height: height + 30 }}
      >
        {/* track */}
        <div
          className="absolute left-0 w-full rounded"
          style={{ top: 14, height, background: "var(--page)", border: "1px solid var(--grid)" }}
        />
        {segments.map((s, i) => {
          const left = acc;
          acc += Math.max(0, s.value);
          const first = i === 0;
          const last = i === segments.length - 1;
          return (
            <button
              key={s.key}
              type="button"
              aria-label={`${s.label}: ${formatMoney(s.value)}. Show opportunities`}
              title={`${s.label}: ${formatMoney(s.value)}`}
              data-testid={`runway-seg-${s.key}`}
              onClick={() => onSelect?.(s.key)}
              className="absolute border-0 p-0"
              style={{
                top: 14,
                height,
                left: pct(left),
                width: `calc(${pct(s.value)} - 2px)`,
                background: FILLS[i % FILLS.length],
                borderRadius: `${first ? 4 : 0}px ${last ? 4 : 0}px ${last ? 4 : 0}px ${first ? 4 : 0}px`,
                cursor: onSelect ? "pointer" : "default",
              }}
            />
          );
        })}
        {markers.map((m) => (
          <div
            key={m.key}
            aria-hidden="true"
            className="absolute"
            style={{
              left: pct(m.value),
              top: 0,
              height: height + 28,
              transform: "translateX(-1px)",
            }}
          >
            <div
              style={{
                width: 2,
                height: height + 20,
                marginTop: 8,
                background: tokens.ink.primary,
              }}
            />
            <span
              className="absolute text-xs font-medium whitespace-nowrap"
              style={{
                top: -6,
                color: "var(--ink)",
                ...(m.value / max > 0.75 ? { right: 6 } : { left: 6 }),
              }}
            >
              {m.label}
            </span>
          </div>
        ))}
      </div>
      {/* legend + exact values (table-view equivalent) */}
      <ul
        className="m-0 flex list-none flex-wrap gap-x-5 gap-y-1 p-0 text-sm"
        data-testid="runway-legend"
      >
        {segments.map((s, i) => (
          <li key={s.key} className="flex items-center gap-1.5">
            <span
              aria-hidden="true"
              style={{
                width: 10,
                height: 10,
                borderRadius: 2,
                background: FILLS[i % FILLS.length],
              }}
            />
            <span style={{ color: "var(--ink-2)" }}>{s.label}</span>
            <span className="font-semibold">{formatMoney(s.value)}</span>
          </li>
        ))}
        {markers.map((m) => (
          <li key={m.key} className="flex items-center gap-1.5">
            <span
              aria-hidden="true"
              style={{ width: 2, height: 12, background: tokens.ink.primary }}
            />
            <span style={{ color: "var(--ink-2)" }}>{m.label}</span>
            <span className="font-semibold">{formatMoney(m.value)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
