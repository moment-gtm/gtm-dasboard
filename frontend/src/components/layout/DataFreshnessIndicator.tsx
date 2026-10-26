/** Per-source freshness + staleness/failure banner (FR-GEN-09, NFR-02). */
import * as Popover from "@radix-ui/react-popover";
import type { SourceHealth } from "@/api/types";
import { useHealth } from "@/hooks/useReference";
import { tokens } from "@/theme/tokens";
import { formatDateTime } from "@/utils/format";

const TONE: Record<
  SourceHealth["status"],
  { key: keyof typeof tokens.status; label: string; icon: string }
> = {
  fresh: { key: "on_track", label: "Fresh", icon: "✓" },
  stale: { key: "watch", label: "Stale", icon: "!" },
  failed: { key: "off_track", label: "Failed", icon: "✕" },
};

function SourcePill({ s }: { s: SourceHealth }) {
  const t = TONE[s.status];
  const c = tokens.status[t.key];
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ background: c.bg, color: c.text }}
    >
      <span aria-hidden="true">{t.icon}</span>
      {t.label}
    </span>
  );
}

export function DataFreshnessIndicator() {
  const h = useHealth();
  const sources = h.data?.sources ?? [];
  const worst: SourceHealth["status"] = sources.some((s) => s.status === "failed")
    ? "failed"
    : sources.some((s) => s.status === "stale")
      ? "stale"
      : "fresh";
  const label = h.isError
    ? "Freshness unavailable"
    : worst === "fresh"
      ? "Data fresh"
      : worst === "stale"
        ? "Data stale"
        : "Source failed";
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          className="btn"
          data-testid="freshness-indicator"
          aria-label={`Data freshness: ${label}`}
        >
          {h.data ? <SourcePill s={{ ...sources[0], status: worst } as SourceHealth} /> : null}
          <span>{h.data ? `As of ${h.data.as_of_date}` : label}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="popover"
          sideOffset={6}
          align="end"
          style={{ minWidth: 320, maxWidth: 420 }}
        >
          <p className="m-0 mb-2 font-semibold">Data freshness by source</p>
          {h.isError ? <p className="m-0">Health endpoint unreachable.</p> : null}
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {sources.map((s) => (
              <li
                key={s.source_id}
                className="flex flex-col gap-0.5"
                data-testid={`freshness-${s.key}`}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="font-medium">
                    {s.source_id} · {s.name}
                  </span>
                  <SourcePill s={s} />
                </span>
                <span className="text-xs" style={{ color: "var(--ink-2)" }}>
                  Last success {formatDateTime(s.last_success)} · {s.cadence}
                  {s.message ? ` · ${s.message}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export function StalenessBanner() {
  const h = useHealth();
  if (!h.data) return null;
  const bad = h.data.sources.filter((s) => s.status !== "fresh");
  if (!h.data.stale && bad.length === 0) return null;
  const failed = bad.some((s) => s.status === "failed");
  const c = tokens.status[failed ? "off_track" : "watch"];
  return (
    <div
      role="alert"
      data-testid="staleness-banner"
      className="px-4 py-2 text-sm"
      style={{ background: c.bg, color: c.text }}
    >
      <strong>
        {failed ? "A data source failed to refresh." : "Some data is older than its refresh SLA."}
      </strong>{" "}
      {bad
        .map((s) => `${s.name} (${s.status}, last success ${formatDateTime(s.last_success)})`)
        .join("; ")}
      . Figures from these sources may be out of date.
    </div>
  );
}
