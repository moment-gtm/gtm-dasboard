/** Widget → CSV/Excel export (FR-GEN-08). RLS is enforced server-side; the export is audited. */
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { api } from "@/api/client";
import { useFilters } from "@/state/filters";

export function ExportMenu({
  metricId,
  path = "/api/exports/widget",
  extra = {},
  label = "Export",
}: {
  metricId: string;
  path?: string;
  extra?: Record<string, string | null | undefined>;
  label?: string;
}) {
  const filters = useFilters();
  const href = (format: "csv" | "xlsx") =>
    api.downloadUrl(path, filters, { metric_id: metricId, format, ...extra });
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className="btn btn-ghost no-print"
          aria-label={`${label} ${metricId} data`}
          data-testid={`export-${metricId}`}
          style={{ padding: 4 }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
            <path
              d="M8 2v8m0 0l-3-3m3 3l3-3M3 13h10"
              stroke="currentColor"
              strokeWidth="1.5"
              fill="none"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content className="popover" sideOffset={6} style={{ padding: 4 }}>
          <DropdownMenu.Item asChild>
            <a
              className="block rounded px-3 py-1.5 no-underline"
              style={{ color: "var(--ink)" }}
              href={href("csv")}
              download
            >
              Download CSV
            </a>
          </DropdownMenu.Item>
          <DropdownMenu.Item asChild>
            <a
              className="block rounded px-3 py-1.5 no-underline"
              style={{ color: "var(--ink)" }}
              href={href("xlsx")}
              download
            >
              Download Excel
            </a>
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
