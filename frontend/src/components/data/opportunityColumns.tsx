/** Shared opportunity columns for drill-downs and registers (FR-GEN-06 CRM deep link). */
import type { ColumnDef } from "@tanstack/react-table";
import type { OpportunityRow } from "@/api/types";
import { Money } from "@/components/common/Money";
import { tokens } from "@/theme/tokens";
import { formatDate } from "@/utils/format";

const FLAG_STYLE: Record<string, { tone: keyof typeof tokens.status; icon: string }> = {
  Ageing: { tone: "watch", icon: "◷" },
  Stalled: { tone: "off_track", icon: "■" },
  "Past close date": { tone: "off_track", icon: "!" },
};

export function FlagBadge({ flag }: { flag: string | null }) {
  if (!flag) return null;
  const s = FLAG_STYLE[flag] ?? { tone: "watch" as const, icon: "•" };
  const t = tokens.status[s.tone];
  return (
    <span
      data-testid="flag-badge"
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap"
      style={{ background: t.bg, color: t.text }}
    >
      <span aria-hidden="true">{s.icon}</span>
      {flag}
    </span>
  );
}

export function CrmLink({ row }: { row: OpportunityRow }) {
  return (
    <a
      href={row.crm_url}
      target="_blank"
      rel="noreferrer"
      className="font-medium"
      style={{ color: "var(--accent-strong)" }}
      aria-label={`${row.name} — open CRM record in a new tab`}
      data-testid="crm-link"
    >
      {row.name}
    </a>
  );
}

export const opportunityColumns: ColumnDef<OpportunityRow, unknown>[] = [
  {
    id: "name",
    accessorKey: "name",
    header: "Opportunity",
    cell: ({ row }) => (
      <div className="flex flex-col">
        <CrmLink row={row.original} />
        <span className="text-xs" style={{ color: "var(--ink-muted)" }}>
          {row.original.opportunity_id}
        </span>
      </div>
    ),
  },
  { id: "account_name", accessorKey: "account_name", header: "Account" },
  { id: "stage", accessorKey: "stage", header: "Stage" },
  {
    id: "tcv",
    accessorKey: "tcv",
    header: "TCV",
    cell: ({ getValue }) => <Money value={getValue() as number} />,
  },
  {
    id: "close_date",
    accessorKey: "close_date",
    header: "Close",
    cell: ({ getValue }) => formatDate(getValue() as string),
  },
  {
    id: "days_in_stage",
    accessorKey: "days_in_stage",
    header: "Days in stage",
    cell: ({ getValue }) => (getValue() == null ? "—" : String(getValue())),
  },
  {
    id: "offering",
    accessorKey: "offering",
    header: "Offering",
    enableSorting: false,
    cell: ({ row }) => row.original.offering ?? row.original.offering_class,
  },
  { id: "lead_practice", accessorKey: "lead_practice", header: "Practice", enableSorting: false },
  { id: "owner_name", accessorKey: "owner_name", header: "Owner", enableSorting: false },
];

export const flagColumn: ColumnDef<OpportunityRow, unknown> = {
  id: "flag",
  accessorKey: "flag",
  header: "Flag",
  cell: ({ getValue }) => <FlagBadge flag={getValue() as string | null} />,
};
