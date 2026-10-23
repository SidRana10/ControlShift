"use client";

import { HeaderActions } from "@/components/layout/header-actions";
import { cn } from "@/lib/utils";
import { ExplorerProvider, useExplorer } from "./explorer-provider";
import { Navigator } from "./navigator";
import { OrientationPanel } from "./orientation-panel";
import { RecordPane } from "./record-pane";
import { VersionToggle } from "./version-toggle";

function Workspace() {
  const { loc } = useExplorer();
  const onRecord = loc.kind === "record";
  // >=900px: navigator and record side by side. Below 900px: one screen at a time.
  return (
    <>
      <HeaderActions>
        <VersionToggle />
      </HeaderActions>
      <div className="flex h-full min-h-0 flex-col min-[900px]:flex-row">
        <Navigator className={onRecord ? "hidden min-[900px]:flex" : "flex"} />
        <section
          aria-label="Record"
          className={cn(
            "min-h-0 min-w-0 flex-1 overflow-y-auto bg-surface",
            onRecord ? "block" : "hidden min-[900px]:block",
          )}
        >
          {onRecord ? <RecordPane /> : <OrientationPanel />}
        </section>
      </div>
    </>
  );
}

/**
 * The route files only define the URLs; this workspace renders the record pane or the orientation
 * panel itself, from the URL. Rendering it here keeps exactly one instance mounted (the router
 * keeps previously visited pages alive, which would otherwise duplicate effects and focus).
 */
export function ExplorerWorkspace() {
  return (
    <ExplorerProvider>
      <Workspace />
    </ExplorerProvider>
  );
}
