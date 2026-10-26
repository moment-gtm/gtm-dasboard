/** FR-OFF-04 / OFF-04 — asset reuse in proposals; flags low-reuse and refresh-due assets. */
import { DataRegister } from "@/components/data/DataRegister";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAssetReuse } from "@/hooks/useOfferingsData";
import type { ColumnDef } from "@tanstack/react-table";

interface Asset {
  asset_id: string;
  title: string;
  asset_type: string;
  offering: string | null;
  practice: string | null;
  uses: number;
  days_since_refresh: number | null;
  low_reuse: boolean;
  refresh_due: boolean;
}

const columns: ColumnDef<Asset, unknown>[] = [
  { accessorKey: "title", header: "Asset" },
  { accessorKey: "asset_type", header: "Type" },
  { accessorKey: "practice", header: "Practice", cell: (c) => c.getValue<string | null>() ?? "—" },
  { accessorKey: "uses", header: "Uses (12 mo)" },
  {
    accessorKey: "days_since_refresh",
    header: "Days since refresh",
    cell: (c) => c.getValue<number | null>() ?? "—",
  },
  {
    id: "flags",
    header: "Flags",
    accessorFn: (r) =>
      [r.low_reuse ? "Low reuse" : "", r.refresh_due ? "Refresh due" : ""]
        .filter(Boolean)
        .join(", "),
    cell: (c) => {
      const flags = c.getValue<string>();
      return flags ? (
        <span>
          <span aria-hidden="true">⚠ </span>
          {flags}
        </span>
      ) : (
        "—"
      );
    },
  },
];

export function AssetReuse() {
  const q = useAssetReuse();
  const rows = (q.data?.breakdown ?? []) as unknown as Asset[];
  const meta = (q.data?.meta ?? {}) as {
    low_reuse?: number;
    refresh_due?: number;
    total_uses?: number;
    low_reuse_uses?: number;
    refresh_due_days?: number;
  };
  return (
    <WidgetCard
      testId="widget-asset-reuse"
      title="Asset reuse"
      description="How often each knowledge-base asset was used in proposals over the last 12 months."
      metricId="OFF-04"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
      emptyHint="No knowledge-base assets match the current vertical filter."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="reuse-summary">
          <strong>{meta.total_uses}</strong> uses across {rows.length} assets ·{" "}
          <strong>{meta.low_reuse}</strong> used fewer than {meta.low_reuse_uses} times ·{" "}
          <strong>{meta.refresh_due}</strong> not refreshed in {meta.refresh_due_days}+ days
        </p>
        <DataRegister
          testId="asset-register"
          caption="Asset reuse"
          columns={columns}
          data={rows}
          getRowId={(r) => r.asset_id}
          rowHighlight={(r) => r.low_reuse || r.refresh_due}
          searchPlaceholder="Search assets"
        />
      </div>
    </WidgetCard>
  );
}
