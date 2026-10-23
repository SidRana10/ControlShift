import { vi } from "vitest";
import type { ElementSummary } from "@/lib/api/types";
import e11 from "./fixtures/elements-1.1.json";
import e20 from "./fixtures/elements-2.0.json";
import versions from "./fixtures/versions.json";

export const ELEMENTS_2_0 = e20 as ElementSummary[];
export const ELEMENTS_1_1 = e11 as ElementSummary[];
export const ALL = [...ELEMENTS_1_1, ...ELEMENTS_2_0];

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
}

export function installFakeApi(): FakeApi {
  const api: FakeApi = { calls: [], delay: {}, fail: { current: false } };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), "http://test");
      api.calls.push(url.pathname + url.search);
      const wait = Object.entries(api.delay).find(([k]) => url.href.includes(k))?.[1];
      if (wait) await new Promise((r) => setTimeout(r, wait));
      if (api.fail.current) throw new TypeError("network down");
      const path = url.pathname.replace("/api/backend", "");
      if (path === "/catalog/versions") return json(200, versions);
      if (path === "/catalog/elements") {
        const els = queryElements(url.searchParams);
        return json(200, { count: els.length, elements: els });
      }
      const m = /^\/catalog\/elements\/([^/]+)\/([^/]+)$/.exec(path);
      if (m) {
        const id = decodeURIComponent(m[2]).toUpperCase();
        const el = ALL.find(
          (e) => e.version === m[1] && (e.element_id === id || e.original_id.toUpperCase() === id),
        );
        if (!el) return notFound(`${m[2]} not found in CSF ${m[1]}`);
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
