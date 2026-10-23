import { describe, expect, it } from "vitest";
import { listHref, parseContext, parseLocation, recordHref } from "./url";

const sp = (s: string) => new URLSearchParams(s);

describe("explorer URL state", () => {
  it("parses and normalises browsing context, dropping invalid values", () => {
    expect(parseContext(sp("level=subcategory&fn=gv&cat=gv.sc&q=%20supply%20"))).toEqual({
      level: "subcategory",
      fn: "GV",
      cat: "GV.SC",
      q: "supply",
    });
    expect(parseContext(sp("level=section&fn=GOV&cat=GV&q=%20"))).toEqual({});
    expect(parseContext(sp(`q=${"x".repeat(300)}`)).q).toHaveLength(200);
  });

  it("defaults the list view to CSF 2.0 and falls back from an invalid v", () => {
    expect(parseLocation("/explorer", sp(""))).toMatchObject({ kind: "list", version: "2.0" });
    expect(parseLocation("/explorer", sp("v=1.1"))).toMatchObject({ version: "1.1" });
    expect(parseLocation("/explorer", sp("v=3.0"))).toMatchObject({ version: "2.0" });
  });

  it("parses record URLs with version, id and context", () => {
    expect(parseLocation("/explorer/1.1/PR.AT-01", sp("q=awareness"))).toEqual({
      kind: "record",
      version: "1.1",
      versionParam: "1.1",
      recordId: "PR.AT-01",
      ctx: { q: "awareness" },
    });
    expect(parseLocation("/explorer/3.0/GV", sp(""))).toMatchObject({ kind: "record", version: null });
  });

  it("builds canonical hrefs that round-trip", () => {
    const ctx = { level: "subcategory", fn: "GV", q: "supply chain" } as const;
    expect(listHref("2.0", ctx)).toBe("/explorer?v=2.0&level=subcategory&fn=GV&q=supply+chain");
    expect(recordHref("2.0", "GV.SC-03", ctx)).toBe(
      "/explorer/2.0/GV.SC-03?level=subcategory&fn=GV&q=supply+chain",
    );
    const [path, query] = recordHref("1.1", "PR.AT-01", ctx).split("?");
    const loc = parseLocation(path, sp(query));
    expect(loc).toMatchObject({ kind: "record", version: "1.1", recordId: "PR.AT-01", ctx });
  });
});
