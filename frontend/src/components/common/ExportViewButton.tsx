/** "Export view as PDF" primary action for a module header (FR-GEN-08): logs the export and prints. */
import { logViewExport } from "@/api/executive";

export function ExportViewButton({ module }: { module: string }) {
  const onClick = () => {
    // Fire the audit call without awaiting it: print must run inside the click gesture,
    // and a slow or unreachable API must never block the dialog.
    logViewExport(module, "pdf").catch((err: unknown) => {
      console.warn("Export audit log failed", err);
    });
    window.print();
  };
  return (
    <button
      type="button"
      className="btn btn-primary"
      onClick={onClick}
      data-testid="export-view-pdf"
    >
      Export view as PDF
    </button>
  );
}
