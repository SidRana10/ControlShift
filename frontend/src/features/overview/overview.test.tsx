import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import OverviewPage from "@/app/page";
import { HealthProvider } from "@/features/health/health-provider";
import { clearCatalogCache } from "@/lib/explorer/catalog-cache";
import { installFakeApi } from "@/test/fake-api";

beforeEach(() => {
  clearCatalogCache();
  installFakeApi();
});

const mount = () =>
  render(
    <HealthProvider>
      <OverviewPage />
    </HealthProvider>,
  );

describe("Overview", () => {
  it("states what ControlShift does and links the three workflows", () => {
    mount();
    expect(screen.getByRole("heading", { level: 2, name: /Read CSF 1\.1 and CSF 2\.0 against each other/ })).toBeInTheDocument();
    const w = screen.getByRole("region", { name: "Three ways to work" });
    expect(within(w).getByRole("link", { name: /Ask a question/ })).toHaveAttribute("href", "/ask");
    expect(within(w).getByRole("link", { name: /Browse official records/ })).toHaveAttribute("href", "/explorer");
    expect(within(w).getByRole("link", { name: /Compare frameworks/ })).toHaveAttribute("href", "/compare");
  });

  it("only links to routes and records that exist", () => {
    mount();
    const start = screen.getByRole("region", { name: "Start exploring" });
    expect(within(start).getAllByRole("link").map((a) => a.getAttribute("href"))).toEqual([
      "/explorer/2.0/GV.SC-03",
      "/compare?focal=GV.SC-03&row=26",
      "/compare?focal=ID.IM-03",
      "/compare?ref=RC.CO-02",
    ]);
  });

  it("shows real framework counts and has no placeholder status labels", async () => {
    mount();
    expect(await screen.findByText(/6 functions · 22 categories · 106 subcategories/)).toBeInTheDocument();
    expect(screen.getByText(/5 functions · 23 categories · 108 subcategories/)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\bSoon\b|In development|coming soon/i);
  });

  it("explains the three content labels, including AI-generated", () => {
    mount();
    const labels = screen.getByRole("region", { name: "How content is labelled" });
    for (const t of ["NIST", "Derived", "AI-generated"]) expect(within(labels).getByText(t)).toBeInTheDocument();
  });
});
