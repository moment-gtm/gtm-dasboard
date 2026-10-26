/**
 * MatrixGrid — rows × columns of categorical cells (Sold / Open / Not addressed). Each cell is
 * shape + letter + colour (never colour alone) and a real button so it is keyboard operable.
 */
import { tokens } from "@/theme/tokens";

export type CellState = "sold" | "open" | "not_addressed";

const CELL: Record<CellState, { label: string; glyph: string; fill: string; ink: string }> = {
  sold: { label: "Sold", glyph: "●", fill: tokens.ordinal.strong, ink: "#ffffff" },
  open: { label: "Open", glyph: "◐", fill: tokens.ordinal.light, ink: tokens.ink.primary },
  not_addressed: {
    label: "Not addressed",
    glyph: "○",
    fill: tokens.surface,
    ink: tokens.ink.secondary,
  },
};

export interface MatrixRow {
  key: string;
  label: string;
  sublabel?: string;
  cells: Record<string, CellState>;
}

export function MatrixLegend() {
  return (
    <ul className="m-0 flex list-none flex-wrap gap-x-5 gap-y-1 p-0 text-sm">
      {(Object.keys(CELL) as CellState[]).map((s) => (
        <li key={s} className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            style={{
              width: 18,
              height: 18,
              borderRadius: 3,
              background: CELL[s].fill,
              color: CELL[s].ink,
              border: `1px solid ${tokens.axis}`,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 11,
            }}
          >
            {CELL[s].glyph}
          </span>
          {CELL[s].label}
        </li>
      ))}
    </ul>
  );
}

export function MatrixGrid({
  rows,
  columns,
  onSelectRow,
  caption,
  testId,
}: {
  rows: MatrixRow[];
  columns: string[];
  onSelectRow?: (row: MatrixRow) => void;
  caption: string;
  testId: string;
}) {
  return (
    <div className="overflow-x-auto" data-testid={testId}>
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            <th scope="col" className="p-1 text-left">
              Account
            </th>
            {columns.map((c) => (
              <th key={c} scope="col" className="p-1 text-center text-xs font-medium">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} data-testid={`${testId}-row-${r.key}`}>
              <th scope="row" className="p-1 text-left font-normal">
                <button
                  type="button"
                  className="text-left"
                  style={{ background: "transparent", border: 0, cursor: "pointer", padding: 0 }}
                  onClick={() => onSelectRow?.(r)}
                  aria-label={`Open ${r.label} account detail`}
                >
                  <span className="font-medium" style={{ color: "var(--accent-strong)" }}>
                    {r.label}
                  </span>
                  {r.sublabel ? (
                    <span className="block text-xs" style={{ color: "var(--ink-2)" }}>
                      {r.sublabel}
                    </span>
                  ) : null}
                </button>
              </th>
              {columns.map((c) => {
                const s = r.cells[c] ?? "not_addressed";
                const d = CELL[s];
                return (
                  <td
                    key={c}
                    className="p-0.5 text-center"
                    title={`${r.label} · ${c}: ${d.label}`}
                    data-state={s}
                  >
                    <span
                      role="img"
                      aria-label={`${c}: ${d.label}`}
                      style={{
                        display: "inline-flex",
                        width: 28,
                        height: 24,
                        alignItems: "center",
                        justifyContent: "center",
                        borderRadius: 3,
                        background: d.fill,
                        color: d.ink,
                        border: `1px solid ${tokens.axis}`,
                      }}
                    >
                      {d.glyph}
                    </span>
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
