"use client";

import { VersionChip } from "@/components/shared/version-chip";
import { Button } from "@/components/ui/button";
import { useHealth } from "@/features/health/health-provider";
import { loadVersions } from "@/lib/explorer/catalog-cache";
import { useLoader } from "@/lib/explorer/use-loader";
import { cn } from "@/lib/utils";

/**
 * Live framework facts from GET /catalog/versions and GET /health. Counts are what the API reports;
 * the workbook figure is the number of ingested workbook rows, not a number of controls.
 */
export function FrameworkFacts() {
  const versions = useLoader("versions", loadVersions);
  const health = useHealth();
  const rows = health.status === "online" ? health.health.database.crosswalk_rows : null;
  // Newest first, matching the app's CSF 2.0 → CSF 1.1 direction.
  const list = [...(versions.data?.versions ?? [])].sort((a, b) => b.version.localeCompare(a.version));

  if (versions.status === "error") {
    return (
      <p className="text-body text-fg-2">
        Framework details could not be loaded because the API is unreachable.{" "}
        <Button variant="link" className="h-auto p-0 text-body" onClick={versions.reload}>
          Retry
        </Button>
      </p>
    );
  }
  if (list.length === 0) {
    return <div aria-busy="true" className="h-24 rounded-lg border border-border bg-surface" />;
  }
  return (
    <div className="grid gap-px overflow-hidden rounded-lg border border-border bg-border min-[720px]:grid-cols-2">
      {list.map((v) => (
        <div key={v.version} className={cn("bg-surface p-4", v.version === "2.0" ? "border-t-2 border-t-v20" : "border-t-2 border-t-v11")}>
          <p className="flex items-center gap-2">
            <VersionChip version={v.version} />
            <span className="text-ui font-semibold text-fg-1">{v.name}</span>
          </p>
          <p className="mt-2 text-ui-sm text-fg-2 tabular-nums">
            {v.counts.function} functions · {v.counts.category} categories · {v.counts.subcategory} subcategories
          </p>
          <p className="mt-1 text-caption text-fg-3">
            Source: <span className="font-mono text-mono-sm">{v.source_document.source_file}</span>
            {v.source_document.pages ? `, ${v.source_document.pages} pages` : ""}
          </p>
        </div>
      ))}
      {rows !== null && (
        <p className="bg-surface-sunken px-4 py-2 text-caption text-fg-2 min-[720px]:col-span-2">
          The official transition workbook relates them in <span className="tabular-nums">{rows}</span> rows, direction
          CSF 2.0 → CSF 1.1. A row is not a unique control: one element can have several rows.
        </p>
      )}
    </div>
  );
}
