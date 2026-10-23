import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { HEADER_ACTIONS_ID } from "@/components/layout/header-actions";
import { clearCatalogCache } from "@/lib/explorer/catalog-cache";
import { resetExpansion } from "@/lib/explorer/expansion-store";
import { describeEntry, statusLabel } from "@/lib/explorer/crosswalk";
import { currentUrl, go, resetNavigation } from "@/test/next-navigation";
import { DETAILS, installFakeApi, type FakeApi } from "@/test/fake-api";
import type { ElementDetail } from "@/lib/api/types";
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

const record = () => screen.getByRole("region", { name: "Record" });
const rows = () => within(within(record()).getByRole("list", { name: "Official crosswalk rows" })).getAllByRole("listitem");
const detail = (key: string) => DETAILS[key] as ElementDetail;

beforeEach(() => {
  clearCatalogCache();
  resetExpansion();
  api = installFakeApi();
});

describe("crosswalk helpers", () => {
  it("describes each row from its own fields only", () => {
    const [r25, r26] = detail("2.0/GV.SC-03").crosswalk.entries;
    expect(describeEntry(r25)).toBe("Row 25: maps to ID.SC-2.");
    expect(describeEntry(r26)).toBe("Row 26: has no reference element; comment “Conceptually new in 2.0”.");
    expect(statusLabel("mapped_and_new_in_2_0")).toBe("mapped and new in 2.0");
    expect(statusLabel("no_crosswalk_reference")).toBe("no crosswalk reference");
  });
});

describe("GV.SC-03: two official rows that need interpretation", () => {
  it("shows rows 25 and 26 separately, in workbook order, with the ambiguity notice", async () => {
    mount("/explorer/2.0/GV.SC-03");
    expect(await screen.findByRole("heading", { name: "Official crosswalk · CSF 2.0 → CSF 1.1" })).toBeInTheDocument();
    const [r25, r26] = rows();
    expect(rows()).toHaveLength(2);
    expect(r25).toHaveAttribute("data-excel-row", "25");
    expect(r26).toHaveAttribute("data-excel-row", "26");

    // row 25: maps to ID.SC-02, printed ID.SC-2, with both spellings visible
    expect(within(r25).getByText("ROW 25")).toBeInTheDocument();
    const link = within(r25).getByRole("link", { name: "Open ID.SC-2 in CSF 1.1" });
    expect(link).toHaveAttribute("href", "/explorer/1.1/ID.SC-02");
    expect(link).toHaveTextContent("(ID.SC-02)");
    expect(within(r25).getByText(/Suppliers and third party partners/)).toBeInTheDocument();
    expect(within(r25).getByText("mapped")).toBeInTheDocument();

    // row 26: no reference element, workbook comment verbatim, own ingest label
    expect(within(r26).getByText("ROW 26")).toBeInTheDocument();
    expect(within(r26).getByText(/No reference element/)).toBeInTheDocument();
    expect(within(r26).queryByRole("link")).toBeNull();
    expect(within(r26).getByText(/Conceptually new in 2\.0/)).toBeInTheDocument();
    expect(within(r26).getByText("new_in_2_0")).toBeInTheDocument();
    for (const r of [r25, r26]) expect(within(r).getByText("Derived")).toBeInTheDocument();

    // generated notice
    const notice = within(record()).getByRole("status", { name: "" , hidden: true }) ?? null;
    expect(notice).toBeTruthy();
    expect(within(record()).getByText("Multiple crosswalk entries require interpretation")).toBeInTheDocument();
    expect(within(record()).getByText(/contains 2 entries for GV\.SC-03/)).toBeInTheDocument();
    expect(within(record()).getByText("Row 25: maps to ID.SC-2.")).toBeInTheDocument();
    expect(within(record()).getByText("Row 26: has no reference element; comment “Conceptually new in 2.0”.")).toBeInTheDocument();
    expect(within(record()).queryByText(/error|mistake|removed/i)).toBeNull();
    expect(within(record()).queryByText(/strength/i)).toBeNull();
  });

  it("labels the summary as derived and explains it on demand with the API note", async () => {
    const u = userEvent.setup();
    mount("/explorer/2.0/GV.SC-03");
    const chip = await screen.findByRole("button", { name: /Derived classification: mapped and new in 2\.0/ });
    expect(chip).toHaveTextContent("Derived: mapped and new in 2.0");
    await u.click(chip);
    expect(await screen.findByText(detail("2.0/GV.SC-03").crosswalk.summary.note)).toBeInTheDocument();
    expect(screen.getByText(/not a field of the\s+NIST workbook/)).toBeInTheDocument();
  });

  it("jump links move focus to the matching row", async () => {
    const u = userEvent.setup();
    mount("/explorer/2.0/GV.SC-03");
    await u.click(await screen.findByRole("button", { name: "Jump to row 26" }));
    expect(document.getElementById("crosswalk-row-26")).toHaveFocus();
  });

  it("following the target opens the CSF 1.1 record and offers a way back", async () => {
    const u = userEvent.setup();
    mount("/explorer/2.0/GV.SC-03");
    await u.click(await screen.findByRole("link", { name: "Open ID.SC-2 in CSF 1.1" }));
    expect(currentUrl()).toBe("/explorer/1.1/ID.SC-02");
    expect(await screen.findByRole("heading", { name: "ID.SC-2" })).toBeInTheDocument();
    // reverse view of the same row 25, drawn in the official direction
    expect(await screen.findByRole("heading", { name: "Referenced by CSF 2.0 · official crosswalk" })).toBeInTheDocument();
    const back = screen.getByRole("link", { name: /From GV\.SC-03 \(CSF 2\.0\) · row 25/ });
    await u.click(back);
    expect(currentUrl()).toBe("/explorer/2.0/GV.SC-03");
    expect(screen.queryByRole("link", { name: /^From / })).toBeNull();
  });
});

describe("ID.IM-03: one-to-many", () => {
  it("represents all seven workbook rows individually", async () => {
    mount("/explorer/2.0/ID.IM-03");
    await screen.findByRole("heading", { name: "Official crosswalk · CSF 2.0 → CSF 1.1" });
    const expected = detail("2.0/ID.IM-03").crosswalk.entries.map((e) => e.excel_row);
    expect(expected).toHaveLength(7);
    expect(rows().map((r) => r.getAttribute("data-excel-row"))).toEqual(expected.map(String));
    expect(within(record()).getByText("7 workbook rows · nist_csf_transition.xlsx · sheet Relationships")).toBeInTheDocument();
    expect(within(record()).getByRole("button", { name: /Derived classification: mapped only/ })).toBeInTheDocument();
    expect(within(record()).queryByText("Multiple crosswalk entries require interpretation")).toBeNull();
  });

  it("expands long workbook text per row and for all rows", async () => {
    const u = userEvent.setup();
    mount("/explorer/1.1/ID.SC-02"); // rows 6 and 30 carry workbook text longer than the 2-line clamp
    await screen.findByRole("heading", { name: "Referenced by CSF 2.0 · official crosswalk" });
    const buttons = within(record()).getAllByRole("button", { name: "Show full text" });
    expect(buttons[0]).toHaveAttribute("aria-expanded", "false");
    await u.click(buttons[0]);
    expect(within(record()).getAllByRole("button", { name: "Show less" })[0]).toHaveAttribute("aria-expanded", "true");
    await u.click(within(record()).getByRole("button", { name: "Expand all" }));
    expect(within(record()).queryAllByRole("button", { name: "Show full text" })).toHaveLength(0);
    await u.click(within(record()).getByRole("button", { name: "Collapse all" }));
    expect(within(record()).queryAllByRole("button", { name: "Show less" })).toHaveLength(0);
  });
});

describe("RC.CO-02 (CSF 1.1): no crosswalk reference", () => {
  it("shows a neutral notice and never says the element was removed", async () => {
    mount("/explorer/1.1/RC.CO-02");
    expect(await screen.findByText("No crosswalk reference")).toBeInTheDocument();
    expect(screen.getByText(/does not state whether the element was retained, merged or dropped/)).toBeInTheDocument();
    expect(within(record()).queryByRole("list", { name: "Official crosswalk rows" })).toBeNull();
    expect(within(record()).queryByText(/removed|deprecated|retired/i)).toBeNull();
    expect(within(record()).getByRole("button", { name: /Derived classification: no crosswalk reference/ })).toBeInTheDocument();
    expect(within(record()).getByRole("heading", { name: "Referenced by CSF 2.0 · official crosswalk" })).toBeInTheDocument();
  });
});

describe("PR.AT-01 (CSF 1.1): identifiers, references and the reverse crosswalk", () => {
  it("shows the printed and normalized IDs, references, provenance and a reverse row", async () => {
    mount("/explorer/1.1/PR.AT-1");
    expect(await screen.findByRole("heading", { name: "PR.AT-1" })).toBeInTheDocument();
    expect(screen.getByText("Normalized as PR.AT-01")).toBeInTheDocument();
    await waitFor(() => expect(currentUrl()).toBe("/explorer/1.1/PR.AT-01"));
    const refs = detail("1.1/PR.AT-01").informative_references;
    expect(refs).toHaveLength(5);
    expect(await within(record()).findByRole("heading", { name: "Informative references (5)" })).toBeInTheDocument();
    for (const r of refs) expect(within(record()).getByText(r)).toBeInTheDocument();
    expect(within(record()).getByText(/p\. 31 \(PDF p\. 38\)/)).toBeInTheDocument();
    // reverse lookup: the counterpart is the CSF 2.0 focal element; this record is the reference end
    const [row] = rows();
    expect(within(row).getByText("this record")).toBeInTheDocument();
    const entry = detail("1.1/PR.AT-01").crosswalk.entries[0];
    expect(within(row).getByRole("link", { name: `Open ${entry.focal_original_id} in CSF 2.0` })).toHaveAttribute(
      "href",
      `/explorer/2.0/${entry.focal_element_id}`,
    );
  });

  it("an empty reference list is stated honestly", async () => {
    mount("/explorer/2.0/GV.SC-03");
    expect(await screen.findByText(/No informative references are recorded for this element/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Informative references (0)" })).toBeInTheDocument();
  });
});

describe("reverse lookup navigation", () => {
  it("lists every workbook row that references a CSF 1.1 element and opens the CSF 2.0 records", async () => {
    const u = userEvent.setup();
    mount("/explorer/1.1/ID.SC-02");
    await screen.findByRole("heading", { name: "Referenced by CSF 2.0 · official crosswalk" });
    const entries = detail("1.1/ID.SC-02").crosswalk.entries;
    expect(rows().map((r) => r.getAttribute("data-excel-row"))).toEqual(entries.map((e) => String(e.excel_row)));
    const row25 = rows().find((r) => r.getAttribute("data-excel-row") === "25")!;
    await u.click(within(row25).getByRole("link", { name: "Open GV.SC-03 in CSF 2.0" }));
    expect(currentUrl()).toBe("/explorer/2.0/GV.SC-03");
    expect(await screen.findByRole("link", { name: /From ID\.SC-2 \(CSF 1\.1\) · row 25/ })).toBeInTheDocument();
    // Back / Forward keep working
    act(() => go(-1));
    expect(await screen.findByRole("heading", { name: "ID.SC-2" })).toBeInTheDocument();
  });
});

describe("hierarchy and null fields", () => {
  it("a CSF 1.1 function without a description says so and links to every child", async () => {
    const u = userEvent.setup();
    mount("/explorer/1.1/DE");
    expect(await screen.findByRole("heading", { name: "DE" })).toBeInTheDocument();
    expect(screen.getByText(/does not provide a description for this function/)).toBeInTheDocument();
    expect(await within(record()).findByRole("heading", { name: "Categories (3)" })).toBeInTheDocument();
    const list = within(record()).getByRole("heading", { name: "Categories (3)" }).closest("section")!;
    const links = within(list).getAllByRole("link");
    expect(links.map((l) => l.getAttribute("href"))).toEqual(
      detail("1.1/DE").children.map((c) => `/explorer/1.1/${c.element_id}`).sort(),
    );
    await u.click(links[0]);
    expect(currentUrl()).toMatch(/^\/explorer\/1\.1\/DE\./);
  });

  it("a category lists all subcategories; breadcrumbs navigate to parents", async () => {
    const u = userEvent.setup();
    mount("/explorer/2.0/GV.SC");
    const heading = await within(record()).findByRole("heading", { name: "Subcategories (10)" });
    expect(within(heading.closest("section")!).getAllByRole("link")).toHaveLength(10);
    const crumbs = within(screen.getByRole("navigation", { name: "Breadcrumb" }));
    await u.click(await crumbs.findByRole("link", { name: /Govern \(GV\)/ }));
    expect(currentUrl()).toBe("/explorer/2.0/GV");
    expect(await within(record()).findByRole("heading", { name: "Categories (6)" })).toBeInTheDocument();
  });

  it("subcategories have no official name and show their description as the text", async () => {
    mount("/explorer/2.0/GV.SC-03");
    expect(await screen.findByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
    expect(within(record()).getByText(/Cybersecurity supply chain risk management is integrated/)).toHaveClass("font-serif");
    expect(within(record()).getAllByText("Subcategory").length).toBeGreaterThan(0);
  });
});

describe("provenance", () => {
  it("always shows the NIST source line; full details open on demand from the API fields", async () => {
    const u = userEvent.setup();
    mount("/explorer/2.0/GV.SC-03");
    expect(await within(record()).findByText("CSF 2.0 · p. 17 (PDF p. 22)")).toBeInTheDocument();
    const [toggle] = within(record()).getAllByRole("button", { name: "Source details" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await u.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const p = detail("2.0/GV.SC-03").provenance;
    const panel = document.getElementById(toggle.getAttribute("aria-controls")!)!;
    expect(panel).toBeVisible();
    for (const text of [p.source_document.source_file, p.chunk.section, p.source_document.sha256, p.chunk.chunk_id]) {
      expect(within(panel).getByText(text)).toBeInTheDocument();
    }
    expect(within(panel).getByText(/PDF · 32 pages/)).toBeInTheDocument();
    expect(panel.querySelector("a")).toBeNull(); // no invented links to documents
  });
});

describe("loading and errors", () => {
  it("shows a loading state before the record arrives", async () => {
    api.delay["/catalog/elements/2.0/GV.SC-03"] = 150;
    mount("/explorer/2.0/GV.SC-03");
    expect(screen.getByRole("status", { name: "Loading record" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "GV.SC-03" })).toBeInTheDocument();
  });

  it("keeps the identity when only the record request fails, and retries", async () => {
    const u = userEvent.setup();
    mount("/explorer?v=2.0");
    await screen.findByRole("tree");
    api.failDetail.push("/catalog/elements/2.0/GV.OC");
    await u.click(screen.getByRole("treeitem", { name: /^GV\.OC /, hidden: true }));
    expect(await within(record()).findByText("ControlShift API is unreachable")).toBeInTheDocument();
    expect(within(record()).getByText(/identity above comes from the framework list/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "GV.OC" })).toBeInTheDocument();
    api.failDetail.length = 0;
    await u.click(within(record()).getByRole("button", { name: "Retry" }));
    expect(await within(record()).findByRole("heading", { name: /^Official crosswalk|^Referenced by/ })).toBeInTheDocument();
  });

  it("reports an unreachable API on a deep link without raw output", async () => {
    api.failDetail.push("/catalog/elements/2.0/GV.SC-03");
    api.fail.current = false;
    mount("/explorer/2.0/GV.SC-03");
    expect(await screen.findAllByText("ControlShift API is unreachable")).not.toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/Internal Server Error|TypeError|\{"/);
  });

  it("rejects a malformed record response", async () => {
    api.malformed.push("/catalog/elements/2.0/GV.PO");
    mount("/explorer/2.0/GV.PO");
    expect(await within(record()).findByText("Record details could not be loaded")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "GV.PO" })).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('"foo"');
  });

  it("keeps a filtered-out record open with the pinned indicator", async () => {
    const u = userEvent.setup();
    mount("/explorer/2.0/GV.SC-03");
    await screen.findByRole("heading", { name: "GV.SC-03" });
    await u.selectOptions(screen.getByRole("combobox", { name: "Function" }), "PR");
    expect(await screen.findByText("Selected record is outside the current results")).toBeInTheDocument();
    expect(await within(record()).findByRole("heading", { name: "Official crosswalk · CSF 2.0 → CSF 1.1" })).toBeInTheDocument();
  });
});

describe("responsive structure", () => {
  it("renders the facts rail for wide screens only (CSS-gated) and stacks entries below 600px", async () => {
    mount("/explorer/2.0/GV.SC-03");
    await screen.findByRole("heading", { name: "GV.SC-03" });
    const rail = await screen.findByRole("complementary", { name: "Record facts", hidden: true });
    expect(rail.className).toMatch(/\bhidden\b/);
    expect(rail.className).toMatch(/min-\[1640px\]:block/);
    expect(within(rail).getByText("Official text")).toBeInTheDocument();
    expect(within(rail).getByRole("link", { name: "GV.SC" })).toBeInTheDocument(); // parent
    expect(rows()[0].className).toMatch(/min-\[600px\]:grid-cols/);
    const inline = within(record()).getAllByRole("button", { name: "Source details" }).map((b) => b.parentElement!);
    expect(inline.some((el) => /min-\[1640px\]:hidden/.test(el.className))).toBe(true);
  });
});
