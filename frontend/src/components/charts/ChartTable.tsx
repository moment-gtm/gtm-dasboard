/** Table-view twin of a chart — the WCAG-clean, keyboard-reachable equivalent (dataviz rule). */
import type { ReactNode } from "react";

export interface ChartTableColumn<T> {
  header: string;
  cell: (row: T) => ReactNode;
}

export function ChartTable<T>({
  caption,
  rows,
  columns,
  rowKey,
  onSelect,
  selectLabel,
}: {
  caption: string;
  rows: T[];
  columns: ChartTableColumn<T>[];
  rowKey: (row: T) => string;
  onSelect?: (row: T) => void;
  selectLabel?: (row: T) => string;
}) {
  return (
    <details className="text-sm">
      <summary className="cursor-pointer" style={{ color: "var(--ink-2)" }}>
        Show data table
      </summary>
      <div className="overflow-x-auto">
        <table className="mt-2 w-full border-collapse tabular">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {columns.map((c) => (
                <th
                  key={c.header}
                  scope="col"
                  className="px-2 py-1 text-left font-medium"
                  style={{ color: "var(--ink-2)", borderBottom: "1px solid var(--grid)" }}
                >
                  {c.header}
                </th>
              ))}
              {onSelect ? <th className="sr-only">Drill-down</th> : null}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={rowKey(r)} style={{ borderBottom: "1px solid var(--grid)" }}>
                {columns.map((c) => (
                  <td key={c.header} className="px-2 py-1">
                    {c.cell(r)}
                  </td>
                ))}
                {onSelect ? (
                  <td className="px-2 py-1">
                    <button type="button" className="btn" onClick={() => onSelect(r)}>
                      {selectLabel ? selectLabel(r) : "View deals"}
                    </button>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
