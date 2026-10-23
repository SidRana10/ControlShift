import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { clearCrosswalkCache } from "@/lib/compare/cache";
import { parseCompare, compareHref } from "@/lib/compare/url";
import { clearCatalogCache } from "@/lib/explorer/catalog-cache";
import { currentUrl, go, historyLength, resetNavigation } from "@/test/next-navigation";
import { CROSSWALK_ROWS, installFakeApi, type FakeApi } from "@/test/fake-api";
import { NAV_ITEMS } from "@/lib/navigation";
import { CompareWorkspace } from "./compare-workspace";

let api: FakeApi;
const mount = (url = "/compare") => {
  resetNavigation(url);
  return render(<CompareWorkspace />);
};
const index = () => screen.getByRole("region", { name: "Relationship index" });
const inspector = () => screen.getByRole("region", { name: "Comparison" });
const indexRows = () => within(within(index()).getByRole("list", { name: "Workbook rows" })).getAllByRole("listitem");

beforeEach(() => {
  clearCatalogCache();
  clearCrosswalkCache();
  api = installFakeApi();
});

describe("URL parsing", () => {
  it("accepts valid state and drops invalid values safely", () => {
    const p = (s: string) => parseCompare(new URLSearchParams(s));
    expect(p("focal=gv.sc-03&row=26&q=supply&type=mapped")).toEqual({ focal: "GV.SC-03", row: 26, q: "supply", type: "mapped" });
    expect(p("ref=id.sc-02")).toEqual({ ref: "ID.SC-02" });
    expect(p("focal=GV.SC-03&ref=ID.SC-02")).toEqual({ focal: "GV.SC-03" }); // focal wins; versions never mix
    expect(p("focal=bogus&row=-3&type=other&q=%20")).toEqual({});
    expect(p("row=abc")).toEqual({});
    expect(compareHref({ focal: "GV.SC-03", row: 25, type: "mapped" })).toBe("/compare?focal=GV.SC-03&row=25&type=mapped");
    expect(compareHref({})).toBe("/compare");
  });
});

describe("initial browsing", () => {
  it("lists all workbook rows in workbook order with real counts, and shows the orientation", async () => {
    mount();
    await waitFor(() => expect(indexRows()).toHaveLength(205));
    expect(within(index()).getByRole("status")).toHaveTextContent("205 workbook rows");
    const rows = indexRows();
    expect(rows[0]).toHaveTextContent("ROW 2");
    expect(within(index()).getByRole("button", { name: /^Mapped 185$/ })).toBeInTheDocument();
    expect(within(index()).getByRole("button", { name: /^New in 2\.0 20$/ })).toBeInTheDocument();
    expect(within(index()).queryByRole("button", { name: /unmapped/ })).toBeNull(); // zero in this data
    expect(await screen.findByText(/205 workbook rows from/)).toBeInTheDocument();
    expect(screen.getByText(/A row is not a unique control/)).toBeInTheDocument();
    expect(screen.getByText(/the direction is fixed by the workbook/i)).toBeInTheDocument();
    expect(api.calls.filter((c) => c === "/api/backend/crosswalk")).toHaveLength(1); // shared by index and orientation
  });

  it("shows a no-reference row without inventing a control", async () => {
    mount("/compare?type=new_in_2_0");
    await waitFor(() => expect(indexRows()).toHaveLength(20));
    expect(within(indexRows()[0]).getAllByText("No reference element").length).toBeGreaterThan(0);
  });
});

describe("search and filters", () => {
  it("searches by ID, text, comment and row number, puts exact matches first, and updates the URL without adding history", async () => {
    const user = userEvent.setup();
    mount();
    await waitFor(() => expect(indexRows()).toHaveLength(205));
    const before = historyLength();
    await user.type(within(index()).getByRole("searchbox"), "gv.sc-03");
    await waitFor(() => expect(currentUrl()).toBe("/compare?q=gv.sc-03"));
    await waitFor(() => expect(indexRows().length).toBeLessThan(10));
    expect(historyLength()).toBe(before);
    expect(indexRows()[0]).toHaveTextContent("ROW 25");
    expect(within(indexRows()[0]).getByText("Exact match")).toBeInTheDocument();
    expect(within(index()).getByRole("status")).toHaveTextContent(/rows? match.*gv\.sc-03/);

    await user.clear(within(index()).getByRole("searchbox"));
    await user.type(within(index()).getByRole("searchbox"), "Conceptually new");
    await waitFor(() => expect(indexRows()).toHaveLength(20));
    await user.clear(within(index()).getByRole("searchbox"));
    await user.type(within(index()).getByRole("searchbox"), "26{Enter}");
    await waitFor(() => expect(indexRows()[0]).toHaveTextContent("ROW 26"));
  });

  it("filters by ingest label with counts that ignore the filter, and clears", async () => {
    const user = userEvent.setup();
    mount();
    await waitFor(() => expect(indexRows()).toHaveLength(205));
    await user.click(within(index()).getByRole("button", { name: /^New in 2\.0 20$/ }));
    await waitFor(() => expect(indexRows()).toHaveLength(20));
    expect(currentUrl()).toBe("/compare?type=new_in_2_0");
    expect(within(index()).getByRole("button", { name: /^Mapped 185$/ })).toBeInTheDocument();
    expect(within(index()).getByText("Derived")).toBeInTheDocument();
    await user.click(within(index()).getByRole("button", { name: "Clear" }));
    await waitFor(() => expect(indexRows()).toHaveLength(205));
    expect(currentUrl()).toBe("/compare");
  });

  it("shows an empty state with a way out", async () => {
    const user = userEvent.setup();
    mount("/compare?q=zzzzqqq");
    expect(await within(index()).findByText("No workbook rows match")).toBeInTheDocument();
    await user.click(within(index()).getByRole("button", { name: "Clear filters" }));
    await waitFor(() => expect(indexRows()).toHaveLength(205));
  });
});

describe("selection, history and deep links", () => {
  it("selecting a row pushes a history entry; Back and Forward restore the comparison", async () => {
    const user = userEvent.setup();
    mount();
    await waitFor(() => expect(indexRows()).toHaveLength(205));
    const before = historyLength();
    await user.click(within(index()).getByRole("link", { name: /Row 4:/ }));
    expect(currentUrl()).toBe("/compare?focal=GV.OC-01&row=4");
    expect(historyLength()).toBe(before + 1);
    expect(await within(inspector()).findByRole("heading", { level: 2, name: "GV.OC-01" })).toBeInTheDocument();
    await user.click(within(inspector()).getByRole("link", { name: "Compare workbook row 5" }));
    expect(currentUrl()).toBe("/compare?focal=GV.OC-01&row=5");
    act(() => go(-1));
    await waitFor(() => expect(within(inspector()).getByText(/Selected relationship · workbook row 4/)).toBeInTheDocument());
    act(() => go(1));
    await waitFor(() => expect(within(inspector()).getByText(/Selected relationship · workbook row 5/)).toBeInTheDocument());
  });

  it("a deep link restores selection and filters; a bare row resolves to its element", async () => {
    mount("/compare?focal=ID.IM-03&row=40&q=supply");
    expect(await within(inspector()).findByRole("heading", { level: 2, name: "ID.IM-03" })).toBeInTheDocument();
    expect(within(index()).getByRole("searchbox")).toHaveValue("supply");
  });

  it("resolves ?row=26 to GV.SC-03 and reports an unknown row", async () => {
    const { unmount } = mount("/compare?row=26");
    expect(await within(inspector()).findByRole("heading", { level: 2, name: "GV.SC-03" })).toBeInTheDocument();
    expect(within(inspector()).getByText(/Selected relationship · workbook row 26/)).toBeInTheDocument();
    unmount();
    mount("/compare?row=999");
    expect(await within(inspector()).findByText("Workbook row 999 was not found")).toBeInTheDocument();
  });

  it("an exact CSF 1.1 ID search opens the row from the CSF 1.1 side", async () => {
    const user = userEvent.setup();
    mount("/compare?q=ID.SC-2");
    await waitFor(() => expect(indexRows()[0]).toHaveTextContent("ID.SC-2"));
    await user.click(within(index()).getAllByRole("link")[0]);
    expect(currentUrl()).toMatch(/^\/compare\?ref=ID\.SC-02&row=\d+&q=ID\.SC-2$/);
  });
});

describe("GV.SC-03: rows 25 and 26, side by side", () => {
  it("shows both CSF 2.0 and CSF 1.1 official records for row 25, with provenance and Explorer links", async () => {
    mount("/compare?focal=GV.SC-03&row=25");
    const pair = await within(inspector()).findByRole("article", { name: "CSF 1.1 record ID.SC-2" });
    const left = within(inspector()).getByRole("article", { name: "CSF 2.0 record GV.SC-03" });
    expect(within(left).getByText("CSF 2.0 · focal side")).toBeInTheDocument();
    expect(within(pair).getByText("CSF 1.1 · referenced side")).toBeInTheDocument();
    expect(within(pair).getByText("Normalized as ID.SC-02")).toBeInTheDocument();
    expect(within(left).getByText(/Cybersecurity supply chain risk management is integrated/).className).toMatch(/font-serif/);
    expect(within(pair).getByText(/Suppliers and third party partners/).className).toMatch(/font-serif/);
    expect(within(left).getByText(/p\. 17 \(PDF p\. 22\)/)).toBeInTheDocument();
    expect(left.textContent).toMatch(/Govern \(GV\) › Cybersecurity Supply Chain Risk Management \(GV\.SC\)/);
    expect(within(left).getByRole("link", { name: /Open GV\.SC-03 in Control Explorer/ })).toHaveAttribute("href", "/explorer/2.0/GV.SC-03");
    expect(within(pair).getByRole("link", { name: /Open ID\.SC-2 in Control Explorer/ })).toHaveAttribute("href", "/explorer/1.1/ID.SC-02");
    expect(within(inspector()).getByRole("img", { name: /Workbook row 25: official direction CSF 2.0 to CSF 1.1$/ })).toBeInTheDocument();
  });

  it("keeps both rows visible and independent, with the generated ambiguity notice", async () => {
    mount("/compare?focal=GV.SC-03&row=26");
    const notice = await within(inspector()).findByText("Multiple crosswalk entries require interpretation");
    const box = notice.closest("[role=status]") as HTMLElement;
    expect(within(box).getByText(/contains 2 entries for GV\.SC-03/)).toBeInTheDocument();
    expect(within(box).getByText("Row 25: maps to ID.SC-2.")).toBeInTheDocument();
    expect(within(box).getByText("Row 26: has no reference element; comment “Conceptually new in 2.0”.")).toBeInTheDocument();
    const rows = within(inspector()).getByRole("list", { name: "Workbook rows" });
    const [r25, r26] = within(rows).getAllByRole("listitem");
    expect(r25).toHaveAttribute("data-excel-row", "25");
    expect(r26).toHaveAttribute("data-excel-row", "26");
    expect(r26).toHaveAttribute("aria-current", "true");
    expect(r25).not.toHaveAttribute("aria-current");
    expect(within(r26).getByText("Selected")).toBeInTheDocument();
    expect(within(r25).getByRole("link", { name: "Compare workbook row 25" })).toHaveAttribute("href", "/compare?focal=GV.SC-03&row=25");
  });

  it("row 26 shows an explicit no-reference panel and the workbook comment, not a fake control card", async () => {
    mount("/compare?focal=GV.SC-03&row=26");
    expect(await within(inspector()).findByText("No reference element", { selector: "p" })).toBeInTheDocument();
    expect(within(inspector()).queryByRole("article", { name: /CSF 1\.1 record/ })).toBeNull();
    expect(within(inspector()).getAllByText("“Conceptually new in 2.0”").length).toBeGreaterThan(0);
    expect(within(inspector()).getByText(/does not say the element has no conceptual counterpart/)).toBeInTheDocument();
  });

  it("separates official workbook fields from ControlShift-derived labels", async () => {
    mount("/compare?focal=GV.SC-03&row=26");
    const official = (await within(inspector()).findByText("Official workbook row")).closest("div")!;
    expect(within(official).getByText("NIST")).toBeInTheDocument();
    expect(within(official).getByText("nist_csf_transition.xlsx")).toBeInTheDocument();
    expect(within(official).getByText("Relationships")).toBeInTheDocument();
    expect(within(official).queryByText(/new_in_2_0/)).toBeNull();
    const derived = within(inspector()).getByText("Derived by ControlShift").closest("div")!;
    expect(within(derived).getByText("New in 2.0")).toBeInTheDocument();
    expect(within(derived).getByText("(new_in_2_0)")).toBeInTheDocument(); // exact stored value stays visible
    expect(within(derived).getByRole("button", { name: /Derived classification: mapped and new in 2\.0/ })).toBeInTheDocument();
    expect(within(derived).getByText(/not a measure of how closely/)).toBeInTheDocument();
  });
});

describe("one-to-many and forward / reverse lookups", () => {
  it("ID.IM-03 lists all seven workbook rows, never merged", async () => {
    mount("/compare?focal=ID.IM-03");
    const list = await within(inspector()).findByRole("list", { name: "Workbook rows" });
    const items = within(list).getAllByRole("listitem");
    expect(items).toHaveLength(7);
    expect(items.map((i) => i.getAttribute("data-excel-row"))).toEqual(
      CROSSWALK_ROWS.filter((r) => r.focal_element_id === "ID.IM-03").map((r) => String(r.excel_row)),
    );
    expect(within(inspector()).getByText(/7 workbook rows list this element/)).toBeInTheDocument();
    expect(items[0]).toHaveAttribute("aria-current", "true"); // first row selected by default
    expect(screen.queryByText("Multiple crosswalk entries require interpretation")).toBeNull();
  });

  it("reverse lookup from a CSF 1.1 element shows every row that references it", async () => {
    mount("/compare?ref=ID.SC-02&row=25");
    expect(await within(inspector()).findByText(/5 workbook rows reference this element/)).toBeInTheDocument();
    expect(within(inspector()).getByText(/reverse lookup/)).toBeInTheDocument();
    const items = within(within(inspector()).getByRole("list", { name: "Workbook rows" })).getAllByRole("listitem");
    expect(items.map((i) => i.getAttribute("data-excel-row"))).toEqual(["6", "25", "27", "30", "77"]);
    expect(items[1]).toHaveAttribute("aria-current", "true");
    const focal = await within(inspector()).findByRole("article", { name: "CSF 2.0 record GV.SC-03" });
    expect(focal).toBeInTheDocument();
    expect(within(inspector()).getByRole("link", { name: /Inspect from the CSF 2\.0 side \(GV\.SC-03\)/ })).toHaveAttribute(
      "href",
      "/compare?focal=GV.SC-03&row=25",
    );
  });

  it("forward view offers the CSF 1.1 side without assuming equivalence", async () => {
    mount("/compare?focal=GV.OC-01&row=4");
    const link = await within(inspector()).findByRole("link", { name: /Inspect from the CSF 1\.1 side \(ID\.BE-2\)/ });
    expect(link).toHaveAttribute("href", "/compare?ref=ID.BE-02&row=4");
  });

  it("an unreferenced CSF 1.1 element gets the neutral state and no removal claim", async () => {
    mount("/compare?ref=RC.CO-02");
    expect(await within(inspector()).findByText("No crosswalk reference")).toBeInTheDocument();
    expect(within(inspector()).getByText(/does not state whether the element was retained, merged or dropped/)).toBeInTheDocument();
    expect(within(inspector()).getByRole("article", { name: "CSF 1.1 record RC.CO-2" })).toBeInTheDocument();
    expect(inspector().textContent).not.toMatch(/removed|deprecated|retired/i);
  });

  it("mentions a row that is not part of the inspected element and falls back to its first row", async () => {
    mount("/compare?focal=GV.SC-03&row=99");
    expect(await within(inspector()).findByText("Row 99 is not one of this element's rows")).toBeInTheDocument();
    expect(within(inspector()).getByText(/Showing row 25 instead/)).toBeInTheDocument();
  });
});

describe("errors, retry and stale requests", () => {
  it("reports an unreachable API in the index and recovers on Retry", async () => {
    const user = userEvent.setup();
    api.fail.current = true;
    mount();
    expect(await within(index()).findByRole("alert")).toHaveTextContent("ControlShift API is unreachable");
    api.fail.current = false;
    await user.click(within(index()).getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(indexRows()).toHaveLength(205));
  });

  it("treats a malformed /crosswalk response as an error, not data", async () => {
    api.malformed.push("/crosswalk");
    mount();
    expect(await within(index()).findByRole("alert")).toHaveTextContent("could not be loaded");
    expect(screen.queryByRole("list", { name: "Workbook rows" })).toBeNull();
  });

  it("shows not-found for an unknown control and an error with Retry for a failing record", async () => {
    const user = userEvent.setup();
    mount("/compare?focal=ZZ.ZZ-99");
    expect(await within(inspector()).findByText("ZZ.ZZ-99 was not found in CSF 2.0")).toBeInTheDocument();
    expect(within(inspector()).getByRole("link", { name: /Search the workbook for “ZZ.ZZ-99”/ })).toHaveAttribute("href", "/compare?q=ZZ.ZZ-99");

    api.failDetail.push("/catalog/elements/2.0/GV.SC-03");
    act(() => resetNavigation("/compare?focal=GV.SC-03"));
    expect(await within(inspector()).findByRole("alert")).toHaveTextContent("ControlShift API is unreachable");
    api.failDetail.length = 0;
    await user.click(within(inspector()).getByRole("button", { name: "Retry" }));
    expect(await within(inspector()).findByRole("heading", { level: 2, name: "GV.SC-03" })).toBeInTheDocument();
  });

  it("a slow earlier search cannot overwrite the newer, faster one", async () => {
    const user = userEvent.setup();
    mount();
    await waitFor(() => expect(indexRows()).toHaveLength(205));
    api.delay["q=supply"] = 400;
    const box = within(index()).getByRole("searchbox");
    await user.type(box, "supply{Enter}");
    await waitFor(() => expect(currentUrl()).toBe("/compare?q=supply"));
    await user.click(within(index()).getByRole("button", { name: "Clear search" }));
    await waitFor(() => expect(currentUrl()).toBe("/compare"));
    await act(() => new Promise((r) => setTimeout(r, 600))); // the supply response arrives late
    expect(indexRows()).toHaveLength(205);
    expect(within(index()).getByRole("status")).toHaveTextContent("205 workbook rows");
  });
});

describe("responsive structure and accessibility", () => {
  it("shows the index (not the inspector) on a bare /compare below 900px, and the inspector with a Back link when a row is open", async () => {
    mount();
    expect(index().className).toMatch(/\bflex\b/);
    expect(index().className).not.toMatch(/hidden min-\[900px\]:flex/);
    expect(inspector().className).toMatch(/hidden min-\[900px\]:block/);
  });

  it("hides the index on narrow screens while inspecting, with a 44px Back to results link that keeps filters", async () => {
    mount("/compare?focal=GV.SC-03&row=25&q=supply&type=mapped");
    await within(inspector()).findByRole("heading", { level: 2, name: "GV.SC-03" });
    expect(index().className).toMatch(/hidden min-\[900px\]:flex/);
    expect(inspector().className).toMatch(/\bblock\b/);
    const back = within(inspector()).getByRole("link", { name: "Back to results" });
    expect(back).toHaveAttribute("href", "/compare?q=supply&type=mapped");
    expect(back.className).toMatch(/h-11/);
  });

  it("uses side-by-side only at wide widths and stacks otherwise; controls have 44px targets", async () => {
    mount("/compare?focal=GV.SC-03&row=25");
    await within(inspector()).findByRole("article", { name: "CSF 1.1 record ID.SC-2" });
    const wrap = within(inspector()).getByRole("article", { name: "CSF 2.0 record GV.SC-03" }).parentElement!;
    expect(wrap.className).toMatch(/flex-col/);
    expect(wrap.className).toMatch(/min-\[1480px\]:grid/);
    expect(within(index()).getByRole("button", { name: /^Mapped/ }).className).toMatch(/min-h-11/);
    expect(within(index()).getByRole("searchbox").className).toMatch(/h-11/);
  });

  it("has a logical heading hierarchy for the inspector", async () => {
    mount("/compare?focal=GV.SC-03&row=25");
    await within(inspector()).findByRole("article", { name: "CSF 1.1 record ID.SC-2" });
    const levels = within(inspector()).getAllByRole("heading").map((h) => Number(h.tagName[1]));
    expect(levels[0]).toBe(2);
    for (let i = 1; i < levels.length; i++) expect(levels[i] - levels[i - 1]).toBeLessThanOrEqual(1);
  });
});

describe("index selection", () => {
  it("marks the inspected element's first row in the index for a control-only URL", async () => {
    mount("/compare?focal=GV.SC-03");
    await within(inspector()).findByRole("heading", { level: 2, name: "GV.SC-03" });
    await waitFor(() => {
      const row = within(index()).getByRole("link", { name: /^Row 25:/ });
      expect(row).toHaveAttribute("aria-current", "true");
    });
    expect(within(index()).getByRole("link", { name: /^Row 26:/ })).not.toHaveAttribute("aria-current");
  });
});

describe("navigation", () => {
  it("no longer marks Compare Frameworks as Soon", () => {
    const item = NAV_ITEMS.find((i) => i.href === "/compare")!;
    expect(item.tag).toBeUndefined();
  });
});
