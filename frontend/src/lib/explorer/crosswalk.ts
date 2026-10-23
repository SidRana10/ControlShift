import type { CrosswalkEntry, CrosswalkStatus, CrosswalkSummary } from "@/lib/api/types";

/** Labels for crosswalk.summary.status (ControlShift-derived, never NIST workbook fields). */
export const STATUS_LABEL: Record<CrosswalkStatus, string> = {
  mapped_only: "mapped only",
  new_in_2_0_only: "new in 2.0 only",
  mapped_and_new_in_2_0: "mapped and new in 2.0",
  no_crosswalk_reference: "no crosswalk reference",
  unclassified: "unclassified",
};

export const statusLabel = (s: CrosswalkSummary["status"]): string =>
  STATUS_LABEL[s] ?? String(s).replace(/_/g, " ");

/** One factual clause per workbook row, built only from the returned fields. */
export function describeEntry(e: CrosswalkEntry): string {
  const parts: string[] = [];
  if (e.reference_element_id) {
    parts.push(`maps to ${e.reference_original_id ?? e.reference_element_id}`);
  } else {
    parts.push("has no reference element");
  }
  if (e.comments) parts.push(`comment “${e.comments}”`);
  return `Row ${e.excel_row}: ${parts.join("; ")}.`;
}

/** Descriptions longer than this get a "Show full text" control (2-line clamp otherwise). */
export const LONG_TEXT_CHARS = 150;
export const isLongText = (t: string | null | undefined) => (t?.length ?? 0) > LONG_TEXT_CHARS;

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
