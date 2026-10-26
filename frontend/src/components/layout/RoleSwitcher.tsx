/** Mock Entra persona switcher → RLS scope + module visibility (RSD 9, NFR-04/05).
 *  DEMO ONLY: rendered by AppShell solely when VITE_ENABLE_PERSONA_SWITCHER=true (and the backend
 *  runs with GTM_ENABLE_PERSONA_SWITCHER=1 and GTM_ALLOW_PASSWORDLESS_LOGIN=1). */
import { useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/api/auth";
import { useMe, useRoles } from "@/hooks/useReference";
import { useAuthStore } from "@/state/auth";
import { useRoleStore } from "@/state/role";

export function RoleSwitcher() {
  const roles = useRoles();
  const me = useMe();
  const role = useRoleStore((s) => s.role);
  const setRole = useRoleStore((s) => s.setRole);
  const setAuth = useAuthStore((s) => s.setAuth);
  const qc = useQueryClient();

  const handleRoleChange = async (newRole: string) => {
    setRole(newRole);
    const targetPersona = roles.data?.find((p) => p.role === newRole);
    if (targetPersona?.upn) {
      try {
        const res = await authApi.loginWithEntra(targetPersona.upn);
        setAuth(res.access_token, res.user);
      } catch {
        // Fall back gracefully in mock/offline testing
      }
    }
    void qc.invalidateQueries();
  };

  return (
    // Fixed width: the scope line is persona-dependent text and must truncate inside the column
    // instead of widening it, otherwise the header controls wrap onto extra rows per persona.
    <div className="flex w-64 min-w-0 shrink-0 flex-col gap-0.5">
      <label className="flex min-w-0 items-center gap-1 text-sm">
        <span style={{ color: "var(--ink-2)" }}>Persona</span>
        <select
          className="btn min-w-0 flex-1"
          data-testid="role-switcher"
          value={role}
          onChange={(e) => void handleRoleChange(e.target.value)}
        >
          {(roles.data ?? [{ role, label: role, name: "" }]).map((p) => (
            <option key={p.role} value={p.role}>
              {p.label}
              {p.name ? ` — ${p.name}` : ""}
            </option>
          ))}
        </select>
      </label>
      {me.data ? (
        <span
          className="truncate text-xs"
          title={me.data.scope_detail}
          data-testid="role-scope"
          style={{ color: "var(--ink-muted)" }}
        >
          Scope: {me.data.scope_detail}
        </span>
      ) : null}
    </div>
  );
}
