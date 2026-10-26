/** Read-only persona + RLS scope of the signed-in user (a user holds exactly one persona per login). */
import { useMe } from "@/hooks/useReference";
import { useAuthStore } from "@/state/auth";

export function PersonaBadge() {
  const user = useAuthStore((s) => s.user);
  const me = useMe();
  const label = me.data?.label ?? user?.role_label;

  if (!label) return null;

  return (
    <div className="flex w-64 min-w-0 shrink-0 flex-col gap-0.5" data-testid="persona-badge">
      <span className="truncate text-sm" title={label}>
        <span style={{ color: "var(--ink-2)" }}>Persona </span>
        <strong>{label}</strong>
      </span>
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
