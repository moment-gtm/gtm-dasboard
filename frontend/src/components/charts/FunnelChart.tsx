/**
 * FunnelChart — ordered stages as bars scaled by value, each showing count + value and the
 * conversion to the next stage. Stages are buttons (click selects, click again clears) so the
 * chart is keyboard operable and never colour-only (NFR-08). Data in only.
 */
import { tokens } from "@/theme/tokens";
import { formatPct } from "@/utils/format";

export interface FunnelStep {
  key: string;
  label: string;
  count: number;
  value: number;
  /** Conversion to the next step (0–1); null/undefined on the last step or when unknown. */
  conversion?: number | null;
  /** Secondary caption, e.g. "356 reached". */
  note?: string;
}

export function FunnelChart({
  steps,
  selectedKey,
  onSelect,
  formatValue,
  ariaLabel,
}: {
  steps: FunnelStep[];
  selectedKey?: string | null;
  onSelect?: (key: string) => void;
  formatValue: (v: number) => string;
  ariaLabel: string;
}) {
  const max = Math.max(1, ...steps.map((s) => s.value));
  return (
    <ol className="m-0 flex list-none flex-col gap-1 p-0" aria-label={ariaLabel}>
      {steps.map((s) => {
        const selected = s.key === selectedKey;
        return (
          <li key={s.key} className="flex flex-col gap-1">
            <button
              type="button"
              onClick={() => onSelect?.(s.key)}
              aria-pressed={onSelect ? selected : undefined}
              disabled={!onSelect}
              data-testid={`funnel-stage-${s.key}`}
              className="grid w-full items-center gap-3 rounded-md border-0 bg-transparent p-1 text-left"
              style={{
                gridTemplateColumns: "minmax(5.5rem, 8rem) 1fr",
                outline: selected ? `2px solid ${tokens.focus}` : "none",
                cursor: onSelect ? "pointer" : "default",
              }}
            >
              <span className="text-sm font-medium">
                {s.label}
                {selected ? <span className="sr-only"> (selected)</span> : null}
              </span>
              <span className="flex min-w-0 items-center gap-2">
                <span
                  aria-hidden="true"
                  className="h-6 rounded-sm"
                  style={{
                    width: `${Math.max(2, (s.value / max) * 100)}%`,
                    background: selected ? tokens.ordinal.strong : tokens.ordinal.mid,
                    minWidth: 4,
                  }}
                />
                <span className="text-sm whitespace-nowrap tabular">
                  {s.count} · {formatValue(s.value)}
                  {s.note ? <span style={{ color: "var(--ink-muted)" }}> · {s.note}</span> : null}
                </span>
              </span>
            </button>
            {s.conversion != null ? (
              <p
                className="m-0 pl-1 text-xs tabular"
                style={{ color: "var(--ink-2)", marginLeft: "8.75rem" }}
              >
                ↓ {formatPct(s.conversion)} convert to next stage
              </p>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
