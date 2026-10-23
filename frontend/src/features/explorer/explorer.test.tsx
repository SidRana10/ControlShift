import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { clearCatalogCache } from "@/lib/explorer/catalog-cache";
import { resetExpansion } from "@/lib/explorer/expansion-store";
import { currentUrl, go, historyLength, resetNavigation } from "@/test/next-navigation";
import { installFakeApi, type FakeApi } from "@/test/fake-api";
import { HEADER_ACTIONS_ID } from "@/components/layout/header-actions";
import { ExplorerWorkspace } from "./explorer-workspace";

let api: FakeApi;

function mount(url: string) {
  resetNavigation(url);
  return render(
    <>
      <div id={HEADER_ACTIONS_ID} />
      <ExplorerWorkspace />
    </>,
  );
}

const navigator = () => screen.getByRole("region", { name: "Navigator" });
const searchbox = () => screen.getByRole("searchbox", { name: /search/i });
const treeItem = (name: RegExp | string) => within(navigator()).getByRole("treeitem", { name });
const row = (id: string) => navigator().querySelector<HTMLElement>(`[data-node-id="${id}"]`)!;
const status = () => within(navigator()).getByRole("status");
const user = () => userEvent.setup();
const topLevelIds = () =>
  within(navigator())
    .getAllByRole("treeitem")
    .filter((e) => e.getAttribute("aria-level") === "1")
    .map((e) => e.getAttribute("data-node-id"));

beforeEach(() => {
  clearCatalogCache();
  resetExpansion();
  api = installFakeApi();
});

describe("browsing", () => {
  it("opens on CSF 2.0 with Govern expanded, no record selected, and real framework facts", async () => {
    mount("/explorer");
    expect(await within(navigator()).findByRole("tree", { name: /CSF 2\.0/ })).toBeInTheDocument();
    expect(treeItem(/^GV Govern/)).toHaveAttribute("aria-expanded", "true");
    expect(treeItem(/^ID Identify/)).toHaveAttribute("aria-expanded", "false");
    expect(within(navigator()).queryByRole("treeitem", { selected: true })).toBeNull();
    // function rows in NIST order
    expect(topLevelIds()).toEqual(["GV", "ID", "PR", "DE", "RS", "RC"]);
    expect(await screen.findByText(/6 functions · 22 categories · 106 subcategories/)).toBeInTheDocument();
    expect(status()).toHaveTextContent("134 elements · CSF 2.0");
    expect(screen.getByRole("radio", { name: "CSF 2.0" })).toBeChecked();
  });

  it("chevron click only expands; row click opens the record and pushes history", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    const oc = treeItem(/^GV\.OC/);
    await u.click(oc.querySelector("span[aria-hidden]")!);
    expect(oc).toHaveAttribute("aria-expanded", "true");
    expect(currentUrl()).toBe("/explorer");
    expect(historyLength()).toBe(1);
    await u.click(treeItem(/^GV\.OC-01/));
    expect(currentUrl()).toBe("/explorer/2.0/GV.OC-01");
    expect(historyLength()).toBe(2);
    expect(await screen.findByRole("heading", { name: "GV.OC-01" })).toBeInTheDocument();
    expect(treeItem(/^GV\.OC-01/)).toHaveAttribute("aria-selected", "true");
  });

  it("keeps expansion state when a record opens, and Back restores the browse view", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    await u.click(treeItem(/^ID Identify/).querySelector("span[aria-hidden]")!);
    await u.click(treeItem(/^GV\.OV$|^GV\.OV /));
    expect(treeItem(/^ID Identify/)).toHaveAttribute("aria-expanded", "true");
    act(() => go(-1));
    expect(currentUrl()).toBe("/explorer");
    expect(await screen.findByText(/Records worth a look/)).toBeInTheDocument();
    expect(treeItem(/^ID Identify/)).toHaveAttribute("aria-expanded", "true");
  });

  it("shows a deep-linked record, selects it and expands its ancestors", async () => {
    mount("/explorer/2.0/GV.SC-03");
    expect(await screen.findByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
    expect(await screen.findByText(/p\. 17 \(PDF p\. 22\)/)).toBeInTheDocument();
    await waitFor(() => expect(treeItem(/^GV\.SC-03/)).toHaveAttribute("aria-selected", "true"));
    expect(treeItem(/^GV\.SC /)).toHaveAttribute("aria-expanded", "true");
  });
});

describe("tree keyboard", () => {
  it("implements the tree key bindings", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    row("GV").focus();
    await u.keyboard("{ArrowDown}");
    expect(row("GV.OC")).toHaveFocus();
    await u.keyboard("{ArrowRight}");
    expect(row("GV.OC")).toHaveAttribute("aria-expanded", "true");
    await u.keyboard("{ArrowRight}");
    expect(row("GV.OC-01")).toHaveFocus();
    await u.keyboard("{ArrowLeft}");
    expect(row("GV.OC")).toHaveFocus();
    await u.keyboard("{ArrowLeft}");
    expect(row("GV.OC")).toHaveAttribute("aria-expanded", "false");
    await u.keyboard("{ArrowLeft}");
    expect(row("GV")).toHaveFocus();
    await u.keyboard("{End}");
    expect(row("RC")).toHaveFocus();
    await u.keyboard("{Home}");
    expect(row("GV")).toHaveFocus();
    // roving tabindex: exactly one tabbable row
    expect(within(navigator()).getAllByRole("treeitem").filter((e) => e.tabIndex === 0)).toHaveLength(1);
  });

  it("Enter opens the focused record and moves focus to its heading", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    treeItem(/^GV\.OC/).focus();
    await u.keyboard("{Enter}");
    expect(currentUrl()).toBe("/explorer/2.0/GV.OC");
    const heading = await screen.findByRole("heading", { name: "GV.OC" });
    await waitFor(() => expect(heading).toHaveFocus());
  });

  it("'/' focuses the search field and Down moves into the tree", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    await u.keyboard("/");
    expect(searchbox()).toHaveFocus();
    await u.keyboard("{ArrowDown}");
    expect(treeItem(/^GV Govern/)).toHaveFocus();
  });
});

describe("search", () => {
  it("debounces into the URL, shows a flat highlighted list, exact ID first, and restores the tree on clear", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    await u.click(treeItem(/^ID Identify/).querySelector("span[aria-hidden]")!);
    await u.type(searchbox(), "supply");
    await waitFor(() => expect(currentUrl()).toBe("/explorer?v=2.0&q=supply"));
    expect(historyLength()).toBe(1); // search edits replace, never push
    const list = await within(navigator()).findByRole("list", { name: /Search results/ });
    expect(within(navigator()).queryByRole("tree")).toBeNull();
    expect(list.querySelectorAll("mark").length).toBeGreaterThan(0);
    expect(status()).toHaveTextContent(/matches for “supply” in CSF 2\.0/);
    // only one request per settled query (typing is debounced)
    expect(api.calls.filter((c) => c.includes("q=supply"))).toHaveLength(1);
    // exact ID
    await u.clear(searchbox());
    await u.type(searchbox(), "gv.sc-03");
    await waitFor(() => expect(status()).toHaveTextContent(/1 match for “gv\.sc-03”/));
    const first = within(navigator()).getAllByRole("link")[0];
    expect(first).toHaveTextContent("GV.SC-03");
    expect(first).toHaveTextContent("Exact ID");
    // clear restores the tree with its expansion
    await u.click(screen.getByRole("button", { name: "Clear search" }));
    expect(await within(navigator()).findByRole("tree")).toBeInTheDocument();
    expect(treeItem(/^ID Identify/)).toHaveAttribute("aria-expanded", "true");
    expect(currentUrl()).toBe("/explorer?v=2.0");
  });

  it("matches printed 1.1 IDs and shows an empty state with real actions", async () => {
    const u = user();
    mount("/explorer?v=1.1");
    await within(navigator()).findByRole("tree");
    await u.type(searchbox(), "PR.AT-1");
    await waitFor(() => expect(status()).toHaveTextContent(/match(es)? for “PR\.AT-1”/));
    const first = within(navigator()).getAllByRole("link")[0];
    expect(first).toHaveTextContent("PR.AT-1");
    expect(first).toHaveTextContent("Exact ID");
    await u.clear(searchbox());
    await u.type(searchbox(), "zzzqqq");
    expect(await within(navigator()).findByText(/No elements match “zzzqqq” in CSF 1\.1/)).toBeInTheDocument();
    await u.click(within(navigator()).getByRole("button", { name: /Search CSF 2\.0 instead/ }));
    expect(currentUrl()).toBe("/explorer?v=2.0&q=zzzqqq");
  });

  it("Escape clears the query first, then leaves the field", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    await u.type(searchbox(), "oversight");
    await waitFor(() => expect(currentUrl()).toContain("q=oversight"));
    await u.keyboard("{Escape}");
    expect(searchbox()).toHaveValue("");
    expect(searchbox()).toHaveFocus();
    await waitFor(() => expect(currentUrl()).toBe("/explorer?v=2.0"));
    await u.keyboard("{Escape}");
    expect(searchbox()).not.toHaveFocus();
  });

  it("never lets a slow earlier response overwrite a newer search", async () => {
    const u = user();
    api.delay["q=supply"] = 400;
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    await u.type(searchbox(), "supply");
    await new Promise((r) => setTimeout(r, 250)); // first request is in flight
    await u.clear(searchbox());
    await u.type(searchbox(), "oversight");
    expect(await within(navigator()).findByText(/1 match for “oversight”/)).toBeInTheDocument();
    await new Promise((r) => setTimeout(r, 500)); // let the slow response arrive
    expect(status()).toHaveTextContent(/1 match for “oversight”/);
    expect(within(navigator()).queryByText("GV.SC-03")).toBeNull();
  });

  it("reports an unreachable API with a working Retry", async () => {
    const u = user();
    api.fail.current = true;
    mount("/explorer");
    expect(await within(navigator()).findByText("ControlShift API is unreachable")).toBeInTheDocument();
    api.fail.current = false;
    await u.click(within(navigator()).getByRole("button", { name: "Retry" }));
    expect(await within(navigator()).findByRole("tree")).toBeInTheDocument();
  });
});

describe("filters", () => {
  it("level filter gives a flat list; function and category narrow it; chips remove them", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    await u.selectOptions(screen.getByRole("combobox", { name: "Level" }), "subcategory");
    expect(await within(navigator()).findByRole("list", { name: /Filtered elements/ })).toBeInTheDocument();
    expect(status()).toHaveTextContent("106 results · CSF 2.0");
    await u.selectOptions(screen.getByRole("combobox", { name: "Function" }), "GV");
    expect(status()).toHaveTextContent("31 results · CSF 2.0");
    await u.selectOptions(screen.getByRole("combobox", { name: "Category" }), "GV.SC");
    expect(status()).toHaveTextContent("10 results · CSF 2.0");
    expect(currentUrl()).toBe("/explorer?v=2.0&level=subcategory&fn=GV&cat=GV.SC");
    await u.click(screen.getByRole("button", { name: /Remove filter: Level/ }));
    // without a level filter, function + category browse as a tree again (category subtree)
    expect(await within(navigator()).findByRole("tree")).toBeInTheDocument();
    expect(topLevelIds()).toEqual(["GV.SC"]);
    await u.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(currentUrl()).toBe("/explorer?v=2.0");
    expect(status()).toHaveTextContent("134 elements · CSF 2.0");
  });

  it("combines filters with text search through the API parameters", async () => {
    const u = user();
    mount("/explorer");
    await within(navigator()).findByRole("tree");
    await u.selectOptions(screen.getByRole("combobox", { name: "Function" }), "ID");
    await u.type(searchbox(), "asset");
    await waitFor(() => expect(status()).toHaveTextContent(/matches for “asset”/));
    expect(api.calls.some((c) => c.includes("function=ID") && c.includes("q=asset") && c.includes("version=2.0"))).toBe(true);
    const items = await within(navigator()).findAllByRole("link");
    expect(items.every((a) => /ID\./.test(a.textContent ?? ""))).toBe(true);
  });

  it("explains when no element matches the filters", async () => {
    const u = user();
    mount("/explorer?level=function&cat=GV.SC");
    // level=function with a category is contradictory: the UI drops nothing silently, but shows it clearly
    expect(await within(navigator()).findByText(/No elements match these filters/)).toBeInTheDocument();
    await u.click(within(navigator()).getAllByRole("button", { name: "Clear filters" })[0]);
    expect(await within(navigator()).findByRole("tree")).toBeInTheDocument();
  });

  it("keeps the open record visible and flags it when filters exclude it", async () => {
    const u = user();
    mount("/explorer/2.0/GV.SC-03");
    expect(await screen.findByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
    await u.selectOptions(screen.getByRole("combobox", { name: "Function" }), "PR");
    expect(await within(navigator()).findByText("Selected record is outside the current results")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
    expect(currentUrl()).toBe("/explorer/2.0/GV.SC-03?fn=PR");
    await u.click(within(navigator()).getAllByRole("button", { name: "Clear filters" })[0]);
    await waitFor(() => expect(within(navigator()).queryByText(/outside the current results/)).toBeNull());
    expect(currentUrl()).toBe("/explorer/2.0/GV.SC-03");
    expect(screen.getByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
  });
});

describe("version switching", () => {
  it("is a single-selection radio group; switching loads CSF 1.1 and keeps q and level but clears GV", async () => {
    const u = user();
    mount("/explorer?v=2.0&fn=GV&level=category&q=risk");
    await within(navigator()).findByRole("list");
    const group = screen.getByRole("radiogroup", { name: "Framework version" });
    expect(within(group).getAllByRole("radio")).toHaveLength(2);
    await u.click(screen.getByRole("radio", { name: "CSF 1.1" }));
    await waitFor(() => expect(currentUrl()).toBe("/explorer?v=1.1&level=category&q=risk"));
    expect(historyLength()).toBe(2);
    expect(screen.getByRole("radio", { name: "CSF 1.1" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "CSF 2.0" })).not.toBeChecked();
    await waitFor(() => expect(status()).toHaveTextContent(/in CSF 1\.1/));
    act(() => go(-1));
    expect(screen.getByRole("radio", { name: "CSF 2.0" })).toBeChecked();
    expect(searchbox()).toHaveValue("risk");
  });

  it("closes an open record on switch and explains that IDs are not equivalent", async () => {
    const u = user();
    mount("/explorer/2.0/GV.SC-03");
    expect(await screen.findByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
    await u.click(screen.getByRole("radio", { name: "CSF 1.1" }));
    await waitFor(() => expect(currentUrl()).toBe("/explorer?v=1.1"));
    expect(screen.queryByRole("heading", { name: "GV.SC-03" })).toBeNull();
    expect(await screen.findByText("GV.SC-03 is a CSF 2.0 element")).toBeInTheDocument();
    await within(navigator()).findByRole("tree");
    expect(topLevelIds()).toEqual(["ID", "PR", "DE", "RS", "RC"]);
  });
});

describe("records and URLs", () => {
  it("normalises an original 1.1 spelling to the canonical URL and shows the printed ID", async () => {
    mount("/explorer/1.1/PR.AT-1?q=awareness");
    expect(await screen.findByRole("heading", { name: "PR.AT-1" })).toBeInTheDocument();
    await waitFor(() => expect(currentUrl()).toBe("/explorer/1.1/PR.AT-01?q=awareness"));
    expect(screen.getByText("Normalized as PR.AT-01")).toBeInTheDocument();
    expect(historyLength()).toBe(1); // canonicalising replaces
  });

  it("handles unknown records and unknown versions", async () => {
    mount("/explorer/2.0/ZZ.QQ-99");
    expect(await screen.findByText("ZZ.QQ-99 was not found in CSF 2.0")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Search for “ZZ\.QQ-99”/ })).toHaveAttribute("href", "/explorer?v=2.0&q=ZZ.QQ-99");
  });

  it("shows a null-description 1.1 function honestly", async () => {
    mount("/explorer/1.1/DE");
    expect(await screen.findByRole("heading", { name: "DE" })).toBeInTheDocument();
    expect(await within(screen.getByRole("region", { name: "Record" })).findByText("Detect")).toBeInTheDocument();
    expect(screen.getByText(/does not provide a description for this function/)).toBeInTheDocument();
  });
});

describe("narrow screens", () => {
  it("shows the navigator OR the record, with a Back-to-results link that keeps the context", async () => {
    mount("/explorer/2.0/GV.SC-03?q=supply");
    expect(await screen.findByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
    expect(navigator().className).toMatch(/\bhidden\b/); // hidden below 900px, visible from 900px up
    expect(navigator().className).toMatch(/min-\[900px\]:flex/);
    const back = screen.getByRole("link", { name: "Back to results" });
    expect(back).toHaveAttribute("href", "/explorer?v=2.0&q=supply");
    expect(back.className).toMatch(/min-\[900px\]:hidden/);
    // list screen: record pane hidden
    resetNavigation("/explorer");
    expect(await screen.findByText(/Records worth a look/)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Record", hidden: true }).className).toMatch(/\bhidden\b/);
  });

  it("labels the back link by version when no results context exists", async () => {
    mount("/explorer/1.1/PR.AT-01");
    expect(await screen.findByRole("link", { name: "Browse CSF 1.1" })).toHaveAttribute("href", "/explorer?v=1.1");
  });
});
