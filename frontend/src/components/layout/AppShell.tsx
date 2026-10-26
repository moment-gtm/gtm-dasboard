/** App shell: nav rail + header (metric ID toggle, freshness, read-only persona) + global filter bar + routed module. */
import { Outlet, useLocation } from "react-router-dom";
import { DrilldownPanel } from "@/components/common/DrilldownPanel";
import { DataFreshnessIndicator, StalenessBanner } from "./DataFreshnessIndicator";
import { FilterBar } from "./FilterBar";
import { MetricIdsToggle } from "./MetricIdsToggle";
import { NavRail } from "./NavRail";
import { PersonaBadge } from "./PersonaBadge";
import { RoleSwitcher } from "./RoleSwitcher";
import { UserProfile } from "./UserProfile";

/** Demo-only: a user has a single persona per login. Opt in with VITE_ENABLE_PERSONA_SWITCHER=true. */
const PERSONA_SWITCHER_ENABLED = import.meta.env.VITE_ENABLE_PERSONA_SWITCHER === "true";

export function AppShell() {
  const { pathname } = useLocation();
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <a href="#main" className="sr-only focus:not-sr-only">
        Skip to content
      </a>
      <NavRail />
      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className="no-print sticky top-0 z-30 flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-4 py-2 md:px-6"
          style={{
            background: "var(--header-glass)",
            backdropFilter: "saturate(1.4) blur(10px)",
            borderBottom: "1px solid var(--tile-border)",
          }}
        >
          <h1
            className="m-0 text-xl font-bold tracking-tight md:text-2xl"
            style={{ color: "var(--nav)", lineHeight: 1.2 }}
          >
            GTM Performance
          </h1>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <MetricIdsToggle />
            <DataFreshnessIndicator />
            {PERSONA_SWITCHER_ENABLED ? <RoleSwitcher /> : <PersonaBadge />}
            <UserProfile />
          </div>
        </header>
        <StalenessBanner />
        {pathname.startsWith("/admin") ? null : <FilterBar />}
        <main id="main" className="min-w-0 flex-1 px-3 pt-2 pb-8 md:px-6">
          <Outlet />
        </main>
      </div>
      <DrilldownPanel />
    </div>
  );
}
