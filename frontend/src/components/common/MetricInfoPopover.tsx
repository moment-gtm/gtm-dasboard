/** Metric ID, plain definition, sources, owner and last refresh on demand (FR-GEN-07). */
import * as Popover from "@radix-ui/react-popover";
import { useMetricMeta } from "@/hooks/useReference";
import { formatDateTime } from "@/utils/format";

export function MetricInfoPopover({ id }: { id: string }) {
  const { meta, isLoading, isError } = useMetricMeta(id);
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          className="btn btn-ghost"
          aria-label={`About metric ${id}`}
          data-testid={`metric-info-${id}`}
          style={{ padding: 4 }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
            <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.4" />
            <path
              d="M8 7v4.2M8 4.6v.2"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="popover"
          sideOffset={6}
          collisionPadding={12}
          style={{ maxWidth: 360 }}
          data-testid={`metric-info-content-${id}`}
        >
          {isLoading ? (
            <p className="m-0">Loading definition…</p>
          ) : isError || !meta ? (
            <p className="m-0">Definition for {id} is unavailable.</p>
          ) : (
            <div className="flex flex-col gap-2">
              <p className="m-0 font-semibold">
                <span
                  className="mr-2 rounded px-1.5 py-0.5 text-xs tabular"
                  style={{ background: "var(--accent-wash)", color: "var(--accent-strong)" }}
                >
                  {meta.metric_id}
                </span>
                {meta.name}
              </p>
              <p className="m-0">{meta.definition}</p>
              <p className="m-0" style={{ color: "var(--ink-2)" }}>
                <strong>Calculation:</strong> {meta.calculation}
              </p>
              {meta.goal_label ? (
                <p className="m-0" style={{ color: "var(--ink-2)" }}>
                  <strong>Goal / bands:</strong> {meta.goal_label}
                </p>
              ) : null}
              <p className="m-0" style={{ color: "var(--ink-2)" }}>
                <strong>Sources:</strong>{" "}
                {meta.sources.map((s) => `${s.source_id} ${s.name}`).join("; ")}
              </p>
              <p className="m-0" style={{ color: "var(--ink-2)" }}>
                <strong>Owner:</strong> {meta.owner} · <strong>Refresh:</strong> {meta.refresh}
              </p>
              <p className="m-0" style={{ color: "var(--ink-2)" }}>
                <strong>Last successful refresh:</strong> {formatDateTime(meta.last_refresh)}
              </p>
              {!meta.period_sensitive ? (
                <p className="m-0 text-xs" style={{ color: "var(--ink-muted)" }}>
                  Not affected by the period filter (fixed window by definition).
                </p>
              ) : null}
            </div>
          )}
          <Popover.Arrow fill="white" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
