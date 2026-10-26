/**
 * DataRegister — TanStack Table register: sort, search, (server) pagination, row highlight.
 * Client mode sorts/filters locally; server mode delegates sort/search/page to the caller.
 */
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { useState } from "react";

export interface ServerControls {
  sort: string;
  order: "asc" | "desc";
  onSort: (sort: string, order: "asc" | "desc") => void;
  search: string;
  onSearch: (s: string) => void;
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}

export interface DataRegisterProps<T> {
  columns: ColumnDef<T, unknown>[];
  data: T[];
  caption: string;
  getRowId?: (row: T) => string;
  rowHighlight?: (row: T) => boolean;
  server?: ServerControls;
  searchPlaceholder?: string;
  testId?: string;
}

function SortIcon({ dir }: { dir: false | "asc" | "desc" }) {
  return (
    <span aria-hidden="true" style={{ color: "var(--ink-muted)", marginLeft: 4 }}>
      {dir === "asc" ? "▲" : dir === "desc" ? "▼" : "↕"}
    </span>
  );
}

export function DataRegister<T>({
  columns,
  data,
  caption,
  getRowId,
  rowHighlight,
  server,
  searchPlaceholder = "Search deals, accounts, owners…",
  testId = "data-register",
}: DataRegisterProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  const table = useReactTable({
    data,
    columns,
    getRowId,
    state: server
      ? { sorting: [{ id: server.sort, desc: server.order === "desc" }] }
      : { sorting, globalFilter },
    manualSorting: !!server,
    manualFiltering: !!server,
    onSortingChange: (updater) => {
      const current: SortingState = server
        ? [{ id: server.sort, desc: server.order === "desc" }]
        : sorting;
      const next = typeof updater === "function" ? updater(current) : updater;
      if (server) {
        const s = next[0];
        if (s) server.onSort(s.id, s.desc ? "desc" : "asc");
      } else setSorting(next);
    },
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: server ? undefined : getSortedRowModel(),
    getFilteredRowModel: server ? undefined : getFilteredRowModel(),
  });

  const rows = table.getRowModel().rows;
  const pages = server ? Math.max(1, Math.ceil(server.total / server.pageSize)) : 1;

  return (
    <div className="data-register flex flex-col gap-2" data-testid={testId}>
      <label className="flex items-center gap-2 text-sm">
        <span className="sr-only">Search</span>
        <input
          type="search"
          value={server ? server.search : globalFilter}
          onChange={(e) =>
            server ? server.onSearch(e.target.value) : setGlobalFilter(e.target.value)
          }
          placeholder={searchPlaceholder}
          className="w-full max-w-sm rounded-md px-3 py-1.5 text-sm"
          style={{ border: "1px solid var(--grid)", background: "var(--surface)" }}
          data-testid={`${testId}-search`}
        />
      </label>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((h) => {
                  const canSort = h.column.getCanSort();
                  const dir = h.column.getIsSorted();
                  return (
                    <th
                      key={h.id}
                      scope="col"
                      aria-sort={
                        dir === "asc" ? "ascending" : dir === "desc" ? "descending" : "none"
                      }
                      className="px-2 py-2 text-left font-medium whitespace-nowrap"
                      style={{ color: "var(--ink-2)", borderBottom: "1px solid var(--grid)" }}
                    >
                      {canSort ? (
                        <button
                          type="button"
                          className="btn btn-ghost"
                          style={{ padding: "2px 4px", color: "inherit", fontWeight: 500 }}
                          onClick={h.column.getToggleSortingHandler()}
                        >
                          {flexRender(h.column.columnDef.header, h.getContext())}
                          <SortIcon dir={dir} />
                        </button>
                      ) : (
                        flexRender(h.column.columnDef.header, h.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-2 py-4"
                  style={{ color: "var(--ink-2)" }}
                >
                  No rows match the search.
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr
                  key={r.id}
                  data-testid={`${testId}-row`}
                  style={{
                    borderBottom: "1px solid var(--grid)",
                    background: rowHighlight?.(r.original) ? "var(--accent-wash)" : undefined,
                  }}
                >
                  {r.getVisibleCells().map((c) => (
                    <td key={c.id} className="px-2 py-2 align-top tabular">
                      {flexRender(c.column.columnDef.cell, c.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {server ? (
        <nav className="flex items-center justify-between gap-2 text-sm" aria-label="Pagination">
          <span style={{ color: "var(--ink-2)" }}>
            Page {server.page} of {pages} · {server.total.toLocaleString("en-US")} rows
          </span>
          <span className="flex gap-2">
            <button
              type="button"
              className="btn"
              disabled={server.page <= 1}
              onClick={() => server.onPage(server.page - 1)}
            >
              Previous
            </button>
            <button
              type="button"
              className="btn"
              disabled={server.page >= pages}
              onClick={() => server.onPage(server.page + 1)}
              data-testid={`${testId}-next`}
            >
              Next
            </button>
          </span>
        </nav>
      ) : null}
    </div>
  );
}
