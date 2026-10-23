import type { FrameworkVersion } from "@/lib/api/types";
import { isVersion } from "@/lib/explorer/url";
import type { Evidence, EvidenceItem } from "./types";

/** DOM id for an evidence entry; derived from the backend citation id (e.g. "xwalk:row25"). */
export const evidenceDomId = (citationId: string) =>
  `evidence-${citationId.replace(/[^A-Za-z0-9]+/g, "-")}`;

export const asVersion = (v: string | null | undefined): FrameworkVersion | null =>
  v && isVersion(v) ? v : null;

/** Every evidence entry the response returned, keyed by its citation id. */
export function indexEvidence(evidence: Evidence | null): Map<string, EvidenceItem> {
  const map = new Map<string, EvidenceItem>();
  if (!evidence) return map;
  for (const item of [...evidence.controls, ...evidence.crosswalk, ...evidence.passages]) {
    if (!map.has(item.citation_id)) map.set(item.citation_id, item);
  }
  return map;
}

/** Every citation id the answer cites anywhere (top level, key points, mappings), in first-seen order. */
export function allAnswerCitations(answer: {
  citations: string[];
  key_changes: { citations: string[] }[];
  mappings: { citations: string[] }[];
}): string[] {
  const seen = new Set<string>();
  for (const id of [
    ...answer.citations,
    ...answer.key_changes.flatMap((k) => k.citations),
    ...answer.mappings.flatMap((m) => m.citations),
  ]) {
    seen.add(id);
  }
  return [...seen];
}

/** "p. 17 (PDF p. 22)", or "PDF p. 22" when the printed page is unknown, or null. */
export function pageLabel(printed: string | null, page: number | null): string | null {
  if (printed && page !== null) return `p. ${printed} (PDF p. ${page})`;
  if (page !== null) return `PDF p. ${page}`;
  return printed ? `p. ${printed}` : null;
}

/** Short chip text for an evidence item: the control id, the workbook row, or the page of a text passage. */
export function itemLabel(item: EvidenceItem): string {
  if (item.kind === "control") return item.control_id;
  if (item.kind === "crosswalk") return `Row ${item.excel_row}`;
  if (item.control_id) return item.control_id;
  return pageLabel(item.printed_page, item.page) ?? "Text passage";
}

/** The version a chip should show; workbook rows span two versions, so they carry none. */
export function itemVersion(item: EvidenceItem): FrameworkVersion | null {
  return item.kind === "crosswalk" ? null : asVersion(item.version);
}

export const sourceKindLabel = (item: EvidenceItem) =>
  item.kind === "crosswalk" ? "Transition workbook" : `CSF ${item.version}`;
