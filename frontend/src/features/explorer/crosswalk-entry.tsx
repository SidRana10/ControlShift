"use client";

import Link from "next/link";
import { useId } from "react";
import { ChevronRight, CircleDashed } from "lucide-react";
import { DerivedTag, SourceTag } from "@/components/shared/source-tags";
import { VersionChip } from "@/components/shared/version-chip";
import type { CrosswalkEntry as Entry, FrameworkVersion } from "@/lib/api/types";
import { isLongText } from "@/lib/explorer/crosswalk";
import { recordHref, type ExplorerContext } from "@/lib/explorer/url";
import { cn } from "@/lib/utils";

interface Endpoint {
  version: FrameworkVersion;
  elementId: string;
  printedId: string;
}

function Ident({
  end,
  isCurrent,
  ctx,
  onFollow,
}: {
  end: Endpoint;
  isCurrent: boolean;
  ctx: ExplorerContext;
  onFollow: () => void;
}) {
  const differs = end.printedId !== end.elementId;
  const label = (
    <>
      <VersionChip version={end.version} />
      <span className="font-mono text-id font-medium">{end.printedId}</span>
      {differs && <span className="font-mono text-id text-fg-3">({end.elementId})</span>}
    </>
  );
  if (isCurrent) {
    return (
      <span className="inline-flex items-center gap-1.5 text-fg-1">
        {label}
        <span className="text-caption text-fg-3">this record</span>
      </span>
    );
  }
  return (
    <Link
      href={recordHref(end.version, end.elementId, ctx)}
      onClick={onFollow}
      aria-label={`Open ${end.printedId} in CSF ${end.version}`}
      className="inline-flex min-h-11 items-center gap-1.5 rounded-md text-cobalt hover:underline min-[900px]:min-h-7"
    >
      {label}
    </Link>
  );
}

/** Horizontal (wide) or vertical (narrow) link between the two ends of an official row. */
function Connector({ mapped }: { mapped: boolean }) {
  return (
    <span
      aria-hidden="true"
      className="flex h-6 items-center min-[600px]:h-auto min-[600px]:min-w-8 min-[600px]:max-w-24 min-[600px]:flex-1 max-[599px]:ml-3 max-[599px]:flex-col"
    >
      {mapped ? (
        <>
          <span className="h-3 w-px bg-v20 min-[600px]:h-px min-[600px]:w-auto min-[600px]:flex-1" />
          <span className="h-3 w-px bg-v11 min-[600px]:h-px min-[600px]:w-auto min-[600px]:flex-1" />
          <ChevronRight strokeWidth={1.5} className="-ml-1 size-3.5 text-v11 max-[599px]:hidden" />
        </>
      ) : (
        <>
          <span className="h-4 w-px border-l border-dashed border-fg-4 min-[600px]:h-px min-[600px]:w-auto min-[600px]:flex-1 min-[600px]:border-t min-[600px]:border-l-0" />
          <CircleDashed strokeWidth={1.5} className="size-3.5 text-fg-4" />
        </>
      )}
    </span>
  );
}

/**
 * One official workbook row, exactly as stored. The official direction is always
 * CSF 2.0 (focal) -> CSF 1.1 (reference): the focal end is drawn first in both lookups, and the
 * end that is the open record is labelled "this record".
 */
export function CrosswalkEntryRow({
  entry,
  lookup,
  ctx,
  expanded,
  onToggleExpanded,
  onFollow,
}: {
  entry: Entry;
  lookup: "forward" | "reverse";
  ctx: ExplorerContext;
  expanded: boolean;
  onToggleExpanded: () => void;
  onFollow: (target: Endpoint) => void;
}) {
  const textId = useId();
  const focal: Endpoint = {
    version: entry.focal_version,
    elementId: entry.focal_element_id,
    printedId: entry.focal_original_id,
  };
  const reference: Endpoint | null = entry.reference_element_id
    ? {
        version: entry.reference_version,
        elementId: entry.reference_element_id,
        printedId: entry.reference_original_id ?? entry.reference_element_id,
      }
    : null;
  const counterpart = lookup === "forward" ? reference : focal;
  const description = lookup === "forward" ? entry.reference_description : entry.focal_description;
  const long = isLongText(description);

  return (
    <li
      id={`crosswalk-row-${entry.excel_row}`}
      data-excel-row={entry.excel_row}
      tabIndex={-1}
      className="grid gap-x-4 gap-y-2 px-4 py-3 outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 min-[600px]:grid-cols-[4.5rem_1fr]"
    >
      <p
        className="font-mono text-mono-sm text-fg-3 min-[600px]:pt-1.5"
        title={`Workbook row ${entry.excel_row}, sheet ${entry.sheet}, ${entry.source_file}`}
      >
        ROW {entry.excel_row}
      </p>
      <div className="min-w-0">
        <div className="flex flex-col items-start gap-0 min-[600px]:flex-row min-[600px]:items-center min-[600px]:gap-2">
          <Ident
            end={focal}
            isCurrent={lookup === "forward"}
            ctx={ctx}
            onFollow={() => onFollow(focal)}
          />
          <Connector mapped={Boolean(reference)} />
          {reference ? (
            <Ident
              end={reference}
              isCurrent={lookup === "reverse"}
              ctx={ctx}
              onFollow={() => onFollow(reference)}
            />
          ) : (
            <span className="text-ui-sm text-fg-2 italic">
              <span className="sr-only">has </span>No reference element
            </span>
          )}
        </div>

        {counterpart && description && (
          <div className="mt-2">
            <p className="flex items-center gap-2 text-caption text-fg-3">
              <SourceTag />
              Workbook description of {counterpart.printedId} · CSF {counterpart.version}
            </p>
            <p
              id={textId}
              className={cn("mt-1 font-serif text-source text-fg-1", !expanded && "line-clamp-2")}
            >
              {description}
            </p>
            {long && (
              <button
                type="button"
                aria-expanded={expanded}
                aria-controls={textId}
                onClick={onToggleExpanded}
                className="inline-flex min-h-11 items-center text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
              >
                {expanded ? "Show less" : "Show full text"}
              </button>
            )}
          </div>
        )}

        {entry.comments && (
          <div className="mt-2">
            <p className="text-caption text-fg-3">Workbook comment:</p>
            <p className="font-serif text-source text-fg-1 italic">“{entry.comments}”</p>
          </div>
        )}

        <p className="mt-2 flex flex-wrap items-center gap-2 text-caption text-fg-2">
          Ingest label: <span className="font-mono text-id">{entry.mapping_type}</span>
          <DerivedTag />
        </p>
      </div>
    </li>
  );
}
