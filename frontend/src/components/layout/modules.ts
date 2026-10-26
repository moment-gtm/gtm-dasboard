/** Module registry for the nav rail (FR-GEN-01). `step` = roadmap step that builds it. */
export interface ModuleDef {
  key: string;
  label: string;
  path: string;
  step: string;
  built: boolean;
}

export const MODULES: ModuleDef[] = [
  { key: "executive", label: "Executive summary", path: "/executive", step: "Step 1", built: true },
  { key: "pipeline", label: "Pipeline", path: "/pipeline", step: "Step 2", built: true },
  { key: "pursuits", label: "Pursuits & wins", path: "/pursuits", step: "Step 3", built: true },
  { key: "offerings", label: "Offerings", path: "/offerings", step: "Step 5", built: true },
  { key: "accounts", label: "Accounts", path: "/accounts", step: "Step 5", built: true },
  { key: "partners", label: "Partners", path: "/partners", step: "Step 5", built: true },
  {
    key: "solutions_capacity",
    label: "Solutions capacity",
    path: "/solutions-capacity",
    step: "Step 6",
    built: true,
  },
  {
    key: "market_signals",
    label: "Market signals",
    path: "/market-signals",
    step: "Step 7",
    built: true,
  },
  { key: "admin", label: "Administration", path: "/admin", step: "Step 4", built: true },
];
