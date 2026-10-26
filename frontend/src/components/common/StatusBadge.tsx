/** Status as text + icon + colour — never colour alone (FR-GEN-05, NFR-08). */
import type { StatusValue } from "@/api/types";
import { tokens } from "@/theme/tokens";

const LABEL: Record<StatusValue, string> = {
  on_track: "On track",
  watch: "Watch",
  off_track: "Off track",
};

function Icon({ status }: { status: StatusValue }) {
  const c = tokens.status[status].fill;
  if (status === "on_track")
    return (
      <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="8" cy="8" r="7" fill={c} />
        <path
          d="M4.5 8.2l2.3 2.3 4.7-4.8"
          stroke="#fff"
          strokeWidth="1.8"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    );
  if (status === "watch")
    return (
      <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 1.5l7 12.5H1z" fill={c} />
        <path
          d="M8 6v3.6M8 11.6v.4"
          stroke={tokens.ink.primary}
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    );
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
      <rect x="1.5" y="1.5" width="13" height="13" rx="3" fill={c} />
      <path
        d="M5.2 5.2l5.6 5.6M10.8 5.2l-5.6 5.6"
        stroke="#fff"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function statusLabel(status: StatusValue): string {
  return LABEL[status];
}

export function StatusBadge({
  status,
  basis,
  size = "md",
}: {
  status: StatusValue | null | undefined;
  basis?: string | null;
  size?: "sm" | "md";
}) {
  if (!status) return null;
  const t = tokens.status[status];
  return (
    <span
      data-testid="status-badge"
      data-status={status}
      title={basis ?? undefined}
      className="inline-flex items-center gap-1 rounded-full font-medium whitespace-nowrap"
      style={{
        background: t.bg,
        color: t.text,
        padding: size === "sm" ? "1px 8px" : "2px 10px",
        fontSize: size === "sm" ? 12 : 13,
      }}
    >
      <Icon status={status} />
      {LABEL[status]}
      {basis ? <span className="sr-only">: {basis}</span> : null}
    </span>
  );
}
