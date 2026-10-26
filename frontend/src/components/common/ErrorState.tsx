/** Error state with a retry (FR-GEN-13). */
import { ApiError } from "@/api/client";
import { tokens } from "@/theme/tokens";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const status = error instanceof ApiError ? error.status : undefined;
  const message =
    error instanceof Error ? error.message : "Something went wrong while loading this widget.";
  const hint =
    status === 0
      ? "Start the backend (uvicorn on port 8000) and retry."
      : status && status >= 500
        ? "A source may have failed to load — check the data freshness indicator, then retry."
        : "Retry, or adjust the filters.";
  return (
    <div
      role="alert"
      data-testid="error-state"
      className="flex flex-col items-start gap-2 rounded-lg p-4"
      style={{ background: tokens.status.off_track.bg, color: tokens.status.off_track.text }}
    >
      <p className="m-0 text-sm font-semibold">Couldn’t load this data</p>
      <p className="m-0 text-sm">{message}</p>
      <p className="m-0 text-sm">{hint}</p>
      {onRetry ? (
        <button type="button" className="btn" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
