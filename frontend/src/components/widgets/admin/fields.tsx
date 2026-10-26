/** Small shared form pieces for the Administration widgets. */
import type { ReactNode } from "react";
import { useId } from "react";

export const inputStyle = {
  border: "1px solid var(--grid)",
  borderRadius: 6,
  padding: "4px 8px",
  background: "var(--surface)",
  color: "var(--ink)",
  minHeight: 32,
} as const;

export function Field({ label, children }: { label: string; children: (id: string) => ReactNode }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs font-medium" style={{ color: "var(--ink-2)" }}>
        {label}
      </label>
      {children(id)}
    </div>
  );
}

export function FormError({ error }: { error: unknown }) {
  if (!error) return null;
  return (
    <p role="alert" className="m-0 text-sm" style={{ color: "#b3261e" }}>
      {error instanceof Error ? error.message : "Something went wrong."}
    </p>
  );
}

export function Notice({ children }: { children: ReactNode }) {
  return (
    <p
      role="status"
      className="m-0 rounded px-3 py-2 text-sm"
      style={{ background: "var(--accent-wash)", color: "var(--accent-strong)" }}
    >
      {children}
    </p>
  );
}

export const fmtDate = (iso: string) => iso.slice(0, 16).replace("T", " ");
