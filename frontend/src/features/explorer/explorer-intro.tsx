"use client";

import { useEffect, useState } from "react";
import { Notice } from "@/components/shared/notice";
import { StateBlock } from "@/components/shared/state-block";
import { VersionChip } from "@/components/shared/version-chip";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getVersions } from "@/lib/api/client";
import type { VersionInfo } from "@/lib/api/types";
import { useApi } from "@/lib/api/use-api";

/** Skeletons appear only after 150ms so fast responses do not flash. */
function useDelayedFlag(active: boolean, ms = 150) {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    if (!active) {
      const reset = setTimeout(() => setShown(false), 0);
      return () => clearTimeout(reset);
    }
    const t = setTimeout(() => setShown(true), ms);
    return () => clearTimeout(t);
  }, [active, ms]);
  return shown;
}

function VersionRow({ v }: { v: VersionInfo }) {
  return (
    <li className="px-4 py-3">
      <div className="flex items-center gap-2">
        <VersionChip version={v.version} />
        <span className="text-ui font-medium text-fg-1">{v.name}</span>
      </div>
      <p className="mt-1 text-caption text-fg-3">
        {v.counts.function} functions · {v.counts.category} categories · {v.counts.subcategory}{" "}
        subcategories
      </p>
      <p className="mt-0.5 font-mono text-id text-fg-3">
        {v.source_document.source_file}
        {v.source_document.pages ? ` · ${v.source_document.pages} pages` : ""}
      </p>
    </li>
  );
}

function FrameworksPane() {
  const { state, reload } = useApi(getVersions);
  const showSkeleton = useDelayedFlag(state.status === "loading");

  let body: React.ReactNode;
  if (state.status === "loading") {
    body = showSkeleton ? (
      <div aria-hidden="true" className="space-y-4 p-4">
        {[0, 1].map((i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        ))}
      </div>
    ) : null;
  } else if (state.status === "error") {
    const unreachable = state.error.kind === "unreachable";
    body = (
      <div className="p-4">
        <Notice
          variant="error"
          title={unreachable ? "ControlShift API is unreachable" : "Framework versions could not be loaded"}
          actions={
            <Button variant="outline" size="sm" onClick={reload}>
              Retry
            </Button>
          }
        >
          {unreachable
            ? "Start the FastAPI service (controlshift-serve) and retry."
            : state.error.message}
        </Notice>
      </div>
    );
  } else if (state.data.versions.length === 0) {
    body = (
      <StateBlock title="No framework versions are available">
        The database returned no framework versions.
      </StateBlock>
    );
  } else {
    body = (
      <ul className="divide-y divide-border">
        {[...state.data.versions].sort((a, b) => b.version.localeCompare(a.version)).map((v) => (
          <VersionRow key={v.version} v={v} />
        ))}
      </ul>
    );
  }

  return (
    <section
      aria-label="Frameworks"
      aria-busy={state.status === "loading"}
      className="border-b border-border bg-surface min-[900px]:w-[288px] min-[900px]:shrink-0 min-[900px]:overflow-y-auto min-[900px]:border-r min-[900px]:border-b-0 min-[1200px]:w-[320px] min-[1320px]:w-[340px]"
    >
      <h2 className="border-b border-border px-4 py-3 text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
        Frameworks
      </h2>
      {body}
    </section>
  );
}

/**
 * Explorer introductory workspace. The two regions mirror the final master-detail layout
 * (navigator column + record pane) but contain only real version data and an honest status;
 * hierarchy, search, filters and record detail are not implemented yet.
 */
export function ExplorerIntro() {
  return (
    <div className="flex min-h-full flex-col min-[900px]:h-full min-[900px]:flex-row">
      <FrameworksPane />
      <section aria-label="Record" className="min-w-0 flex-1 bg-surface min-[900px]:overflow-y-auto">
        <div className="max-w-[720px] px-4 py-8 min-[900px]:px-10">
          <h2 className="text-name-lg font-semibold text-fg-1">NIST CSF records</h2>
          <p className="mt-2 text-body text-fg-2">
            Control Explorer will let you browse functions, categories and subcategories of both
            frameworks, read the official text with its source page, and inspect each record&apos;s
            official crosswalk entries. Records are shown as published by NIST and do not depend on
            any language model.
          </p>
          <Notice variant="info" className="mt-6" title="The navigator and record view are in development">
            Search, filters and record details are not available yet. The framework summaries on
            this page are read from the live API.
          </Notice>
        </div>
      </section>
    </div>
  );
}
