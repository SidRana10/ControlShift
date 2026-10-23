"use client";

import Link from "next/link";
import { Notice } from "@/components/shared/notice";
import { VersionChip } from "@/components/shared/version-chip";
import { Button } from "@/components/ui/button";
import { loadVersions } from "@/lib/explorer/catalog-cache";
import { recordHref } from "@/lib/explorer/url";
import { useLoader } from "@/lib/explorer/use-loader";
import { useExplorer } from "./explorer-provider";

const EXAMPLES = [
  { version: "2.0", id: "GV.SC-03", note: "two official crosswalk rows (workbook rows 25 and 26)" },
  { version: "2.0", id: "ID.IM-03", note: "several official crosswalk rows, one per workbook row" },
  { version: "1.1", id: "RC.CO-02", note: "no row in the official crosswalk references it" },
] as const;

/** Shown when no record is open (desktop): real framework facts and a few record links. */
export function OrientationPanel() {
  const { version, versionHint, loc, ctx } = useExplorer();
  const versions = useLoader("versions", loadVersions);
  const info = versions.data?.versions.find((v) => v.version === version);

  const hintVisible =
    versionHint &&
    loc.kind === "list" &&
    loc.version === versionHint.to &&
    JSON.stringify(loc.ctx) === JSON.stringify(versionHint.ctx);

  return (
    <div className="max-w-[720px] px-4 py-8 min-[900px]:px-10">
      {hintVisible && (
        <Notice variant="info" className="mb-6" title={`${versionHint.recordId} is a CSF ${versionHint.from} element`}>
          Matching IDs in different framework versions are not equivalent, so the record was closed.
          Its official crosswalk relationships to CSF {versionHint.to} will be shown in the record view.
        </Notice>
      )}
      <div className="flex items-center gap-2">
        <VersionChip version={version} />
        <h2 className="text-name-lg font-semibold text-fg-1">{info?.name ?? `NIST CSF ${version}`}</h2>
      </div>
      {info ? (
        <p className="mt-2 text-body text-fg-2">
          {info.counts.function} functions · {info.counts.category} categories ·{" "}
          {info.counts.subcategory} subcategories. Source:{" "}
          <span className="font-mono text-id">{info.source_document.source_file}</span>
          {info.source_document.pages ? `, ${info.source_document.pages} pages` : ""}.
        </p>
      ) : versions.status === "error" ? (
        <p className="mt-2 text-body text-fg-2">
          Framework details could not be loaded.{" "}
          <Button variant="link" className="h-auto p-0 text-body" onClick={versions.reload}>
            Retry
          </Button>
        </p>
      ) : null}
      <p className="mt-3 text-body text-fg-2">
        Browse the hierarchy on the left, or search by ID, name or description. Select a record to
        open it. Everything here is official NIST text; no language model is involved.
      </p>

      <h3 className="mt-8 text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
        Records worth a look
      </h3>
      <ul className="mt-2 divide-y divide-border rounded-lg border border-border">
        {EXAMPLES.map((ex) => (
          <li key={ex.id}>
            <Link
              href={recordHref(ex.version, ex.id, ctx)}
              className="flex min-h-11 items-center gap-3 px-4 py-2 hover:bg-surface-hover"
            >
              <VersionChip version={ex.version} />
              <span className="font-mono text-id font-medium text-fg-1">{ex.id}</span>
              <span className="min-w-0 text-ui-sm text-fg-2">{ex.note}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
