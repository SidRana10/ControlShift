import { Suspense } from "react";
import { ExplorerWorkspace } from "@/features/explorer/explorer-workspace";

// The workspace (navigator, provider, record pane) lives in the layout so it persists, with its
// scroll and expansion state, while records change. The page files below only define the routes.
export default function ExplorerLayout() {
  return (
    <Suspense fallback={<div className="h-full bg-surface" aria-busy="true" />}>
      <ExplorerWorkspace />
    </Suspense>
  );
}
