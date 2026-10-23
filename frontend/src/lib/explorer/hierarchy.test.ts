import { describe, expect, it } from "vitest";
import { ELEMENTS_1_1, ELEMENTS_2_0 } from "@/test/fake-api";
import {
  ancestorsOf,
  buildTree,
  categoriesOf,
  filterElements,
  findElement,
  flattenVisible,
  functionsOf,
  indexById,
  isExactIdMatch,
  orderSearchResults,
  sanitizeContext,
  splitHighlight,
} from "./hierarchy";

const count = (els: { level: string }[], level: string) => els.filter((e) => e.level === level).length;

describe("hierarchy construction (recorded Catalog API data)", () => {
  it("has the expected dataset shape", () => {
    expect([count(ELEMENTS_2_0, "function"), count(ELEMENTS_2_0, "category"), count(ELEMENTS_2_0, "subcategory")]).toEqual([6, 22, 106]);
    expect([count(ELEMENTS_1_1, "function"), count(ELEMENTS_1_1, "category"), count(ELEMENTS_1_1, "subcategory")]).toEqual([5, 23, 108]);
  });

  it("orders functions in official NIST order, not alphabetically", () => {
    expect(buildTree(ELEMENTS_2_0).map((n) => n.element.element_id)).toEqual(["GV", "ID", "PR", "DE", "RS", "RC"]);
    expect(buildTree(ELEMENTS_1_1).map((n) => n.element.element_id)).toEqual(["ID", "PR", "DE", "RS", "RC"]);
  });

  it("nests function > category > subcategory with counts", () => {
    const gv = buildTree(ELEMENTS_2_0)[0];
    expect(gv.subcategoryCount).toBe(31);
    expect(gv.children.map((c) => c.element.element_id)).toEqual(["GV.OC", "GV.OV", "GV.PO", "GV.RM", "GV.RR", "GV.SC"]);
    const sc = gv.children[5];
    expect(sc.children).toHaveLength(10);
    expect(sc.children.map((c) => c.element.element_id)).toEqual([...sc.children.map((c) => c.element.element_id)].sort());
    expect(sc.children[0].children).toEqual([]);
  });

  it("keeps null names and null descriptions as they are", () => {
    expect(ELEMENTS_2_0.filter((e) => e.level === "subcategory").every((e) => e.name === null)).toBe(true);
    const detect11 = ELEMENTS_1_1.find((e) => e.element_id === "DE")!;
    expect(detect11.name).toBe("Detect");
    expect(detect11.description).toBeNull();
  });

  it("keeps original IDs for display and normalized IDs as keys", () => {
    const e = ELEMENTS_1_1.find((x) => x.element_id === "PR.AT-01")!;
    expect(e.original_id).toBe("PR.AT-1");
    expect(findElement(ELEMENTS_1_1, "PR.AT-1")).toBe(e);
    expect(findElement(ELEMENTS_1_1, "pr.at-01")).toBe(e);
    expect(findElement(ELEMENTS_1_1, "PR.AT-99")).toBeUndefined();
  });

  it("flattens only visible rows given the expanded branches", () => {
    const roots = buildTree(ELEMENTS_2_0);
    const rows = flattenVisible(roots, new Set(["GV"]));
    expect(rows).toHaveLength(6 + 6);
    expect(rows[1]).toMatchObject({ depth: 2, parentId: "GV" });
    expect(flattenVisible(roots, new Set(["GV", "GV.SC"])).length).toBe(12 + 10);
    expect(flattenVisible(roots, new Set())).toHaveLength(6);
  });

  it("finds ancestors nearest first", () => {
    const byId = indexById(ELEMENTS_2_0);
    const sc03 = byId.get("GV.SC-03")!;
    expect(ancestorsOf(sc03, byId).map((a) => a.element_id)).toEqual(["GV.SC", "GV"]);
  });
});

describe("filters and search helpers", () => {
  it("filters by level, function and category with exact-match semantics", () => {
    expect(filterElements(ELEMENTS_2_0, { level: "function" })).toHaveLength(6);
    expect(filterElements(ELEMENTS_2_0, { fn: "GV" })).toHaveLength(1 + 6 + 31);
    const sc = filterElements(ELEMENTS_2_0, { cat: "GV.SC" });
    expect(sc).toHaveLength(1 + 10); // the category itself plus its subcategories
    expect(filterElements(ELEMENTS_1_1, { fn: "GV" })).toEqual([]);
  });

  it("builds a valid tree from a filtered subset (orphans become roots)", () => {
    const tree = buildTree(filterElements(ELEMENTS_2_0, { cat: "GV.SC" }));
    expect(tree).toHaveLength(1);
    expect(tree[0].element.element_id).toBe("GV.SC");
    expect(tree[0].children).toHaveLength(10);
  });

  it("drops filters that do not exist in the target version", () => {
    expect(sanitizeContext({ fn: "GV", q: "x", level: "category" }, ELEMENTS_1_1)).toEqual({ q: "x", level: "category" });
    expect(sanitizeContext({ fn: "ID", cat: "ID.AM" }, ELEMENTS_1_1)).toEqual({ fn: "ID", cat: "ID.AM" });
    expect(sanitizeContext({ fn: "PR", cat: "ID.AM" }, ELEMENTS_2_0)).toEqual({ fn: "PR" });
    expect(sanitizeContext({ level: "function", cat: "GV.SC" }, ELEMENTS_2_0)).toEqual({ level: "function" });
    expect(sanitizeContext({ fn: "GV", cat: "GV.SC", q: "a" }, null)).toEqual({ q: "a" });
  });

  it("lists functions and categories for the filter menus", () => {
    expect(functionsOf(ELEMENTS_2_0).map((f) => f.element_id)).toEqual(["GV", "ID", "PR", "DE", "RS", "RC"]);
    expect(categoriesOf(ELEMENTS_2_0, "GV")).toHaveLength(6);
  });

  it("puts an exact ID match first, in either spelling", () => {
    const results = [
      ...filterElements(ELEMENTS_1_1, { cat: "PR.AT" }),
    ];
    const { elements, exactIds } = orderSearchResults(results, "pr.at-1");
    expect(elements[0].element_id).toBe("PR.AT-01");
    expect([...exactIds]).toEqual(["PR.AT-01"]);
    expect(isExactIdMatch(elements[0], "PR.AT-01")).toBe(true);
    expect(isExactIdMatch(elements[1], "pr.at-1")).toBe(false);
  });

  it("splits text for case-insensitive highlighting", () => {
    expect(splitHighlight("Supply chain risk, supply", "SUPPLY")).toEqual([
      { text: "Supply", match: true },
      { text: " chain risk, ", match: false },
      { text: "supply", match: true },
    ]);
    expect(splitHighlight("abc", "")).toEqual([{ text: "abc", match: false }]);
    expect(splitHighlight("abc", "z")).toEqual([{ text: "abc", match: false }]);
  });
});
