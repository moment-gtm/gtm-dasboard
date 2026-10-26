/** Left navigation across modules; active module indicated; inaccessible modules disabled (FR-GEN-01). */
import { NavLink } from "react-router-dom";
import { useMe } from "@/hooks/useReference";
import { MODULES } from "./modules";

/** 18px stroke icons, decorative only (the label carries meaning). */
const ICON_PATHS: Record<string, string> = {
  executive: "M3 13h4v8H3zM10 9h4v12h-4zM17 4h4v17h-4z",
  pipeline: "M3 4h18l-7 8v6l-4 2v-8z",
  pursuits: "M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0zM7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3",
  offerings: "M12 2 3 7l9 5 9-5zM3 12l9 5 9-5M3 17l9 5 9-5",
  accounts: "M4 21V7l8-4 8 4v14M9 21v-6h6v6M8 10h.01M12 10h.01M16 10h.01",
  partners:
    "M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM16 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2 20a6 6 0 0 1 12 0M10 20a6 6 0 0 1 12 0",
  solutions_capacity:
    "M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
  market_signals: "M3 12h4l3-8 4 16 3-8h4",
  admin: "M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0M14 4v4M8 10v4M16 16v4",
};

function ModuleIcon({ k }: { k: string }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      <path d={ICON_PATHS[k] ?? "M4 4h16v16H4z"} />
    </svg>
  );
}

export function NavRail() {
  const me = useMe();
  const allowed = new Set(me.data?.modules ?? []);
  return (
    <nav
      aria-label="Dashboard modules"
      data-testid="nav-rail"
      className="relative flex shrink-0 gap-1 overflow-x-auto p-2 md:sticky md:top-0 md:h-screen md:w-60 md:flex-col md:overflow-y-auto md:p-4"
      style={{ background: "var(--nav)", color: "var(--nav-ink)" }}
    >
      <div className="hidden items-center gap-3 px-1 pb-5 md:flex">
        <span
          aria-hidden="true"
          className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-sm font-bold"
          style={{ background: "var(--brand-mark)", color: "var(--spotlight-ink)" }}
        >
          M
        </span>
        <div className="min-w-0">
          <p className="m-0 text-sm font-semibold" style={{ color: "var(--spotlight-ink)" }}>
            Moment GTM
          </p>
          <p className="m-0 text-xs" style={{ color: "var(--nav-muted)" }}>
            Go-to-market dashboard
          </p>
        </div>
      </div>
      <p
        className="m-0 hidden px-2 pb-1 text-[11px] font-semibold tracking-widest uppercase md:block"
        style={{ color: "var(--nav-muted)" }}
      >
        Modules
      </p>
      {MODULES.map((m) => {
        const can = !me.data || allowed.has(m.key);
        if (!can)
          return (
            <span
              key={m.key}
              aria-disabled="true"
              title="Not available for your role"
              data-testid={`nav-${m.key}`}
              className="nav-link"
              style={{ color: "var(--nav-muted)", opacity: 0.7, cursor: "not-allowed" }}
            >
              <ModuleIcon k={m.key} />
              <span style={{ textDecoration: "line-through" }}>{m.label}</span>
              <span className="sr-only"> (not available for your role)</span>
            </span>
          );
        return (
          <NavLink key={m.key} to={m.path} data-testid={`nav-${m.key}`} className="nav-link">
            <ModuleIcon k={m.key} />
            {m.label}
            {!m.built ? (
              <span className="ml-1 text-xs" style={{ color: "var(--nav-muted)" }}>
                ({m.step})
              </span>
            ) : null}
          </NavLink>
        );
      })}
    </nav>
  );
}
