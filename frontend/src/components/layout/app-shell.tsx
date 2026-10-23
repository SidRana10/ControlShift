"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { BrandMark } from "@/components/shared/brand-mark";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { HealthProvider } from "@/features/health/health-provider";
import { SidebarStatus } from "@/features/health/sidebar-status";
import { titleFor } from "@/lib/navigation";
import { useMediaQuery } from "@/lib/use-media-query";
import { useSidebarCollapsed } from "@/lib/use-sidebar-collapsed";
import { SidebarNav } from "./sidebar-nav";

function Brand({ docked }: { docked: boolean }) {
  return (
    <Link
      href="/"
      aria-label="ControlShift home"
      className="flex h-14 shrink-0 items-center gap-3 px-5 text-title-sm font-semibold text-fg-1"
    >
      <BrandMark className="shrink-0" />
      <span className={docked ? "rail-hide" : undefined}>ControlShift</span>
    </Link>
  );
}

/**
 * Shared shell (docs/frontend-design-spec.md section 4-5).
 *  >=1200px  docked sidebar, 232px (56px when collapsed by the user)
 *  900-1199  docked 56px rail; the toggle opens the full navigation as an overlay sheet
 *  <900px    52px top bar with a menu button that opens the same sheet
 * Layout switches with CSS (the collapse preference arrives as <html data-sidebar>, set by an inline
 * script before first paint), so first paint is correct; JS only drives the toggle and tooltips.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, toggleCollapsed] = useSidebarCollapsed();
  const wide = useMediaQuery("(min-width: 1200px)");
  const [sheetOpen, setSheetOpen] = useState(false);
  const rail = !wide || collapsed;

  const toggleLabel = wide ? (collapsed ? "Expand sidebar" : "Collapse sidebar") : "Open navigation";
  const onToggle = () => (wide ? toggleCollapsed() : setSheetOpen(true));

  return (
    <HealthProvider>
      <div className="flex h-dvh overflow-hidden">
        <a
          href="#main"
          className="sr-only z-[60] rounded-md bg-surface px-3 py-2 text-ui font-medium shadow-overlay focus:not-sr-only focus:fixed focus:top-2 focus:left-2"
        >
          Skip to content
        </a>

        <aside
          aria-label="Sidebar"
          className="sidebar-dock hidden shrink-0 flex-col border-r border-border bg-surface-sunken min-[900px]:flex"
        >
          <Brand docked />
          <div className="flex-1 overflow-y-auto">
            <SidebarNav docked showTooltips={rail} />
          </div>
          <div className="flex flex-col gap-0.5 border-t border-border py-2">
            <Tooltip>
              <TooltipTrigger
                render={
                  <button
                    type="button"
                    onClick={onToggle}
                    aria-label={toggleLabel}
                    className="mx-2 flex h-8 items-center gap-3 rounded-md px-3 text-ui text-fg-2 hover:bg-surface-hover hover:text-fg-1 active:bg-surface-pressed"
                  />
                }
              >
                <PanelLeftClose
                  aria-hidden="true"
                  strokeWidth={1.5}
                  className="toggle-close size-4 shrink-0 text-fg-3"
                />
                <PanelLeftOpen
                  aria-hidden="true"
                  strokeWidth={1.5}
                  className="toggle-open size-4 shrink-0 text-fg-3"
                />
                <span className="rail-hide font-medium">Collapse</span>
              </TooltipTrigger>
              {rail && (
                <TooltipContent side="right" sideOffset={8}>
                  {toggleLabel}
                </TooltipContent>
              )}
            </Tooltip>
            <SidebarStatus docked />
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-[52px] shrink-0 items-center gap-2 border-b border-border bg-surface px-2 min-[900px]:h-14 min-[900px]:px-6">
            <Button
              variant="ghost"
              size="icon"
              className="size-11 min-[900px]:hidden"
              aria-label="Open navigation"
              onClick={() => setSheetOpen(true)}
            >
              <Menu aria-hidden="true" className="size-[18px]" strokeWidth={1.5} />
            </Button>
            <h1 className="truncate text-title font-semibold text-fg-1">{titleFor(pathname)}</h1>
          </header>
          <main id="main" tabIndex={-1} className="min-h-0 flex-1 overflow-y-auto outline-none">
            {children}
          </main>
        </div>

        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetContent side="left" showCloseButton>
            <SheetTitle className="sr-only">Navigation</SheetTitle>
            <SheetDescription className="sr-only">
              Move between ControlShift sections and check API status.
            </SheetDescription>
            <Brand docked={false} />
            <div className="flex-1 overflow-y-auto">
              <SidebarNav docked={false} onNavigate={() => setSheetOpen(false)} />
            </div>
            <div className="border-t border-border py-2">
              <SidebarStatus docked={false} />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </HealthProvider>
  );
}
