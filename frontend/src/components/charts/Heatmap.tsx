/**
 * Heatmap — 2-D grid of count + value per cell. Intensity is a single-hue ramp, but every cell also
 * prints its count and value, so colour is never the only signal (NFR-08). Data in only.
 */
import type { ReactNode } from "react";
import { tokens } from "@/theme/tokens";

export interface HeatmapCell {
  count: number;
  value: number;
}

export interface HeatmapColumn {
  key: string;
  label: ReactNode;
}

export interface HeatmapRow {
  key: string;
  label: string;
  cells: Record<string, HeatmapCell>;
}

export function Heatmap({
  rows,
  columns,
  formatValue,
  onSelect,
  ariaLabel,
}: {
  rows: HeatmapRow[];
  columns: HeatmapColumn[];
  formatValue: (v: number) => string;
  onSelect?: (rowKey: string, colKey: string) => void;
  ariaLabel: string;
}) {
  const max = Math.max(1, ...rows.flatMap((r) => columns.map((c) => r.cells[c.key]?.count ?? 0)));
  return (
    <div className="overflow-x-auto">
      <table
        className="w-full border-separate tabular"
        style={{ borderSpacing: 3 }}
        aria-label={ariaLabel}
      >
        <thead>
          <tr>
            <th scope="col" className="px-2 py-1 text-left text-sm font-medium">
              <span className="sr-only">Vertical</span>
            </th>
            {columns.map((c) => (
              <th key={c.key} scope="col" className="px-2 py-1 text-center text-sm font-medium">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}>
              <th scope="row" className="px-2 py-1 text-left text-sm font-medium whitespace-nowrap">
                {r.label}
              </th>
              {columns.map((c) => {
                const cell = r.cells[c.key] ?? { count: 0, value: 0 };
                const t = cell.count / max;
                const dark = t > 0.75;
                const content = (
                  <>
                    <span className="block text-base font-semibold">{cell.count}</span>
                    <span className="block text-xs">
                      {cell.count ? formatValue(cell.value) : "—"}
                    </span>
                  </>
                );
                return (
                  <td key={c.key} className="p-0 text-center">
                    <button
                      type="button"
                      disabled={!onSelect || cell.count === 0}
                      onClick={() => onSelect?.(r.key, c.key)}
                      aria-label={`${r.label}, ${c.key}: ${cell.count} deals, ${formatValue(cell.value)}`}
                      className="w-full rounded-md border-0 px-2 py-1.5"
                      style={{
                        background: cell.count
                          ? `color-mix(in srgb, ${tokens.ordinal.strong} ${Math.round(12 + t * 88)}%, ${tokens.surface})`
                          : tokens.page,
                        color: dark ? "#ffffff" : tokens.ink.primary,
                        cursor: onSelect && cell.count ? "pointer" : "default",
                      }}
                    >
                      {content}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
