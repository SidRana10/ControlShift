import type { FrameworkVersion, MappingType } from "@/lib/api/types";

/**
 * /compare URL state. One *subject* is inspected at a time: a CSF 2.0 element (`focal`) or a CSF 1.1
 * element (`ref`); `row` picks a workbook row among the subject's rows. `q` and `type` filter the
 * relationship index only. IDs never carry across versions: `focal` and `ref` are separate fields.
 */
export interface CompareState {
  focal?: string;
  ref?: string;
  row?: number;
  q?: string;
  type?: MappingType;
}

export const MAX_Q = 200;
const ID = /^[A-Za-z]{2}(?:\.[A-Za-z]{2}(?:-\d{1,2})?)?$/;
const TYPES: MappingType[] = ["mapped", "new_in_2_0", "unmapped"];

type Params = { get(name: string): string | null };

export const isMappingType = (v: unknown): v is MappingType => TYPES.includes(v as MappingType);

/** Safe parse: anything invalid is dropped, never thrown. `focal` wins over `ref` when both are given. */
export function parseCompare(sp: Params): CompareState {
  const out: CompareState = {};
  const focal = sp.get("focal")?.trim();
  const ref = sp.get("ref")?.trim();
  if (focal && ID.test(focal)) out.focal = focal.toUpperCase();
  else if (ref && ID.test(ref)) out.ref = ref.toUpperCase();
  const row = sp.get("row");
  if (row && /^\d{1,6}$/.test(row) && Number(row) > 0) out.row = Number(row);
  const q = sp.get("q")?.trim().slice(0, MAX_Q);
  if (q) out.q = q;
  const type = sp.get("type");
  if (isMappingType(type)) out.type = type;
  return out;
}

export function compareHref(s: CompareState): string {
  const qs = new URLSearchParams();
  if (s.focal) qs.set("focal", s.focal);
  else if (s.ref) qs.set("ref", s.ref);
  if (s.row) qs.set("row", String(s.row));
  if (s.q) qs.set("q", s.q);
  if (s.type) qs.set("type", s.type);
  return `/compare${qs.size ? `?${qs}` : ""}`;
}

export const hasSubject = (s: CompareState) => Boolean(s.focal || s.ref || s.row);
export const hasFilters = (s: CompareState) => Boolean(s.q || s.type);

/** Reading labels for the ControlShift ingest classification; the exact stored value stays visible alongside. */
export const TYPE_LABEL: Record<MappingType, string> = {
  mapped: "Mapped",
  new_in_2_0: "New in 2.0",
  unmapped: "Unmapped",
};

export const subjectVersion = (s: CompareState): FrameworkVersion | null =>
  s.focal ? "2.0" : s.ref ? "1.1" : null;
