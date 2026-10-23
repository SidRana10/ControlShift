import { vi } from "vitest";
import type { CrosswalkList, ElementSummary } from "@/lib/api/types";
import e11 from "./fixtures/elements-1.1.json";
import e20 from "./fixtures/elements-2.0.json";
import versions from "./fixtures/versions.json";
import d11DE from "./fixtures/details/1.1-DE.json";
import d11IDBE02 from "./fixtures/details/1.1-ID.BE-02.json";
import d20GVOC01 from "./fixtures/details/2.0-GV.OC-01.json";
import crosswalkAll from "./fixtures/crosswalk-all.json";
import d11IDSC02 from "./fixtures/details/1.1-ID.SC-02.json";
import d11PRAT01 from "./fixtures/details/1.1-PR.AT-01.json";
import d11RCCO02 from "./fixtures/details/1.1-RC.CO-02.json";
import d20GV from "./fixtures/details/2.0-GV.json";
import d20GVSC from "./fixtures/details/2.0-GV.SC.json";
import d20GVSC03 from "./fixtures/details/2.0-GV.SC-03.json";
import d20IDIM03 from "./fixtures/details/2.0-ID.IM-03.json";

export const ELEMENTS_2_0 = e20 as ElementSummary[];
export const ELEMENTS_1_1 = e11 as ElementSummary[];
export const ALL = [...ELEMENTS_1_1, ...ELEMENTS_2_0];

/** Real responses recorded from GET /catalog/elements/{version}/{id} (see fixtures/details). */
export const DETAILS: Record<string, unknown> = {
  "1.1/DE": d11DE,
  "1.1/ID.SC-02": d11IDSC02,
  "1.1/ID.BE-02": d11IDBE02,
  "2.0/GV.OC-01": d20GVOC01,
  "1.1/PR.AT-01": d11PRAT01,
  "1.1/RC.CO-02": d11RCCO02,
  "2.0/GV": d20GV,
  "2.0/GV.SC": d20GVSC,
  "2.0/GV.SC-03": d20GVSC03,
  "2.0/ID.IM-03": d20IDIM03,
};

/** Recorded GET /crosswalk (all 205 rows); filters below mirror KnowledgeStore.list_crosswalk. */
export const CROSSWALK_ROWS = (crosswalkAll as unknown as CrosswalkList).entries;

export function queryCrosswalk(p: URLSearchParams): CrosswalkList {
  const norm = (x: string) => x.toUpperCase().replace(/-(\d)$/, "-0$1");
  const q = p.get("q")?.toLowerCase();
  const base = CROSSWALK_ROWS.filter(
    (r) =>
      (!p.get("focal") || r.focal_element_id === norm(p.get("focal")!)) &&
      (!p.get("reference") || r.reference_element_id === norm(p.get("reference")!)) &&
      (!q ||
        [r.focal_element_id, r.focal_original_id, r.reference_element_id, r.reference_original_id, r.focal_description, r.reference_description, r.comments].some((f) => f?.toLowerCase().includes(q)) ||
        String(r.excel_row) === q),
  );
  const counts = { mapped: 0, new_in_2_0: 0, unmapped: 0 };
  for (const r of base) counts[r.mapping_type]++;
  const rows = base.filter((r) => !p.get("type") || r.mapping_type === p.get("type"));
  return { direction: "CSF 2.0 (focal) -> CSF 1.1 (reference)", total: rows.length, count: rows.length, limit: 250, offset: 0, type_counts: counts, entries: rows };
}

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
const notFound = (msg: string) =>
  json(404, { error: { code: "not_found", message: msg, details: null } });

/** Mirrors GET /catalog/elements: exact level/function/category, substring q over four fields. */
export function queryElements(p: URLSearchParams): ElementSummary[] {
  const q = p.get("q")?.toLowerCase();
  return ALL.filter(
    (e) =>
      (!p.get("version") || e.version === p.get("version")) &&
      (!p.get("level") || e.level === p.get("level")) &&
      (!p.get("function") || e.function_id === p.get("function")) &&
      (!p.get("category") || e.category_id === p.get("category")) &&
      (!q ||
        [e.element_id, e.original_id, e.name, e.description].some((f) => f?.toLowerCase().includes(q))),
  ).sort((a, b) => a.version.localeCompare(b.version) || a.element_id.localeCompare(b.element_id));
}

export interface FakeApi {
  calls: string[];
  /** Delay (ms) applied to requests whose URL contains the given text. */
  delay: Record<string, number>;
  fail: { current: boolean };
  /** URL fragments that answer 500 (proxy-style failure) or 200 with an unexpected body. */
  failDetail: string[];
  malformed: string[];
}

export function installFakeApi(): FakeApi {
  const api: FakeApi = { calls: [], delay: {}, fail: { current: false }, failDetail: [], malformed: [] };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), "http://test");
      api.calls.push(url.pathname + url.search);
      const wait = Object.entries(api.delay).find(([k]) => url.href.includes(k))?.[1];
      if (wait) await new Promise((r) => setTimeout(r, wait));
      if (api.fail.current) throw new TypeError("network down");
      const path = url.pathname.replace("/api/backend", "");
      if (path === "/crosswalk") {
        if (api.failDetail.some((f) => url.href.includes(f))) return new Response("Internal Server Error", { status: 500 });
        if (api.malformed.some((f) => url.href.includes(f))) return json(200, { foo: "bar" });
        return json(200, queryCrosswalk(url.searchParams));
      }
      if (path === "/catalog/versions") return json(200, versions);
      if (path === "/catalog/elements") {
        const els = queryElements(url.searchParams);
        return json(200, { count: els.length, elements: els });
      }
      const m = /^\/catalog\/elements\/([^/]+)\/([^/]+)$/.exec(path);
      if (m) {
        if (api.failDetail.some((f) => url.href.includes(f))) {
          return new Response("Internal Server Error", { status: 500 });
        }
        if (api.malformed.some((f) => url.href.includes(f))) return json(200, { foo: "bar" });
        const id = decodeURIComponent(m[2]).toUpperCase();
        const el = ALL.find(
          (e) => e.version === m[1] && (e.element_id === id || e.original_id.toUpperCase() === id),
        );
        if (!el) return notFound(`${m[2]} not found in CSF ${m[1]}`);
        const recorded = DETAILS[`${el.version}/${el.element_id}`];
        if (recorded) return json(200, recorded);
        return json(200, {
          ...el,
          parent: ALL.find((e) => e.version === el.version && e.element_id === el.parent_id) ?? null,
          children: [],
          informative_references: [],
          provenance: {
            source_document: { source_file: "nist.pdf", kind: "pdf", sha256: "0".repeat(64), bytes: 1, pages: 9 },
            chunk: { chunk_id: `csf${el.version}:${el.element_id}`, page: 22, printed_page: "17", section: "Core" },
          },
          crosswalk: {
            direction: "CSF 2.0 (focal) -> CSF 1.1 (reference)",
            queried_role: "focal",
            lookup: "forward",
            entries: [],
            summary: { derived: true, status: "no_crosswalk_reference", mapped_row_count: 0, new_in_2_0_row_count: 0, excel_rows: [], note: "" },
          },
        });
      }
      return json(404, { error: { code: "not_found", message: "nope", details: null } });
    }),
  );
  return api;
}
