/**
 * Spotlight tile — the dark, high-emphasis bento tile for the one thing leadership should act on
 * (risk, gap, exception). Text, StatusBadges and actions only: never put chart marks on it (the
 * chart palette is validated for the light surface). Owns loading / error states like WidgetCard.
 */
import type { ReactNode } from "react";
import { tokens } from "@/theme/tokens";
import { ErrorState } from "./ErrorState";

export interface SpotlightStat {
  label: string;
  value: ReactNode;
}

export function SpotlightCard({
  eyebrow,
  tone = "alert",
  title,
  stats,
  children,
  actions,
  isLoading,
  error,
  onRetry,
  testId,
}: {
  eyebrow: string;
  /** "alert" = something needs attention (warning icon); "ok" = all clear (check icon). */
  tone?: "alert" | "ok";
  title: ReactNode;
  stats?: SpotlightStat[];
  children?: ReactNode;
  actions?: ReactNode;
  isLoading?: boolean;
  error?: unknown;
  onRetry?: () => void;
  testId?: string;
}) {
  if (isLoading)
    return <div className="skeleton" style={{ minHeight: 220 }} aria-label="Loading" />;
  if (error)
    return (
      <div className="card p-5">
        <ErrorState error={error} onRetry={onRetry} />
      </div>
    );
  const headingId = `${testId ?? "spotlight"}-title`;
  return (
    <section
      aria-labelledby={headingId}
      className="card tile-spotlight flex min-w-0 flex-col gap-4 p-5"
      data-testid={testId}
    >
      <div>
        <p className="eyebrow m-0 mb-1 flex items-center gap-1.5">
          {tone === "alert" ? (
            <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M8 1.5l7 12.5H1z" fill={tokens.status.watch.fill} />
            </svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true">
              <circle cx="8" cy="8" r="7" fill={tokens.status.on_track.fill} />
              <path
                d="M4.5 8.2l2.3 2.3 4.7-4.8"
                stroke="#fff"
                strokeWidth="1.8"
                fill="none"
                strokeLinecap="round"
              />
            </svg>
          )}
          {eyebrow}
        </p>
        <h2 id={headingId} className="m-0 text-lg leading-snug font-semibold">
          {title}
        </h2>
      </div>
      {stats?.length ? (
        <dl className="m-0 grid grid-cols-2 gap-3">
          {stats.map((s) => (
            <div
              key={s.label}
              className="rounded-[14px] p-3"
              style={{ background: "var(--spotlight-stat)" }}
            >
              <dt className="text-xs" style={{ color: "var(--spotlight-muted)" }}>
                {s.label}
              </dt>
              <dd className="hero-number m-0 mt-1" style={{ fontSize: "1.75rem" }}>
                {s.value}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
      {children}
      {actions ? <div className="no-print mt-auto flex flex-wrap gap-2">{actions}</div> : null}
    </section>
  );
}
